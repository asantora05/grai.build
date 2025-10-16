"""
BigQuery data loader for grai.build.

Extracts data from BigQuery tables and loads into Neo4j using entity definitions.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from pydantic import BaseModel, Field

from grai.core.models import Entity, Relation


@dataclass
class BigQueryConnection:
    """
    Configuration for BigQuery connection.

    Attributes:
        project_id: GCP project ID.
        dataset: Default dataset name.
        credentials_path: Optional path to service account JSON file.
        location: BigQuery location/region (e.g., 'US', 'EU').
    """

    project_id: str
    dataset: Optional[str] = None
    credentials_path: Optional[Path] = None
    location: str = "US"


class LoadResult(BaseModel):
    """
    Result of a data loading operation.

    Attributes:
        success: Whether the load was successful.
        entity_name: Name of entity or relation loaded.
        rows_extracted: Number of rows extracted from BigQuery.
        rows_loaded: Number of rows loaded into Neo4j.
        errors: List of error messages if any.
        duration_seconds: Time taken for the operation.
    """

    success: bool = Field(..., description="Load operation success status")
    entity_name: str = Field(..., description="Entity or relation name")
    rows_extracted: int = Field(0, description="Rows extracted from BigQuery")
    rows_loaded: int = Field(0, description="Rows loaded to Neo4j")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    duration_seconds: float = Field(0.0, description="Operation duration")


class BigQueryExtractor:
    """
    Extracts data from BigQuery tables.

    Handles connection management, query execution, and data streaming
    from BigQuery with support for batching and large datasets.
    """

    def __init__(self, connection: BigQueryConnection):
        """
        Initialize BigQuery extractor.

        Args:
            connection: BigQuery connection configuration.
        """
        self.connection = connection
        self.client = None

    def connect(self):
        """
        Establish connection to BigQuery.

        Raises:
            ImportError: If google-cloud-bigquery is not installed.
            Exception: If connection fails.
        """
        try:
            from google.cloud import bigquery
        except ImportError:
            raise ImportError(
                "google-cloud-bigquery is required for BigQuery support. "
                "Install with: pip install google-cloud-bigquery"
            )

        try:
            if self.connection.credentials_path:
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_file(
                    str(self.connection.credentials_path)
                )
                self.client = bigquery.Client(
                    project=self.connection.project_id,
                    credentials=credentials,
                    location=self.connection.location,
                )
            else:
                # Use default credentials (from GOOGLE_APPLICATION_CREDENTIALS env var)
                self.client = bigquery.Client(
                    project=self.connection.project_id,
                    location=self.connection.location,
                )
        except Exception as e:
            raise Exception(f"Failed to connect to BigQuery: {e}")

    def extract_table(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        limit: Optional[int] = None,
        batch_size: int = 1000,
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Extract data from a BigQuery table in batches.

        Args:
            table_name: Fully qualified table name (project.dataset.table or dataset.table).
            columns: List of columns to select (None = all columns).
            where_clause: Optional WHERE clause for filtering.
            limit: Optional limit on number of rows.
            batch_size: Number of rows per batch.

        Yields:
            Batches of rows as list of dictionaries.

        Example:
            >>> extractor = BigQueryExtractor(connection)
            >>> extractor.connect()
            >>> for batch in extractor.extract_table("analytics.customers", limit=100):
            ...     print(f"Got {len(batch)} rows")
        """
        if not self.client:
            self.connect()

        # Build query
        cols = ", ".join(columns) if columns else "*"

        # Handle table name (add project/dataset if needed)
        if "." not in table_name:
            # Just table name, use default dataset
            if not self.connection.dataset:
                raise ValueError(
                    f"Table '{table_name}' needs dataset. "
                    f"Use 'dataset.table' format or set default dataset."
                )
            full_table = f"{self.connection.project_id}.{self.connection.dataset}.{table_name}"
        elif table_name.count(".") == 1:
            # dataset.table, add project
            full_table = f"{self.connection.project_id}.{table_name}"
        else:
            # Already fully qualified
            full_table = table_name

        query = f"SELECT {cols} FROM `{full_table}`"

        if where_clause:
            query += f" WHERE {where_clause}"

        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        query_job = self.client.query(query)

        # Stream results in batches
        batch = []
        for row in query_job:
            # Convert row to dict
            row_dict = dict(row.items())
            batch.append(row_dict)

            if len(batch) >= batch_size:
                yield batch
                batch = []

        # Yield remaining rows
        if batch:
            yield batch

    def extract_query(
        self,
        query: str,
        batch_size: int = 1000,
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Execute a custom SQL query and extract results.

        Args:
            query: SQL query to execute.
            batch_size: Number of rows per batch.

        Yields:
            Batches of rows as list of dictionaries.

        Example:
            >>> query = "SELECT * FROM analytics.customers WHERE region = 'US'"
            >>> for batch in extractor.extract_query(query):
            ...     process_batch(batch)
        """
        if not self.client:
            self.connect()

        query_job = self.client.query(query)

        batch = []
        for row in query_job:
            row_dict = dict(row.items())
            batch.append(row_dict)

            if len(batch) >= batch_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get schema information for a BigQuery table.

        Args:
            table_name: Table name (dataset.table or project.dataset.table).

        Returns:
            List of column definitions with name and type.

        Example:
            >>> schema = extractor.get_table_schema("analytics.customers")
            >>> print(schema)
            [{'name': 'customer_id', 'type': 'INTEGER'}, ...]
        """
        if not self.client:
            self.connect()

        # Parse table reference
        if "." not in table_name:
            table_ref = f"{self.connection.project_id}.{self.connection.dataset}.{table_name}"
        elif table_name.count(".") == 1:
            table_ref = f"{self.connection.project_id}.{table_name}"
        else:
            table_ref = table_name

        table = self.client.get_table(table_ref)

        return [{"name": field.name, "type": field.field_type} for field in table.schema]

    def close(self):
        """Close BigQuery connection."""
        if self.client:
            self.client.close()
            self.client = None


def connect_bigquery(
    project_id: str,
    dataset: Optional[str] = None,
    credentials_path: Optional[Path] = None,
    location: str = "US",
) -> BigQueryExtractor:
    """
    Create and connect to BigQuery.

    Args:
        project_id: GCP project ID.
        dataset: Default dataset name.
        credentials_path: Path to service account JSON file.
        location: BigQuery location.

    Returns:
        Connected BigQueryExtractor instance.

    Example:
        >>> extractor = connect_bigquery("my-project", dataset="analytics")
        >>> # Extractor is ready to use
    """
    connection = BigQueryConnection(
        project_id=project_id,
        dataset=dataset,
        credentials_path=credentials_path,
        location=location,
    )

    extractor = BigQueryExtractor(connection)
    extractor.connect()

    return extractor


def extract_data(
    extractor: BigQueryExtractor,
    entity: Entity,
    limit: Optional[int] = None,
    batch_size: int = 1000,
) -> Iterator[List[Dict[str, Any]]]:
    """
    Extract data for an entity from BigQuery.

    Args:
        extractor: Connected BigQueryExtractor instance.
        entity: Entity definition with source information.
        limit: Optional limit on rows to extract.
        batch_size: Rows per batch.

    Yields:
        Batches of entity data.

    Example:
        >>> entity = Entity(entity="customer", source="analytics.customers", ...)
        >>> for batch in extract_data(extractor, entity, limit=1000):
        ...     print(f"Processing {len(batch)} customers")
    """
    # Get table name from entity source
    source_name = entity.get_source_name()

    # Get property names for column selection
    columns = [prop.name for prop in entity.properties]

    # Add keys if not already in properties
    for key in entity.keys:
        if key not in columns:
            columns.insert(0, key)

    # Extract data
    yield from extractor.extract_table(
        source_name,
        columns=columns,
        limit=limit,
        batch_size=batch_size,
    )


def load_entity_from_bigquery(
    entity: Entity,
    bigquery_connection: BigQueryConnection,
    neo4j_connection: Any,  # Neo4jConnection from neo4j_loader
    limit: Optional[int] = None,
    batch_size: int = 1000,
    dry_run: bool = False,
    verbose: bool = False,
) -> LoadResult:
    """
    Load entity data from BigQuery to Neo4j.

    Args:
        entity: Entity definition.
        bigquery_connection: BigQuery connection config.
        neo4j_connection: Neo4j connection (from neo4j_loader).
        limit: Optional row limit.
        batch_size: Rows per batch.
        dry_run: If True, extract but don't load to Neo4j.

    Returns:
        LoadResult with operation details.

    Example:
        >>> result = load_entity_from_bigquery(
        ...     entity=customer_entity,
        ...     bigquery_connection=bq_conn,
        ...     neo4j_connection=neo4j_conn,
        ...     limit=10000
        ... )
        >>> print(f"Loaded {result.rows_loaded} rows")
    """
    import time

    start_time = time.time()
    rows_extracted = 0
    rows_loaded = 0
    errors = []

    try:
        # Connect to BigQuery
        extractor = BigQueryExtractor(bigquery_connection)
        extractor.connect()

        # Extract and load data in batches
        batch_num = 0
        for batch in extract_data(extractor, entity, limit=limit, batch_size=batch_size):
            batch_num += 1
            rows_extracted += len(batch)

            if verbose:
                print(f"\n[Batch {batch_num}] Extracted {len(batch)} rows")
                if batch:
                    print(f"  Sample row: {batch[0]}")

            if not dry_run:
                # Generate Cypher for this batch
                # For now, we'll use parameterized queries
                cypher = _generate_batch_cypher(entity, batch)

                if verbose:
                    print(f"\n[Batch {batch_num}] Generated Cypher:")
                    print(f"  {cypher[:200]}..." if len(cypher) > 200 else f"  {cypher}")

                # Execute against Neo4j
                try:
                    # Import here to avoid circular dependency
                    from grai.core.loader.neo4j_loader import execute_cypher

                    result = execute_cypher(neo4j_connection, cypher, parameters={"batch": batch})

                    if verbose:
                        print(f"\n[Batch {batch_num}] Neo4j execution result:")
                        print(f"  Success: {result.success}")
                        print(f"  Statements executed: {result.statements_executed}")
                        print(f"  Records affected: {result.records_affected}")
                        print(f"  Nodes created: {result.nodes_created}")
                        print(f"  Properties set: {result.properties_set}")
                        if result.errors:
                            print(f"  Errors: {result.errors}")

                    if result.success:
                        rows_loaded += len(batch)
                    else:
                        errors.append(f"Batch {batch_num} failed: {'; '.join(result.errors)}")

                except Exception as e:
                    errors.append(f"Neo4j error in batch {batch_num}: {e}")
                    if verbose:
                        print(f"\n[Batch {batch_num}] Error: {e}")

        duration = time.time() - start_time

        return LoadResult(
            success=len(errors) == 0,
            entity_name=entity.entity,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded if not dry_run else 0,
            errors=errors,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        return LoadResult(
            success=False,
            entity_name=entity.entity,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded,
            errors=[str(e)],
            duration_seconds=duration,
        )


def load_relation_from_bigquery(
    relation: Relation,
    bigquery_connection: BigQueryConnection,
    neo4j_connection: Any,
    limit: Optional[int] = None,
    batch_size: int = 1000,
    dry_run: bool = False,
    verbose: bool = False,
) -> LoadResult:
    """
    Load relation data from BigQuery to Neo4j.

    Args:
        relation: Relation definition.
        bigquery_connection: BigQuery connection config.
        neo4j_connection: Neo4j connection.
        limit: Optional row limit.
        batch_size: Rows per batch.
        dry_run: If True, extract but don't load.

    Returns:
        LoadResult with operation details.
    """
    import time

    start_time = time.time()
    rows_extracted = 0
    rows_loaded = 0
    errors = []

    try:
        extractor = BigQueryExtractor(bigquery_connection)
        extractor.connect()

        # Get source table
        source_name = relation.get_source_name()

        # Determine columns to extract
        columns = []
        # Add mapping keys
        columns.append(relation.mappings.from_key)
        columns.append(relation.mappings.to_key)
        # Add relation properties
        for prop in relation.properties:
            if prop.name not in columns:
                columns.append(prop.name)

        # Extract and load
        batch_num = 0
        for batch in extractor.extract_table(
            source_name, columns=columns, limit=limit, batch_size=batch_size
        ):
            batch_num += 1
            rows_extracted += len(batch)

            if verbose:
                print(f"\n[Batch {batch_num}] Extracted {len(batch)} rows")
                if batch:
                    print(f"  Sample row: {batch[0]}")

            if not dry_run:
                cypher = _generate_relation_batch_cypher(relation, batch)

                if verbose:
                    print(f"\n[Batch {batch_num}] Generated Cypher:")
                    print(f"  {cypher[:200]}..." if len(cypher) > 200 else f"  {cypher}")

                try:
                    from grai.core.loader.neo4j_loader import execute_cypher

                    result = execute_cypher(neo4j_connection, cypher, parameters={"batch": batch})

                    if verbose:
                        print(f"\n[Batch {batch_num}] Neo4j execution result:")
                        print(f"  Success: {result.success}")
                        print(f"  Statements executed: {result.statements_executed}")
                        print(f"  Records affected: {result.records_affected}")
                        print(f"  Relationships created: {result.relationships_created}")
                        print(f"  Properties set: {result.properties_set}")
                        if result.errors:
                            print(f"  Errors: {result.errors}")

                    if result.success:
                        rows_loaded += len(batch)
                    else:
                        errors.append(f"Batch {batch_num} failed: {'; '.join(result.errors)}")

                except Exception as e:
                    errors.append(f"Neo4j error in batch {batch_num}: {e}")
                    if verbose:
                        print(f"\n[Batch {batch_num}] Error: {e}")

        duration = time.time() - start_time

        return LoadResult(
            success=len(errors) == 0,
            entity_name=relation.relation,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded if not dry_run else 0,
            errors=errors,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        return LoadResult(
            success=False,
            entity_name=relation.relation,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded,
            errors=[str(e)],
            duration_seconds=duration,
        )


def _generate_batch_cypher(entity: Entity, batch: List[Dict[str, Any]]) -> str:
    """
    Generate Cypher for a batch of entity rows.

    Uses UNWIND for efficient batch loading.
    """
    # Build property SET clause
    prop_sets = []
    for prop in entity.properties:
        prop_sets.append(f"n.{prop.name} = row.{prop.name}")

    # Build keys for MERGE
    key_conditions = []
    for key in entity.keys:
        key_conditions.append(f"{key}: row.{key}")

    keys_str = ", ".join(key_conditions)
    set_clause = ",\n    ".join(prop_sets) if prop_sets else ""

    cypher = f"""
UNWIND $batch AS row
MERGE (n:{entity.entity} {{{keys_str}}})
"""

    if set_clause:
        cypher += f"SET {set_clause}\n"

    return cypher


def _generate_relation_batch_cypher(relation: Relation, batch: List[Dict[str, Any]]) -> str:
    """
    Generate Cypher for a batch of relation rows.
    """
    from_entity = relation.from_entity
    to_entity = relation.to_entity
    from_key = relation.mappings.from_key
    to_key = relation.mappings.to_key

    # Build property SET clause
    prop_sets = []
    for prop in relation.properties:
        prop_sets.append(f"r.{prop.name} = row.{prop.name}")

    set_clause = ",\n    ".join(prop_sets) if prop_sets else ""

    cypher = f"""
UNWIND $batch AS row
MATCH (from:{from_entity} {{{from_key}: row.{from_key}}})
MATCH (to:{to_entity} {{{to_key}: row.{to_key}}})
MERGE (from)-[r:{relation.relation}]->(to)
"""

    if set_clause:
        cypher += f"SET {set_clause}\n"

    return cypher

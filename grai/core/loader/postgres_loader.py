"""
PostgreSQL Data Loader for grai.build.

This module provides functionality to extract data from PostgreSQL databases
and load it into Neo4j as part of knowledge graph construction.

Similar to BigQuery loader but for PostgreSQL sources.
"""

from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional, Tuple

from ..models import Entity, Relation


@dataclass
class PostgresConnection:
    """
    PostgreSQL connection configuration.

    Attributes:
        host: PostgreSQL server hostname or IP
        port: PostgreSQL server port (default: 5432)
        database: Database name
        user: Username for authentication
        password: Password for authentication
        schema: Default schema (default: 'public')
        ssl_mode: SSL mode ('disable', 'require', 'verify-ca', 'verify-full')

    Example:
        >>> conn = PostgresConnection(
        ...     host="localhost",
        ...     database="analytics",
        ...     user="grai",
        ...     password="secret"
        ... )
    """

    host: str
    database: str
    user: str
    password: str
    port: int = 5432
    schema: str = "public"
    ssl_mode: str = "prefer"


@dataclass
class LoadResult:
    """
    Result of a data loading operation.

    Attributes:
        success: Whether the operation succeeded
        entity_name: Name of entity or relation loaded
        rows_extracted: Number of rows extracted from PostgreSQL
        rows_loaded: Number of rows loaded to Neo4j
        errors: List of error messages
        duration_seconds: Time taken for operation

    Example:
        >>> result = LoadResult(
        ...     success=True,
        ...     entity_name="customer",
        ...     rows_extracted=1000,
        ...     rows_loaded=1000,
        ...     errors=[],
        ...     duration_seconds=2.5
        ... )
    """

    success: bool
    entity_name: str
    rows_extracted: int
    rows_loaded: int
    errors: List[str]
    duration_seconds: float


class PostgresExtractor:
    """
    PostgreSQL data extractor.

    Connects to PostgreSQL and extracts data for entities and relations.

    Attributes:
        connection: PostgreSQL connection configuration
        conn: Active psycopg2 connection (set after connect())
        cursor: Active database cursor (set after connect())

    Example:
        >>> extractor = PostgresExtractor(postgres_connection)
        >>> extractor.connect()
        >>> rows = list(extractor.extract_table("customers", limit=100))
        >>> extractor.close()
    """

    def __init__(self, connection: PostgresConnection):
        """
        Initialize extractor with connection config.

        Args:
            connection: PostgreSQL connection configuration
        """
        self.connection = connection
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """
        Establish connection to PostgreSQL.

        Raises:
            ImportError: If psycopg2 is not installed
            Exception: If connection fails

        Example:
            >>> extractor = PostgresExtractor(connection)
            >>> extractor.connect()
        """
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install psycopg2-binary"
            )

        try:
            self.conn = psycopg2.connect(
                host=self.connection.host,
                port=self.connection.port,
                database=self.connection.database,
                user=self.connection.user,
                password=self.connection.password,
                sslmode=self.connection.ssl_mode,
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise Exception(f"Failed to connect to PostgreSQL: {e}")

    def close(self) -> None:
        """
        Close PostgreSQL connection and cursor.

        Example:
            >>> extractor.close()
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.cursor = None
        self.conn = None

    def extract_table(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        limit: Optional[int] = None,
        batch_size: int = 1000,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Extract data from a PostgreSQL table in batches.

        Args:
            table_name: Name of table to extract (can include schema: 'schema.table')
            columns: List of columns to select (None = all columns)
            where_clause: SQL WHERE clause (without 'WHERE' keyword)
            limit: Maximum number of rows to extract
            batch_size: Number of rows per batch

        Yields:
            Batches of rows as list of dictionaries

        Raises:
            ValueError: If table_name is empty
            Exception: If query execution fails

        Example:
            >>> for batch in extractor.extract_table("customers", limit=1000):
            ...     print(f"Got batch of {len(batch)} rows")
        """
        if not table_name:
            raise ValueError("table_name is required")

        if self.conn is None or self.cursor is None:
            raise Exception("Not connected to PostgreSQL. Call connect() first.")

        # Build column list
        column_str = ", ".join(columns) if columns else "*"

        # Build full table name (handle schema prefix)
        if "." not in table_name and self.connection.schema:
            full_table_name = f"{self.connection.schema}.{table_name}"
        else:
            full_table_name = table_name

        # Build query
        query = f"SELECT {column_str} FROM {full_table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        try:
            self.cursor.execute(query)
        except Exception as e:
            raise Exception(f"Failed to execute query: {e}")

        # Get column names from cursor description
        col_names = [desc[0] for desc in self.cursor.description]

        # Fetch and yield batches
        while True:
            rows = self.cursor.fetchmany(batch_size)
            if not rows:
                break

            # Convert rows to dictionaries
            batch = [dict(zip(col_names, row)) for row in rows]
            yield batch

    def extract_query(
        self, query: str, batch_size: int = 1000
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Execute a custom SQL query and extract results in batches.

        Args:
            query: SQL query to execute
            batch_size: Number of rows per batch

        Yields:
            Batches of rows as list of dictionaries

        Raises:
            ValueError: If query is empty
            Exception: If query execution fails

        Example:
            >>> query = "SELECT * FROM customers WHERE region = 'US'"
            >>> for batch in extractor.extract_query(query):
            ...     process_batch(batch)
        """
        if not query:
            raise ValueError("query is required")

        if self.conn is None or self.cursor is None:
            raise Exception("Not connected to PostgreSQL. Call connect() first.")

        try:
            self.cursor.execute(query)
        except Exception as e:
            raise Exception(f"Failed to execute query: {e}")

        # Get column names
        col_names = [desc[0] for desc in self.cursor.description]

        # Fetch and yield batches
        while True:
            rows = self.cursor.fetchmany(batch_size)
            if not rows:
                break

            batch = [dict(zip(col_names, row)) for row in rows]
            yield batch

    def get_table_schema(self, table_name: str) -> List[Tuple[str, str]]:
        """
        Get column names and types for a table.

        Args:
            table_name: Name of table (can include schema)

        Returns:
            List of (column_name, data_type) tuples

        Example:
            >>> schema = extractor.get_table_schema("customers")
            >>> print(schema)
            [('customer_id', 'integer'), ('name', 'character varying'), ...]
        """
        if self.conn is None or self.cursor is None:
            raise Exception("Not connected to PostgreSQL. Call connect() first.")

        # Parse schema and table name
        if "." in table_name:
            schema, table = table_name.split(".", 1)
        else:
            schema = self.connection.schema
            table = table_name

        query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """

        self.cursor.execute(query, (schema, table))
        return self.cursor.fetchall()


def connect_postgres(connection: PostgresConnection) -> PostgresExtractor:
    """
    Create and connect a PostgreSQL extractor.

    Args:
        connection: PostgreSQL connection configuration

    Returns:
        Connected PostgresExtractor instance

    Example:
        >>> extractor = connect_postgres(postgres_connection)
        >>> rows = list(extractor.extract_table("customers"))
    """
    extractor = PostgresExtractor(connection)
    extractor.connect()
    return extractor


def extract_data(
    extractor: PostgresExtractor,
    entity: Entity,
    limit: Optional[int] = None,
    batch_size: int = 1000,
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Extract data for an entity from PostgreSQL.

    Args:
        extractor: Connected PostgreSQL extractor
        entity: Entity definition with source configuration
        limit: Optional row limit
        batch_size: Rows per batch

    Yields:
        Batches of entity data

    Example:
        >>> for batch in extract_data(extractor, customer_entity, limit=1000):
        ...     print(f"Processing {len(batch)} customers")
    """
    source_name = entity.source.name

    # Check if it's a custom query or table
    if source_name.upper().startswith("SELECT "):
        # Custom query
        yield from extractor.extract_query(source_name, batch_size=batch_size)
    else:
        # Table extraction
        yield from extractor.extract_table(
            table_name=source_name, limit=limit, batch_size=batch_size
        )


def _generate_batch_cypher(entity: Entity, batch: List[Dict[str, Any]]) -> str:
    """
    Generate Cypher for loading a batch of entity data.

    Args:
        entity: Entity definition
        batch: Batch of rows to load

    Returns:
        Cypher UNWIND statement

    Example:
        >>> cypher = _generate_batch_cypher(customer_entity, batch)
    """
    # Build MERGE statement with UNWIND for batch processing
    # UNWIND $batch AS row
    # MERGE (n:EntityLabel {key: row.key_property})
    # SET n.prop1 = row.prop1, n.prop2 = row.prop2, ...

    entity_label = entity.entity.capitalize()
    key_props = entity.keys

    # Build MERGE clause with key properties
    key_conditions = []
    for key in key_props:
        key_conditions.append(f"{key}: row.{key}")
    merge_keys = ", ".join(key_conditions)

    # Build SET clause for all properties (excluding keys)
    set_clauses = []
    for prop in entity.properties:
        if prop.name not in key_props:
            set_clauses.append(f"n.{prop.name} = row.{prop.name}")

    cypher_parts = [
        "UNWIND $batch AS row",
        f"MERGE (n:{entity_label} {{{merge_keys}}})",
    ]

    if set_clauses:
        cypher_parts.append("SET " + ", ".join(set_clauses))

    return "\n".join(cypher_parts)


def _generate_relation_batch_cypher(relation: Relation, batch: List[Dict[str, Any]]) -> str:
    """
    Generate Cypher for loading a batch of relation data.

    Args:
        relation: Relation definition
        batch: Batch of rows to load

    Returns:
        Cypher UNWIND statement

    Example:
        >>> cypher = _generate_relation_batch_cypher(purchased_relation, batch)
    """
    # Build MATCH ... MERGE pattern for relationships
    # UNWIND $batch AS row
    # MATCH (from:FromEntity {from_key: row.from_key_col})
    # MATCH (to:ToEntity {to_key: row.to_key_col})
    # MERGE (from)-[r:RELATION_TYPE]->(to)
    # SET r.prop1 = row.prop1, r.prop2 = row.prop2, ...

    from_label = relation.from_entity.capitalize()
    to_label = relation.to_entity.capitalize()
    rel_type = relation.relation

    # Get key mappings from RelationMapping object
    from_key = relation.mappings.from_key
    to_key = relation.mappings.to_key

    # Build SET clause for relationship properties
    set_clauses = []
    if relation.properties:
        for prop in relation.properties:
            set_clauses.append(f"r.{prop.name} = row.{prop.name}")

    cypher_parts = [
        "UNWIND $batch AS row",
        f"MATCH (from:{from_label} {{{from_key}: row.{from_key}}})",
        f"MATCH (to:{to_label} {{{to_key}: row.{to_key}}})",
        f"MERGE (from)-[r:{rel_type}]->(to)",
    ]

    if set_clauses:
        cypher_parts.append("SET " + ", ".join(set_clauses))

    return "\n".join(cypher_parts)


def load_entity_from_postgres(
    entity: Entity,
    postgres_connection: PostgresConnection,
    neo4j_connection: Any,  # Neo4jConnection from neo4j_loader
    limit: Optional[int] = None,
    batch_size: int = 1000,
    dry_run: bool = False,
    verbose: bool = False,
) -> LoadResult:
    """
    Load entity data from PostgreSQL to Neo4j.

    Args:
        entity: Entity definition.
        postgres_connection: PostgreSQL connection config.
        neo4j_connection: Neo4j connection (from neo4j_loader).
        limit: Optional row limit.
        batch_size: Rows per batch.
        dry_run: If True, extract but don't load to Neo4j.
        verbose: Print progress information.

    Returns:
        LoadResult with operation details.

    Example:
        >>> result = load_entity_from_postgres(
        ...     entity=customer_entity,
        ...     postgres_connection=pg_conn,
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
        # Connect to PostgreSQL
        extractor = PostgresExtractor(postgres_connection)
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
                cypher = _generate_batch_cypher(entity, batch)

                if verbose:
                    print(f"  Generated Cypher ({len(cypher)} chars)")

                # Execute Cypher
                from ..loader.neo4j_loader import execute_cypher

                result = execute_cypher(neo4j_connection, cypher, parameters={"batch": batch})

                if result.success:
                    rows_loaded += len(batch)
                    if verbose:
                        print(f"  ✅ Loaded {len(batch)} rows to Neo4j")
                else:
                    errors.extend(result.errors)
                    if verbose:
                        print(f"  ❌ Failed to load batch: {result.errors}")

        extractor.close()

        duration = time.time() - start_time
        return LoadResult(
            success=len(errors) == 0,
            entity_name=entity.entity,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded,
            errors=errors,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        errors.append(str(e))
        return LoadResult(
            success=False,
            entity_name=entity.entity,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded,
            errors=errors,
            duration_seconds=duration,
        )


def load_relation_from_postgres(
    relation: Relation,
    postgres_connection: PostgresConnection,
    neo4j_connection: Any,
    limit: Optional[int] = None,
    batch_size: int = 1000,
    dry_run: bool = False,
    verbose: bool = False,
) -> LoadResult:
    """
    Load relation data from PostgreSQL to Neo4j.

    Args:
        relation: Relation definition.
        postgres_connection: PostgreSQL connection config.
        neo4j_connection: Neo4j connection.
        limit: Optional row limit.
        batch_size: Rows per batch.
        dry_run: If True, extract but don't load to Neo4j.
        verbose: Print progress information.

    Returns:
        LoadResult with operation details.

    Example:
        >>> result = load_relation_from_postgres(
        ...     relation=purchased_relation,
        ...     postgres_connection=pg_conn,
        ...     neo4j_connection=neo4j_conn
        ... )
        >>> print(f"Loaded {result.rows_loaded} relationships")
    """
    import time

    start_time = time.time()
    rows_extracted = 0
    rows_loaded = 0
    errors = []

    try:
        # Connect to PostgreSQL
        extractor = PostgresExtractor(postgres_connection)
        extractor.connect()

        # Build query or table name from relation source
        source_name = relation.source.name

        # Extract and load data in batches
        batch_num = 0
        if source_name.upper().startswith("SELECT "):
            batches = extractor.extract_query(source_name, batch_size=batch_size)
        else:
            batches = extractor.extract_table(source_name, limit=limit, batch_size=batch_size)

        for batch in batches:
            batch_num += 1
            rows_extracted += len(batch)

            if verbose:
                print(f"\n[Batch {batch_num}] Extracted {len(batch)} relation rows")

            if not dry_run:
                # Generate Cypher for this batch
                cypher = _generate_relation_batch_cypher(relation, batch)

                # Execute Cypher
                from ..loader.neo4j_loader import execute_cypher

                result = execute_cypher(neo4j_connection, cypher, parameters={"batch": batch})

                if result.success:
                    rows_loaded += len(batch)
                    if verbose:
                        print(f"  ✅ Created {len(batch)} relationships")
                else:
                    errors.extend(result.errors)
                    if verbose:
                        print(f"  ❌ Failed: {result.errors}")

        extractor.close()

        duration = time.time() - start_time
        return LoadResult(
            success=len(errors) == 0,
            entity_name=relation.relation,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded,
            errors=errors,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        errors.append(str(e))
        return LoadResult(
            success=False,
            entity_name=relation.relation,
            rows_extracted=rows_extracted,
            rows_loaded=rows_loaded,
            errors=errors,
            duration_seconds=duration,
        )

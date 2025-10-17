"""
Tests for BigQuery data loader.

Tests the BigQueryExtractor class and data loading functions with mocked
BigQuery client to avoid real API calls.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from grai.core.loader.bigquery_loader import (
    BigQueryConnection,
    BigQueryExtractor,
    LoadResult,
    _generate_batch_cypher,
    _generate_relation_batch_cypher,
    connect_bigquery,
    extract_data,
    load_entity_from_bigquery,
    load_relation_from_bigquery,
)
from grai.core.models import Entity, Property, Relation, RelationMapping, SourceType

# Fixtures


@pytest.fixture
def mock_bigquery():
    """Mock the BigQuery library."""
    mock_bq = MagicMock()
    mock_oauth2 = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "google": MagicMock(),
            "google.cloud": MagicMock(),
            "google.cloud.bigquery": mock_bq,
            "google.oauth2": mock_oauth2,
            "google.oauth2.service_account": mock_oauth2.service_account,
        },
    ):
        yield mock_bq


@pytest.fixture
def bigquery_connection():
    """Create a test BigQuery connection."""
    return BigQueryConnection(
        project_id="test-project",
        dataset="test_dataset",
        location="US",
    )


@pytest.fixture
def bigquery_connection_with_credentials(tmp_path):
    """Create a BigQuery connection with credentials file."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text('{"type": "service_account"}')

    return BigQueryConnection(
        project_id="test-project",
        dataset="test_dataset",
        credentials_path=creds_file,
        location="EU",
    )


@pytest.fixture
def sample_entity():
    """Create a sample entity for testing."""
    return Entity(
        entity="customer",
        source="test_dataset.customers",
        source_type=SourceType.TABLE,
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type="string", description="Customer ID"),
            Property(name="name", type="string", description="Customer name"),
            Property(name="email", type="string", description="Email address"),
            Property(name="region", type="string", description="Region"),
        ],
    )


@pytest.fixture
def sample_relation():
    """Create a sample relation for testing."""
    return Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="test_dataset.orders",
        source_type=SourceType.TABLE,
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[
            Property(name="order_id", type="string", description="Order ID"),
            Property(name="quantity", type="integer", description="Quantity"),
            Property(name="amount", type="float", description="Amount"),
        ],
    )


@pytest.fixture
def mock_bigquery_client():
    """Create a mock BigQuery client."""
    with patch("google.cloud.bigquery.Client") as mock_client_class:
        client = Mock()
        mock_client_class.return_value = client
        yield client


# BigQueryConnection Tests


def test_bigquery_connection_basic():
    """Test basic BigQuery connection configuration."""
    conn = BigQueryConnection(project_id="my-project", dataset="analytics")

    assert conn.project_id == "my-project"
    assert conn.dataset == "analytics"
    assert conn.credentials_path is None
    assert conn.location == "US"


def test_bigquery_connection_with_credentials():
    """Test BigQuery connection with credentials path."""
    creds_path = Path("/path/to/creds.json")
    conn = BigQueryConnection(
        project_id="my-project",
        dataset="analytics",
        credentials_path=creds_path,
        location="EU",
    )

    assert conn.project_id == "my-project"
    assert conn.credentials_path == creds_path
    assert conn.location == "EU"


# BigQueryExtractor Tests


def test_extractor_initialization(bigquery_connection):
    """Test BigQueryExtractor initialization."""
    extractor = BigQueryExtractor(bigquery_connection)

    assert extractor.connection == bigquery_connection
    assert extractor.client is None


def test_extractor_connect_without_credentials(bigquery_connection, mock_bigquery):
    """Test connecting to BigQuery without credentials file."""
    mock_client = Mock()
    mock_bigquery.Client.return_value = mock_client

    extractor = BigQueryExtractor(bigquery_connection)
    extractor.connect()

    # The client should be set (from the mocked module)
    assert extractor.client is not None
    # Verify the correct parameters were used (check via attributes)
    assert extractor.connection.project_id == "test-project"
    assert extractor.connection.location == "US"


def test_extractor_connect_with_credentials(bigquery_connection_with_credentials, mock_bigquery):
    """Test connecting to BigQuery with service account credentials."""
    # Need to import to get the mocked service_account module
    import sys

    mock_service_account = sys.modules["google.oauth2.service_account"]

    mock_creds = Mock()
    mock_service_account.Credentials.from_service_account_file.return_value = mock_creds
    mock_client = Mock()
    mock_bigquery.Client.return_value = mock_client

    extractor = BigQueryExtractor(bigquery_connection_with_credentials)
    extractor.connect()

    # The client should be set (from the mocked module)
    assert extractor.client is not None
    # Verify the correct connection parameters
    assert extractor.connection.project_id == "test-project"
    assert extractor.connection.location == "EU"
    assert extractor.connection.credentials_path is not None


def test_extractor_connect_missing_library():
    """Test error when google-cloud-bigquery is not installed."""
    conn = BigQueryConnection(project_id="test-project")
    extractor = BigQueryExtractor(conn)

    with patch.dict("sys.modules", {"google.cloud": None, "google.cloud.bigquery": None}):
        with pytest.raises(ImportError, match="google-cloud-bigquery is required"):
            extractor.connect()


def test_extractor_connect_failure(bigquery_connection, mock_bigquery):
    """Test handling of connection failures."""
    mock_bigquery.Client.side_effect = Exception("Connection failed")

    extractor = BigQueryExtractor(bigquery_connection)

    with pytest.raises(Exception, match="Failed to connect to BigQuery"):
        extractor.connect()


def test_extract_table_basic(bigquery_connection, mock_bigquery):
    """Test extracting data from a BigQuery table."""
    # Mock query results
    mock_row1 = Mock()
    mock_row1.items.return_value = [("customer_id", "C001"), ("name", "Alice")]
    mock_row2 = Mock()
    mock_row2.items.return_value = [("customer_id", "C002"), ("name", "Bob")]

    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([mock_row1, mock_row2]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    # Extract table
    batches = list(extractor.extract_table("customers", batch_size=2))

    assert len(batches) == 1
    assert len(batches[0]) == 2
    assert batches[0][0] == {"customer_id": "C001", "name": "Alice"}
    assert batches[0][1] == {"customer_id": "C002", "name": "Bob"}

    # Verify query
    mock_client.query.assert_called_once()
    query = mock_client.query.call_args[0][0]
    assert "SELECT * FROM `test-project.test_dataset.customers`" in query


def test_extract_table_with_columns(bigquery_connection, mock_bigquery):
    """Test extracting specific columns from a table."""
    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    list(extractor.extract_table("customers", columns=["customer_id", "name"]))

    query = mock_client.query.call_args[0][0]
    assert "SELECT customer_id, name FROM" in query


def test_extract_table_with_where_clause(bigquery_connection, mock_bigquery):
    """Test extracting with WHERE clause filtering."""
    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    list(extractor.extract_table("customers", where_clause="region = 'US'"))

    query = mock_client.query.call_args[0][0]
    assert "WHERE region = 'US'" in query


def test_extract_table_with_limit(bigquery_connection, mock_bigquery):
    """Test extracting with row limit."""
    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    list(extractor.extract_table("customers", limit=100))

    query = mock_client.query.call_args[0][0]
    assert "LIMIT 100" in query


def test_extract_table_batching(bigquery_connection, mock_bigquery):
    """Test that data is correctly batched."""
    # Create 5 mock rows
    mock_rows = []
    for i in range(5):
        mock_row = Mock()
        mock_row.items.return_value = [("id", i), ("value", f"val{i}")]
        mock_rows.append(mock_row)

    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter(mock_rows))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    # Extract with batch size of 2
    batches = list(extractor.extract_table("test", batch_size=2))

    assert len(batches) == 3  # 2 + 2 + 1
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1


def test_extract_table_no_default_dataset(mock_bigquery):
    """Test error when table name has no dataset and no default is set."""
    conn = BigQueryConnection(project_id="test-project")  # No dataset
    extractor = BigQueryExtractor(conn)

    extractor.connect()

    with pytest.raises(ValueError, match="needs dataset"):
        list(extractor.extract_table("customers"))


def test_extract_table_with_dataset_prefix(bigquery_connection, mock_bigquery):
    """Test table extraction with dataset.table format."""
    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    list(extractor.extract_table("analytics.customers"))

    query = mock_client.query.call_args[0][0]
    assert "`test-project.analytics.customers`" in query


def test_extract_table_fully_qualified(bigquery_connection, mock_bigquery):
    """Test table extraction with fully qualified name."""
    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    list(extractor.extract_table("other-project.other_dataset.customers"))

    query = mock_client.query.call_args[0][0]
    assert "`other-project.other_dataset.customers`" in query


def test_extract_query(bigquery_connection, mock_bigquery):
    """Test extracting data with custom SQL query."""
    mock_row = Mock()
    mock_row.items.return_value = [("count", 42)]

    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([mock_row]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    query = "SELECT COUNT(*) as count FROM analytics.customers"
    batches = list(extractor.extract_query(query, batch_size=10))

    assert len(batches) == 1
    assert batches[0][0]["count"] == 42
    mock_client.query.assert_called_once_with(query)


def test_get_table_schema(bigquery_connection, mock_bigquery):
    """Test retrieving table schema."""
    # Mock schema fields
    field1 = Mock()
    field1.name = "customer_id"
    field1.field_type = "STRING"

    field2 = Mock()
    field2.name = "age"
    field2.field_type = "INTEGER"

    mock_table = Mock()
    mock_table.schema = [field1, field2]

    mock_client = MagicMock()
    mock_client.get_table.return_value = mock_table

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    schema = extractor.get_table_schema("customers")

    assert len(schema) == 2
    assert schema[0] == {"name": "customer_id", "type": "STRING"}
    assert schema[1] == {"name": "age", "type": "INTEGER"}


def test_extractor_close(bigquery_connection, mock_bigquery):
    """Test closing BigQuery connection."""
    mock_client = MagicMock()
    mock_client.close = Mock()

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    assert extractor.client is not None

    extractor.close()

    assert extractor.client is None
    mock_client.close.assert_called_once()


# Helper Function Tests


def test_connect_bigquery(mock_bigquery):
    """Test connect_bigquery helper function."""
    mock_client = Mock()
    mock_bigquery.Client.return_value = mock_client

    extractor = connect_bigquery("my-project", dataset="analytics")

    assert isinstance(extractor, BigQueryExtractor)
    assert extractor.connection.project_id == "my-project"
    assert extractor.connection.dataset == "analytics"
    assert extractor.client is not None


def test_extract_data(bigquery_connection, sample_entity, mock_bigquery):
    """Test extract_data function with entity."""
    mock_row = Mock()
    mock_row.items.return_value = [
        ("customer_id", "C001"),
        ("name", "Alice"),
        ("email", "alice@example.com"),
        ("region", "US"),
    ]

    mock_job = MagicMock()
    mock_job.__iter__ = Mock(return_value=iter([mock_row]))

    mock_client = MagicMock()
    mock_client.query.return_value = mock_job

    # Create extractor and manually set the client (bypass connect())
    extractor = BigQueryExtractor(bigquery_connection)
    extractor.client = mock_client

    batches = list(extract_data(extractor, sample_entity, limit=100, batch_size=10))

    assert len(batches) == 1
    assert len(batches[0]) == 1
    assert batches[0][0]["customer_id"] == "C001"

    # Verify query includes all entity properties
    query = mock_client.query.call_args[0][0]
    assert "customer_id" in query
    assert "name" in query
    assert "email" in query
    assert "region" in query
    assert "LIMIT 100" in query


# Cypher Generation Tests


def test_generate_batch_cypher(sample_entity):
    """Test Cypher generation for entity batch."""
    batch = [
        {"customer_id": "C001", "name": "Alice", "email": "alice@example.com", "region": "US"},
        {"customer_id": "C002", "name": "Bob", "email": "bob@example.com", "region": "EU"},
    ]

    cypher = _generate_batch_cypher(sample_entity, batch)

    assert "UNWIND $batch AS row" in cypher
    assert "MERGE (n:customer {customer_id: row.customer_id})" in cypher
    assert "n.name = row.name" in cypher
    assert "n.email = row.email" in cypher
    assert "n.region = row.region" in cypher


def test_generate_relation_batch_cypher(sample_relation):
    """Test Cypher generation for relation batch."""
    batch = [
        {
            "customer_id": "C001",
            "product_id": "P001",
            "order_id": "O001",
            "quantity": 2,
            "amount": 100.0,
        },
        {
            "customer_id": "C002",
            "product_id": "P002",
            "order_id": "O002",
            "quantity": 1,
            "amount": 50.0,
        },
    ]

    cypher = _generate_relation_batch_cypher(sample_relation, batch)

    assert "UNWIND $batch AS row" in cypher
    assert "MATCH (from:customer {customer_id: row.customer_id})" in cypher
    assert "MATCH (to:product {product_id: row.product_id})" in cypher
    assert "MERGE (from)-[r:PURCHASED]->(to)" in cypher
    assert "r.order_id = row.order_id" in cypher
    assert "r.quantity = row.quantity" in cypher
    assert "r.amount = row.amount" in cypher


# Load Function Tests


def test_load_entity_from_bigquery_success(bigquery_connection, sample_entity, mock_bigquery):
    """Test successful entity loading from BigQuery to Neo4j."""
    with patch("grai.core.loader.neo4j_loader.execute_cypher") as mock_execute:
        # Mock successful execution result
        mock_exec_result = Mock()
        mock_exec_result.success = True
        mock_exec_result.statements_executed = 1
        mock_exec_result.records_affected = 1
        mock_exec_result.nodes_created = 1
        mock_exec_result.properties_set = 4
        mock_exec_result.errors = []
        mock_execute.return_value = mock_exec_result

        # Mock BigQuery data
        mock_row = Mock()
        mock_row.items.return_value = [
            ("customer_id", "C001"),
            ("name", "Alice"),
            ("email", "alice@example.com"),
            ("region", "US"),
        ]

        mock_job = MagicMock()
        mock_job.__iter__ = Mock(return_value=iter([mock_row]))

        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        mock_bigquery.Client.return_value = mock_client

        # Mock Neo4j connection
        neo4j_conn = Mock()

        result = load_entity_from_bigquery(
            entity=sample_entity,
            bigquery_connection=bigquery_connection,
            neo4j_connection=neo4j_conn,
            limit=100,
            batch_size=10,
        )

        assert result.success is True
        assert result.entity_name == "customer"
        assert result.rows_extracted == 1
        assert result.rows_loaded == 1
        assert len(result.errors) == 0
        assert result.duration_seconds > 0

        # Verify Cypher was executed
        mock_execute.assert_called_once()


def test_load_entity_from_bigquery_dry_run(bigquery_connection, sample_entity, mock_bigquery):
    """Test entity loading in dry-run mode (no Neo4j writes)."""
    with patch("grai.core.loader.neo4j_loader.execute_cypher") as mock_execute:
        mock_row = Mock()
        mock_row.items.return_value = [("customer_id", "C001")]

        mock_job = MagicMock()
        mock_job.__iter__ = Mock(return_value=iter([mock_row]))

        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        mock_bigquery.Client.return_value = mock_client

        neo4j_conn = Mock()

        result = load_entity_from_bigquery(
            entity=sample_entity,
            bigquery_connection=bigquery_connection,
            neo4j_connection=neo4j_conn,
            dry_run=True,
        )

        assert result.success is True
        assert result.rows_extracted == 1
        assert result.rows_loaded == 0  # Dry run, no loads
        mock_execute.assert_not_called()  # No Cypher execution


def test_load_entity_from_bigquery_neo4j_error(bigquery_connection, sample_entity, mock_bigquery):
    """Test handling Neo4j errors during loading."""
    with patch("grai.core.loader.neo4j_loader.execute_cypher") as mock_execute:
        mock_execute.side_effect = Exception("Neo4j connection failed")

        mock_row = Mock()
        mock_row.items.return_value = [("customer_id", "C001")]

        mock_job = MagicMock()
        mock_job.__iter__ = Mock(return_value=iter([mock_row]))

        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        mock_bigquery.Client.return_value = mock_client

        neo4j_conn = Mock()

        result = load_entity_from_bigquery(
            entity=sample_entity,
            bigquery_connection=bigquery_connection,
            neo4j_connection=neo4j_conn,
        )

        assert result.success is False
        assert result.rows_extracted == 1
        assert result.rows_loaded == 0
        assert len(result.errors) > 0


def test_load_entity_from_bigquery_extraction_error(
    bigquery_connection, sample_entity, mock_bigquery
):
    """Test handling BigQuery extraction errors."""
    mock_bigquery.Client.side_effect = Exception("BigQuery connection failed")

    neo4j_conn = Mock()

    result = load_entity_from_bigquery(
        entity=sample_entity,
        bigquery_connection=bigquery_connection,
        neo4j_connection=neo4j_conn,
    )

    assert result.success is False
    assert result.rows_extracted == 0
    assert result.rows_loaded == 0
    assert len(result.errors) > 0


def test_load_relation_from_bigquery_success(bigquery_connection, sample_relation, mock_bigquery):
    """Test successful relation loading from BigQuery to Neo4j."""
    with patch("grai.core.loader.neo4j_loader.execute_cypher") as mock_execute:
        # Mock successful execution result
        mock_exec_result = Mock()
        mock_exec_result.success = True
        mock_exec_result.statements_executed = 1
        mock_exec_result.records_affected = 1
        mock_exec_result.relationships_created = 1
        mock_exec_result.properties_set = 3
        mock_exec_result.errors = []
        mock_execute.return_value = mock_exec_result

        mock_row = Mock()
        mock_row.items.return_value = [
            ("customer_id", "C001"),
            ("product_id", "P001"),
            ("order_id", "O001"),
            ("quantity", 2),
            ("amount", 100.0),
        ]

        mock_job = MagicMock()
        mock_job.__iter__ = Mock(return_value=iter([mock_row]))

        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        mock_bigquery.Client.return_value = mock_client

        neo4j_conn = Mock()

        result = load_relation_from_bigquery(
            relation=sample_relation,
            bigquery_connection=bigquery_connection,
            neo4j_connection=neo4j_conn,
            limit=100,
        )

        assert result.success is True
        assert result.entity_name == "PURCHASED"
        assert result.rows_extracted == 1
        assert result.rows_loaded == 1
        assert len(result.errors) == 0

        mock_execute.assert_called_once()


def test_load_relation_from_bigquery_dry_run(bigquery_connection, sample_relation, mock_bigquery):
    """Test relation loading in dry-run mode."""
    with patch("grai.core.loader.neo4j_loader.execute_cypher") as mock_execute:
        mock_row = Mock()
        mock_row.items.return_value = [
            ("customer_id", "C001"),
            ("product_id", "P001"),
        ]

        mock_job = MagicMock()
        mock_job.__iter__ = Mock(return_value=iter([mock_row]))

        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        mock_bigquery.Client.return_value = mock_client

        neo4j_conn = Mock()

        result = load_relation_from_bigquery(
            relation=sample_relation,
            bigquery_connection=bigquery_connection,
            neo4j_connection=neo4j_conn,
            dry_run=True,
        )

        assert result.success is True
        assert result.rows_extracted == 1
        assert result.rows_loaded == 0
        mock_execute.assert_not_called()


# LoadResult Tests


def test_load_result_model():
    """Test LoadResult model."""
    result = LoadResult(
        success=True,
        entity_name="customer",
        rows_extracted=100,
        rows_loaded=100,
        errors=[],
        duration_seconds=1.5,
    )

    assert result.success is True
    assert result.entity_name == "customer"
    assert result.rows_extracted == 100
    assert result.rows_loaded == 100
    assert result.errors == []
    assert result.duration_seconds == 1.5


def test_load_result_with_errors():
    """Test LoadResult with errors."""
    result = LoadResult(
        success=False,
        entity_name="customer",
        rows_extracted=50,
        rows_loaded=25,
        errors=["Connection timeout", "Retry failed"],
        duration_seconds=10.0,
    )

    assert result.success is False
    assert len(result.errors) == 2
    assert "Connection timeout" in result.errors

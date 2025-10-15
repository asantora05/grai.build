"""
Tests for Neo4j Loader module.

These tests use mocking to avoid requiring a running Neo4j instance.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from grai.core.loader import (
    Neo4jConnection,
    close_connection,
    connect_neo4j,
    execute_cypher,
    execute_cypher_file,
    verify_connection,
)
from grai.core.loader.neo4j_loader import (
    ExecutionResult,
    clear_database,
    execute_cypher_with_retry,
    get_database_info,
    split_cypher_statements,
)


class TestNeo4jConnection:
    """Test Neo4jConnection dataclass."""

    def test_connection_with_defaults(self):
        """Test connection with default values."""
        conn = Neo4jConnection(uri="bolt://localhost:7687", user="neo4j", password="password")

        assert conn.uri == "bolt://localhost:7687"
        assert conn.user == "neo4j"
        assert conn.password == "password"
        assert conn.database == "neo4j"
        assert conn.encrypted is False
        assert conn.max_retry_time == 30

    def test_connection_with_custom_values(self):
        """Test connection with custom values."""
        conn = Neo4jConnection(
            uri="neo4j://prod.example.com:7687",
            user="admin",
            password="secret",
            database="production",
            encrypted=True,
            max_retry_time=60,
        )

        assert conn.database == "production"
        assert conn.encrypted is True
        assert conn.max_retry_time == 60


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_result_defaults(self):
        """Test result with default values."""
        result = ExecutionResult(success=True)

        assert result.success is True
        assert result.statements_executed == 0
        assert result.records_affected == 0
        assert result.execution_time == 0.0
        assert result.errors == []
        assert result.warnings == []

    def test_result_with_values(self):
        """Test result with custom values."""
        result = ExecutionResult(
            success=True,
            statements_executed=5,
            records_affected=100,
            execution_time=1.5,
            errors=["error1"],
            warnings=["warning1"],
        )

        assert result.success is True
        assert result.statements_executed == 5
        assert result.records_affected == 100
        assert result.execution_time == 1.5
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]


class TestSplitCypherStatements:
    """Test splitting Cypher into statements."""

    def test_split_single_statement(self):
        """Test splitting single statement."""
        cypher = "CREATE (n:Person {name: 'Alice'});"
        statements = split_cypher_statements(cypher)

        assert len(statements) == 1
        assert "CREATE" in statements[0]

    def test_split_multiple_statements(self):
        """Test splitting multiple statements."""
        cypher = """
        CREATE (n:Person {name: 'Alice'});
        CREATE (m:Person {name: 'Bob'});
        MATCH (a:Person), (b:Person) WHERE a.name = 'Alice' AND b.name = 'Bob' CREATE (a)-[:KNOWS]->(b);
        """
        statements = split_cypher_statements(cypher)

        assert len(statements) == 3
        assert "Alice" in statements[0]
        assert "Bob" in statements[1]
        assert "KNOWS" in statements[2]

    def test_split_with_comments(self):
        """Test splitting with comments."""
        cypher = """
        // This is a comment
        CREATE (n:Person {name: 'Alice'});
        // Another comment
        CREATE (m:Person {name: 'Bob'});
        """
        statements = split_cypher_statements(cypher)

        assert len(statements) == 2
        assert "Alice" in statements[0]
        assert "Bob" in statements[1]

    def test_split_empty_statements(self):
        """Test splitting filters empty statements."""
        cypher = ";;;CREATE (n:Person);;"
        statements = split_cypher_statements(cypher)

        assert len(statements) == 1
        assert "CREATE" in statements[0]


@patch("grai.core.loader.neo4j_loader.GraphDatabase")
class TestConnectNeo4j:
    """Test connecting to Neo4j."""

    def test_connect_success(self, mock_graph_db):
        """Test successful connection."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver

        driver = connect_neo4j(uri="bolt://localhost:7687", user="neo4j", password="password")

        assert driver == mock_driver
        mock_graph_db.driver.assert_called_once()
        mock_driver.verify_connectivity.assert_called_once()

    def test_connect_with_custom_params(self, mock_graph_db):
        """Test connection with custom parameters."""
        mock_driver = Mock()
        mock_graph_db.driver.return_value = mock_driver

        driver = connect_neo4j(
            uri="neo4j://prod.example.com:7687",
            user="admin",
            password="secret",
            database="production",
            encrypted=True,
            max_retry_time=60,
        )

        assert driver == mock_driver
        call_args = mock_graph_db.driver.call_args
        assert call_args[0][0] == "neo4j://prod.example.com:7687"
        assert call_args[1]["auth"] == ("admin", "secret")
        assert call_args[1]["encrypted"] is True


@patch("grai.core.loader.neo4j_loader.GraphDatabase")
class TestVerifyConnection:
    """Test verifying Neo4j connection."""

    def test_verify_success(self, mock_graph_db):
        """Test successful verification."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_record = {"test": 1}

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.single.return_value = mock_record

        assert verify_connection(mock_driver) is True
        mock_session.run.assert_called_once_with("RETURN 1 AS test")

    def test_verify_failure(self, mock_graph_db):
        """Test verification failure."""
        mock_driver = Mock()
        mock_driver.session.side_effect = Exception("Connection failed")

        assert verify_connection(mock_driver) is False


class TestCloseConnection:
    """Test closing Neo4j connection."""

    def test_close_connection(self):
        """Test closing connection."""
        mock_driver = Mock()
        close_connection(mock_driver)

        mock_driver.close.assert_called_once()

    def test_close_none_driver(self):
        """Test closing None driver doesn't error."""
        close_connection(None)  # Should not raise


@patch("grai.core.loader.neo4j_loader.GraphDatabase")
class TestExecuteCypher:
    """Test executing Cypher statements."""

    def test_execute_single_statement(self, mock_graph_db):
        """Test executing single statement."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_summary = Mock()
        mock_counters = Mock()

        mock_counters.nodes_created = 1
        mock_counters.nodes_deleted = 0
        mock_counters.relationships_created = 0
        mock_counters.relationships_deleted = 0
        mock_counters.properties_set = 2

        mock_summary.counters = mock_counters
        mock_result.consume.return_value = mock_summary

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result

        result = execute_cypher(mock_driver, "CREATE (n:Person {name: 'Alice'});")

        assert result.success is True
        assert result.statements_executed == 1
        assert result.records_affected == 3  # 1 node + 2 properties
        assert result.execution_time > 0
        assert len(result.errors) == 0

    def test_execute_multiple_statements(self, mock_graph_db):
        """Test executing multiple statements."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_summary = Mock()
        mock_counters = Mock()

        mock_counters.nodes_created = 1
        mock_counters.nodes_deleted = 0
        mock_counters.relationships_created = 0
        mock_counters.relationships_deleted = 0
        mock_counters.properties_set = 0

        mock_summary.counters = mock_counters
        mock_result.consume.return_value = mock_summary

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result

        cypher = """
        CREATE (n:Person {name: 'Alice'});
        CREATE (m:Person {name: 'Bob'});
        """

        result = execute_cypher(mock_driver, cypher)

        assert result.success is True
        assert result.statements_executed == 2
        assert mock_session.run.call_count == 2

    def test_execute_with_parameters(self, mock_graph_db):
        """Test executing with parameters."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_summary = Mock()
        mock_counters = Mock()

        mock_counters.nodes_created = 1
        mock_counters.nodes_deleted = 0
        mock_counters.relationships_created = 0
        mock_counters.relationships_deleted = 0
        mock_counters.properties_set = 1

        mock_summary.counters = mock_counters
        mock_result.consume.return_value = mock_summary

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result

        params = {"name": "Alice", "age": 30}
        result = execute_cypher(
            mock_driver, "CREATE (n:Person {name: $name, age: $age});", parameters=params
        )

        assert result.success is True
        mock_session.run.assert_called_once()
        # Check that parameters were passed (they're the second positional arg)
        call_args = mock_session.run.call_args
        assert call_args[0][1] == params


@patch("grai.core.loader.neo4j_loader.GraphDatabase")
class TestExecuteCypherFile:
    """Test executing Cypher from file."""

    def test_execute_file_success(self, mock_graph_db, tmp_path):
        """Test executing file successfully."""
        # Create temp file
        cypher_file = tmp_path / "test.cypher"
        cypher_file.write_text("CREATE (n:Person {name: 'Alice'});")

        # Mock driver
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_summary = Mock()
        mock_counters = Mock()

        mock_counters.nodes_created = 1
        mock_counters.nodes_deleted = 0
        mock_counters.relationships_created = 0
        mock_counters.relationships_deleted = 0
        mock_counters.properties_set = 1

        mock_summary.counters = mock_counters
        mock_result.consume.return_value = mock_summary

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result

        result = execute_cypher_file(mock_driver, cypher_file)

        assert result.success is True
        assert result.statements_executed == 1

    def test_execute_file_not_found(self, mock_graph_db):
        """Test executing non-existent file."""
        mock_driver = Mock()

        with pytest.raises(FileNotFoundError):
            execute_cypher_file(mock_driver, "nonexistent.cypher")


@patch("grai.core.loader.neo4j_loader.GraphDatabase")
@patch("grai.core.loader.neo4j_loader.time.sleep")
class TestExecuteCypherWithRetry:
    """Test executing Cypher with retry logic."""

    def test_retry_success_first_attempt(self, mock_sleep, mock_graph_db):
        """Test successful execution on first attempt."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_summary = Mock()
        mock_counters = Mock()

        mock_counters.nodes_created = 1
        mock_counters.nodes_deleted = 0
        mock_counters.relationships_created = 0
        mock_counters.relationships_deleted = 0
        mock_counters.properties_set = 0

        mock_summary.counters = mock_counters
        mock_result.consume.return_value = mock_summary

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result

        result = execute_cypher_with_retry(mock_driver, "CREATE (n:Person);", max_retries=3)

        assert result.success is True
        mock_sleep.assert_not_called()

    def test_retry_success_after_failures(self, mock_sleep, mock_graph_db):
        """Test successful execution after retries."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        # Mock to fail twice then succeed
        mock_result_fail = Mock()
        mock_result_fail.consume.side_effect = Exception("Transient error")

        mock_result_success = Mock()
        mock_summary = Mock()
        mock_counters = Mock()
        mock_counters.nodes_created = 1
        mock_counters.nodes_deleted = 0
        mock_counters.relationships_created = 0
        mock_counters.relationships_deleted = 0
        mock_counters.properties_set = 0
        mock_summary.counters = mock_counters
        mock_result_success.consume.return_value = mock_summary

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.side_effect = [
            mock_result_fail,  # First attempt fails
            mock_result_fail,  # Second attempt fails
            mock_result_success,  # Third attempt succeeds
        ]

        result = execute_cypher_with_retry(
            mock_driver, "CREATE (n:Person);", max_retries=3, retry_delay=0.1
        )

        assert result.success is True
        assert mock_sleep.call_count == 2  # Slept twice before success


@patch("grai.core.loader.neo4j_loader.GraphDatabase")
class TestGetDatabaseInfo:
    """Test getting database information."""

    def test_get_info_success(self, mock_graph_db):
        """Test getting database info successfully."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        # Mock node count
        mock_node_result = Mock()
        mock_node_result.single.return_value = {"count": 100}

        # Mock relationship count
        mock_rel_result = Mock()
        mock_rel_result.single.return_value = {"count": 50}

        # Mock labels
        mock_labels_result = [
            {"label": "Person"},
            {"label": "Product"},
        ]

        # Mock relationship types
        mock_rel_types_result = [
            {"relationshipType": "KNOWS"},
            {"relationshipType": "PURCHASED"},
        ]

        # Mock constraints and indexes
        mock_constraints_result = []
        mock_indexes_result = []

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.side_effect = [
            mock_node_result,
            mock_rel_result,
            mock_labels_result,
            mock_rel_types_result,
            mock_constraints_result,
            mock_indexes_result,
        ]

        info = get_database_info(mock_driver)

        assert info["node_count"] == 100
        assert info["relationship_count"] == 50
        assert info["labels"] == ["Person", "Product"]
        assert info["relationship_types"] == ["KNOWS", "PURCHASED"]


@patch("grai.core.loader.neo4j_loader.GraphDatabase")
class TestClearDatabase:
    """Test clearing database."""

    def test_clear_without_confirm(self, mock_graph_db):
        """Test clear fails without confirmation."""
        mock_driver = Mock()

        result = clear_database(mock_driver, confirm=False)

        assert result.success is False
        assert len(result.errors) > 0
        assert "confirm=True" in result.errors[0]

    def test_clear_with_confirm(self, mock_graph_db):
        """Test clear succeeds with confirmation."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = Mock()
        mock_summary = Mock()
        mock_counters = Mock()

        mock_counters.nodes_created = 0
        mock_counters.nodes_deleted = 100
        mock_counters.relationships_created = 0
        mock_counters.relationships_deleted = 50
        mock_counters.properties_set = 0

        mock_summary.counters = mock_counters
        mock_result.consume.return_value = mock_summary

        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result

        result = clear_database(mock_driver, confirm=True)

        assert result.success is True
        assert result.records_affected == 150  # 100 nodes + 50 rels

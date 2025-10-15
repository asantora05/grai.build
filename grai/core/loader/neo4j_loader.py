"""
Neo4j Loader - Execute Cypher statements against Neo4j database.

This module provides functionality to connect to Neo4j, execute Cypher queries,
and manage database operations for grai.build projects.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from neo4j import Driver, GraphDatabase, Result, Session
    from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    Driver = None
    Session = None
    Result = None


@dataclass
class Neo4jConnection:
    """
    Neo4j connection configuration.

    Attributes:
        uri: Neo4j connection URI (e.g., bolt://localhost:7687)
        user: Username for authentication
        password: Password for authentication
        database: Database name (default: neo4j)
        encrypted: Whether to use encrypted connection
        max_retry_time: Maximum time to retry connection (seconds)
    """

    uri: str
    user: str
    password: str
    database: str = "neo4j"
    encrypted: bool = False
    max_retry_time: int = 30


@dataclass
class ExecutionResult:
    """
    Result of executing Cypher statements.

    Attributes:
        success: Whether execution was successful
        statements_executed: Number of statements executed
        records_affected: Number of records affected (if available)
        execution_time: Time taken to execute (seconds)
        errors: List of error messages
        warnings: List of warning messages
    """

    success: bool
    statements_executed: int = 0
    records_affected: int = 0
    execution_time: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


def check_neo4j_available():
    """
    Check if neo4j driver is available.

    Raises:
        ImportError: If neo4j driver is not installed.
    """
    if not NEO4J_AVAILABLE:
        raise ImportError("neo4j driver not installed. Install it with: pip install neo4j")


def connect_neo4j(
    uri: str,
    user: str,
    password: str,
    database: str = "neo4j",
    encrypted: bool = False,
    max_retry_time: int = 30,
) -> Driver:
    """
    Connect to Neo4j database.

    Args:
        uri: Neo4j connection URI (e.g., bolt://localhost:7687)
        user: Username for authentication
        password: Password for authentication
        database: Database name (default: neo4j)
        encrypted: Whether to use encrypted connection
        max_retry_time: Maximum time to retry connection (seconds)

    Returns:
        Neo4j driver instance.

    Raises:
        ImportError: If neo4j driver is not installed.
        ServiceUnavailable: If cannot connect to Neo4j.
        AuthError: If authentication fails.

    Example:
        ```python
        driver = connect_neo4j(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        ```
    """
    check_neo4j_available()

    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            encrypted=encrypted,
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=max_retry_time,
        )

        # Verify connectivity
        driver.verify_connectivity()

        return driver

    except AuthError as e:
        raise AuthError(f"Authentication failed: {e}")
    except ServiceUnavailable as e:
        raise ServiceUnavailable(f"Cannot connect to Neo4j at {uri}: {e}")
    except Exception as e:
        raise RuntimeError(f"Error connecting to Neo4j: {e}")


def verify_connection(driver: Driver, database: str = "neo4j") -> bool:
    """
    Verify that connection to Neo4j is working.

    Args:
        driver: Neo4j driver instance.
        database: Database name to test.

    Returns:
        True if connection is working, False otherwise.

    Example:
        ```python
        driver = connect_neo4j(...)
        if verify_connection(driver):
            print("Connected!")
        ```
    """
    check_neo4j_available()

    try:
        with driver.session(database=database) as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()
            return record["test"] == 1
    except Exception:
        return False


def close_connection(driver: Driver) -> None:
    """
    Close Neo4j driver connection.

    Args:
        driver: Neo4j driver instance to close.

    Example:
        ```python
        driver = connect_neo4j(...)
        # ... use driver ...
        close_connection(driver)
        ```
    """
    if driver:
        driver.close()


def split_cypher_statements(cypher: str) -> List[str]:
    """
    Split Cypher script into individual statements.

    Args:
        cypher: Cypher script containing multiple statements.

    Returns:
        List of individual Cypher statements.

    Note:
        This is a simple implementation that splits on semicolons.
        It does not handle semicolons within strings or comments.
    """
    # Remove comments (but not // inside quoted strings)
    lines = []
    for line in cypher.split("\n"):
        # Simple check: if line has quotes, keep it as-is (might contain // in URLs)
        # Otherwise, remove // comments
        if "'" in line or '"' in line:
            # Line might contain URLs or strings, keep it as-is
            lines.append(line)
        else:
            # Remove single-line comments
            if "//" in line:
                line = line[: line.index("//")]
            lines.append(line)

    cypher_no_comments = "\n".join(lines)

    # Split on semicolons and filter empty statements
    statements = [
        stmt.strip()
        for stmt in cypher_no_comments.split(";")
        if stmt.strip() and not stmt.strip().startswith("//")
    ]

    return statements


def execute_cypher(
    driver: Driver,
    cypher: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: str = "neo4j",
) -> ExecutionResult:
    """
    Execute Cypher statement(s) against Neo4j.

    Args:
        driver: Neo4j driver instance.
        cypher: Cypher statement(s) to execute.
        parameters: Optional parameters for the query.
        database: Database name to execute against.

    Returns:
        ExecutionResult with execution details.

    Example:
        ```python
        driver = connect_neo4j(...)
        result = execute_cypher(
            driver,
            "CREATE (n:Person {name: $name}) RETURN n",
            parameters={"name": "Alice"}
        )
        print(f"Success: {result.success}")
        print(f"Statements executed: {result.statements_executed}")
        ```
    """
    check_neo4j_available()

    start_time = time.time()
    result = ExecutionResult(success=False)

    try:
        # Split into individual statements
        statements = split_cypher_statements(cypher)

        with driver.session(database=database) as session:
            for statement in statements:
                try:
                    # Execute statement
                    query_result = session.run(statement, parameters or {})

                    # Consume results to ensure execution
                    summary = query_result.consume()

                    # Track counters
                    counters = summary.counters
                    result.records_affected += (
                        counters.nodes_created
                        + counters.nodes_deleted
                        + counters.relationships_created
                        + counters.relationships_deleted
                        + counters.properties_set
                    )

                    result.statements_executed += 1

                except Neo4jError as e:
                    result.errors.append(f"Error executing statement: {e}")
                    result.success = False
                    return result

            # All statements executed successfully
            result.success = True

    except Exception as e:
        result.errors.append(f"Execution error: {e}")
        result.success = False

    finally:
        result.execution_time = time.time() - start_time

    return result


def execute_cypher_file(
    driver: Driver,
    file_path: Union[str, Path],
    database: str = "neo4j",
    batch_size: Optional[int] = None,
) -> ExecutionResult:
    """
    Execute Cypher statements from a file.

    Args:
        driver: Neo4j driver instance.
        file_path: Path to Cypher file.
        database: Database name to execute against.
        batch_size: Optional batch size for large files.

    Returns:
        ExecutionResult with execution details.

    Raises:
        FileNotFoundError: If file does not exist.

    Example:
        ```python
        driver = connect_neo4j(...)
        result = execute_cypher_file(
            driver,
            "target/neo4j/compiled.cypher"
        )
        print(f"Executed {result.statements_executed} statements")
        print(f"Affected {result.records_affected} records")
        ```
    """
    check_neo4j_available()

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Cypher file not found: {file_path}")

    # Read file
    cypher = file_path.read_text()

    # Execute
    return execute_cypher(driver, cypher, database=database)


def execute_cypher_with_retry(
    driver: Driver,
    cypher: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: str = "neo4j",
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> ExecutionResult:
    """
    Execute Cypher with retry logic for transient failures.

    Args:
        driver: Neo4j driver instance.
        cypher: Cypher statement(s) to execute.
        parameters: Optional parameters for the query.
        database: Database name to execute against.
        max_retries: Maximum number of retries.
        retry_delay: Delay between retries (seconds).

    Returns:
        ExecutionResult with execution details.

    Example:
        ```python
        driver = connect_neo4j(...)
        result = execute_cypher_with_retry(
            driver,
            cypher,
            max_retries=5,
            retry_delay=2.0
        )
        ```
    """
    check_neo4j_available()

    last_result = None

    for attempt in range(max_retries + 1):
        result = execute_cypher(driver, cypher, parameters, database)

        if result.success:
            return result

        last_result = result

        # Don't retry on last attempt
        if attempt < max_retries:
            if result.warnings:
                result.warnings.append(
                    f"Retrying after failure (attempt {attempt + 1}/{max_retries})"
                )
            time.sleep(retry_delay)

    # All retries exhausted
    return last_result


def get_database_info(driver: Driver, database: str = "neo4j") -> Dict[str, Any]:
    """
    Get information about the Neo4j database.

    Args:
        driver: Neo4j driver instance.
        database: Database name.

    Returns:
        Dictionary with database information.

    Example:
        ```python
        driver = connect_neo4j(...)
        info = get_database_info(driver)
        print(f"Node count: {info['node_count']}")
        print(f"Relationship count: {info['relationship_count']}")
        ```
    """
    check_neo4j_available()

    info = {
        "node_count": 0,
        "relationship_count": 0,
        "labels": [],
        "relationship_types": [],
        "constraints": [],
        "indexes": [],
    }

    try:
        with driver.session(database=database) as session:
            # Get node count
            result = session.run("MATCH (n) RETURN count(n) AS count")
            info["node_count"] = result.single()["count"]

            # Get relationship count
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            info["relationship_count"] = result.single()["count"]

            # Get labels
            result = session.run("CALL db.labels()")
            info["labels"] = [record["label"] for record in result]

            # Get relationship types
            result = session.run("CALL db.relationshipTypes()")
            info["relationship_types"] = [record["relationshipType"] for record in result]

            # Get constraints
            result = session.run("SHOW CONSTRAINTS")
            info["constraints"] = [dict(record) for record in result]

            # Get indexes
            result = session.run("SHOW INDEXES")
            info["indexes"] = [dict(record) for record in result]

    except Exception as e:
        info["error"] = str(e)

    return info


def clear_database(
    driver: Driver,
    database: str = "neo4j",
    confirm: bool = False,
) -> ExecutionResult:
    """
    Clear all nodes and relationships from database.

    WARNING: This will delete all data in the database!

    Args:
        driver: Neo4j driver instance.
        database: Database name.
        confirm: Must be True to actually delete data.

    Returns:
        ExecutionResult with deletion details.

    Example:
        ```python
        driver = connect_neo4j(...)
        # Confirm deletion by passing confirm=True
        result = clear_database(driver, confirm=True)
        print(f"Deleted {result.records_affected} records")
        ```
    """
    check_neo4j_available()

    if not confirm:
        return ExecutionResult(success=False, errors=["Must pass confirm=True to delete data"])

    cypher = """
    MATCH (n)
    DETACH DELETE n;
    """

    return execute_cypher(driver, cypher, database=database)

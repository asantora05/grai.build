"""Real Neo4j integration tests."""

import os
import textwrap
import uuid
from datetime import datetime

import pytest

from grai.core.loader import (
    close_connection,
    connect_neo4j,
    execute_cypher,
    execute_cypher_file,
    verify_connection,
)
from grai.core.migrations.executor import MigrationExecutor


@pytest.fixture(scope="session")
def neo4j_env():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    if not uri or not user or not password:
        pytest.skip("NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD not set")
    return uri, user, password, database


@pytest.fixture(scope="session")
def neo4j_driver(neo4j_env):
    uri, user, password, _ = neo4j_env
    driver = connect_neo4j(uri=uri, user=user, password=password)
    try:
        yield driver
    finally:
        close_connection(driver)


def _cleanup(driver, database: str, run_id: str) -> None:
    with driver.session(database=database) as session:
        session.run("MATCH (n {run_id: $run_id}) DETACH DELETE n", run_id=run_id)


@pytest.mark.neo4j_integration
def test_verify_connection(neo4j_driver, neo4j_env):
    _, _, _, database = neo4j_env
    assert verify_connection(neo4j_driver, database=database) is True


@pytest.mark.neo4j_integration
def test_execute_cypher_creates_node(neo4j_driver, neo4j_env):
    _, _, _, database = neo4j_env
    run_id = uuid.uuid4().hex

    try:
        result = execute_cypher(
            neo4j_driver,
            "CREATE (n:GraiTest {run_id: $run_id})",
            parameters={"run_id": run_id},
            database=database,
        )
        assert result.success is True
        assert result.statements_executed >= 1

        with neo4j_driver.session(database=database) as session:
            record = session.run(
                "MATCH (n:GraiTest {run_id: $run_id}) RETURN count(n) AS c",
                run_id=run_id,
            ).single()
            assert record is not None
            assert record["c"] == 1
    finally:
        _cleanup(neo4j_driver, database, run_id)


@pytest.mark.neo4j_integration
def test_execute_cypher_file_creates_graph(neo4j_driver, neo4j_env, tmp_path):
    _, _, _, database = neo4j_env
    run_id = uuid.uuid4().hex
    cypher_file = tmp_path / "graph.cypher"

    cypher_file.write_text(
        "\n".join(
            [
                "// Create two nodes and a relationship",
                f"CREATE (a:GraiTestFile {{run_id: '{run_id}', name: 'a'}});",
                f"CREATE (b:GraiTestFile {{run_id: '{run_id}', name: 'b'}});",
                f"MATCH (a:GraiTestFile {{run_id: '{run_id}', name: 'a'}})",
                f"MATCH (b:GraiTestFile {{run_id: '{run_id}', name: 'b'}})",
                "MERGE (a)-[:LINKED]->(b);",
            ]
        )
    )

    try:
        result = execute_cypher_file(neo4j_driver, cypher_file, database=database, batch_size=None)
        assert result.success is True
        assert result.statements_executed >= 3

        with neo4j_driver.session(database=database) as session:
            record = session.run(
                "MATCH (a:GraiTestFile {run_id: $run_id})-[r:LINKED]->(b:GraiTestFile {run_id: $run_id}) "
                "RETURN count(r) AS c",
                run_id=run_id,
            ).single()
            assert record is not None
            assert record["c"] == 1
    finally:
        _cleanup(neo4j_driver, database, run_id)


@pytest.mark.neo4j_integration
def test_migration_apply_and_rollback(neo4j_driver, neo4j_env, tmp_path):
    _, _, _, database = neo4j_env
    run_id = uuid.uuid4().hex
    version = f"20990101_{run_id[:6]}"
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()

    migration_file = migrations_dir / f"{version}_neo4j_test.yml"
    migration_file.write_text(
        textwrap.dedent(
            f"""
            version: "{version}"
            description: "neo4j integration test"
            author: "test"
            timestamp: "{datetime.utcnow().isoformat()}"
            checksum: "{run_id}"
            changes:
              entities: []
              relations: []
            up:
              - "CREATE (n:GraiMigrationTest {{run_id: '{run_id}'}})"
            down:
              - "MATCH (n:GraiMigrationTest {{run_id: '{run_id}'}}) DETACH DELETE n"
            """
        ).lstrip()
    )

    executor = MigrationExecutor(neo4j_driver, tmp_path)

    try:
        migration = executor._load_migration(version)
        assert migration is not None

        history = executor.apply_migration(migration)
        assert history.version == version

        with neo4j_driver.session(database=database) as session:
            record = session.run(
                "MATCH (n:GraiMigrationTest {run_id: $run_id}) RETURN count(n) AS c",
                run_id=run_id,
            ).single()
            assert record is not None
            assert record["c"] == 1

        history = executor.rollback_migration(version)
        assert history.version == version

        with neo4j_driver.session(database=database) as session:
            record = session.run(
                "MATCH (n:GraiMigrationTest {run_id: $run_id}) RETURN count(n) AS c",
                run_id=run_id,
            ).single()
            assert record is not None
            assert record["c"] == 0
    finally:
        with neo4j_driver.session(database=database) as session:
            session.run(
                "MATCH (m:__GraiMigration {version: $version}) DETACH DELETE m",
                version=version,
            )
        _cleanup(neo4j_driver, database, run_id)

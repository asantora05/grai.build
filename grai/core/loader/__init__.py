"""Loader module for executing Cypher against Neo4j and loading# PostgreSQL loader (requires psycopg2)
try:
    from grai.core.loader.postgres_loader import (
        PostgresConnection,  # noqa: F401
        PostgresExtractor,  # noqa: F401
        connect_postgres,  # noqa: F401
        load_entity_from_postgres,  # noqa: F401
        load_relation_from_postgres,  # noqa: F401
    )

    _optional_exports.extend(
        [
            "PostgresConnection",
            "PostgresExtractor",
            "connect_postgres",
            "load_entity_from_postgres",
            "load_relation_from_postgres",
        ]
    )
except ImportError:
    passes."""

from grai.core.loader.neo4j_loader import (
    Neo4jConnection,
    close_connection,
    connect_neo4j,
    execute_cypher,
    execute_cypher_file,
    get_database_info,
    verify_connection,
)

# Optional data warehouse loaders
_optional_exports = []

# BigQuery loader (requires google-cloud-bigquery)
try:
    from grai.core.loader.bigquery_loader import (  # noqa: F401
        BigQueryConnection,
        BigQueryExtractor,
        LoadResult,
        connect_bigquery,
        extract_data,
        load_entity_from_bigquery,
        load_relation_from_bigquery,
    )

    _optional_exports.extend(
        [
            "BigQueryConnection",
            "BigQueryExtractor",
            "LoadResult",
            "connect_bigquery",
            "extract_data",
            "load_entity_from_bigquery",
            "load_relation_from_bigquery",
        ]
    )
except ImportError:
    pass

# PostgreSQL loader (requires psycopg2)
try:
    from grai.core.loader.postgres_loader import (  # noqa: F401
        PostgresConnection,
        PostgresExtractor,
        connect_postgres,
        load_entity_from_postgres,
        load_relation_from_postgres,
    )

    _optional_exports.extend(
        [
            "PostgresConnection",
            "PostgresExtractor",
            "connect_postgres",
            "load_entity_from_postgres",
            "load_relation_from_postgres",
        ]
    )
except ImportError:
    pass

# PostgreSQL loader (requires psycopg2)
try:
    from grai.core.loader.postgres_loader import (  # noqa: F401
        PostgresConnection,  # noqa: F401
        PostgresExtractor,  # noqa: F401
        connect_postgres,  # noqa: F401
        load_entity_from_postgres,  # noqa: F401
        load_relation_from_postgres,  # noqa: F401
    )

    _optional_exports.extend(
        [
            "PostgresConnection",
            "PostgresExtractor",
            "connect_postgres",
            "load_entity_from_postgres",
            "load_relation_from_postgres",
        ]
    )
except ImportError:
    pass

# Build final __all__ list
__all__ = [
    "Neo4jConnection",
    "connect_neo4j",
    "execute_cypher",
    "execute_cypher_file",
    "verify_connection",
    "close_connection",
    "get_database_info",
] + _optional_exports

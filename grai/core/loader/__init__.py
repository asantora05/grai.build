"""Loader module for executing Cypher against Neo4j and loading data from warehouses."""

from grai.core.loader.neo4j_loader import (
    Neo4jConnection,
    close_connection,
    connect_neo4j,
    execute_cypher,
    execute_cypher_file,
    get_database_info,
    verify_connection,
)

# BigQuery loader is optional (requires google-cloud-bigquery)
try:
    from grai.core.loader.bigquery_loader import (
        BigQueryConnection,
        BigQueryExtractor,
        LoadResult,
        connect_bigquery,
        extract_data,
        load_entity_from_bigquery,
        load_relation_from_bigquery,
    )

    __all__ = [
        "Neo4jConnection",
        "connect_neo4j",
        "execute_cypher",
        "execute_cypher_file",
        "verify_connection",
        "close_connection",
        "get_database_info",
        "BigQueryConnection",
        "BigQueryExtractor",
        "LoadResult",
        "connect_bigquery",
        "extract_data",
        "load_entity_from_bigquery",
        "load_relation_from_bigquery",
    ]
except ImportError:
    # BigQuery not available
    __all__ = [
        "Neo4jConnection",
        "connect_neo4j",
        "execute_cypher",
        "execute_cypher_file",
        "verify_connection",
        "close_connection",
        "get_database_info",
    ]

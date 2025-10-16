"""
dbt integration for grai.build.

This module provides functionality for importing dbt models and generating
grai.build entity and relation definitions from dbt manifest files.
"""

from grai.core.dbt.manifest_parser import (
    DbtManifestParser,
    parse_dbt_manifest,
    parse_dbt_manifest_file,
    write_entities_to_yaml,
    write_relations_to_yaml,
)

__all__ = [
    "parse_dbt_manifest",
    "parse_dbt_manifest_file",
    "write_entities_to_yaml",
    "write_relations_to_yaml",
    "DbtManifestParser",
]

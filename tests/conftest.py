"""Pytest configuration for integration tests."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip Neo4j integration tests unless explicitly selected via -m."""
    markexpr = config.option.markexpr or ""
    if "neo4j_integration" in markexpr:
        return

    skip_marker = pytest.mark.skip(reason="requires -m neo4j_integration")
    for item in items:
        if "neo4j_integration" in item.keywords:
            item.add_marker(skip_marker)

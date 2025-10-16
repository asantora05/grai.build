"""
Tests for dbt manifest parser.
"""

import json
from pathlib import Path

import pytest

from grai.core.dbt.manifest_parser import (
    DbtManifestParser,
    parse_dbt_manifest,
    parse_dbt_manifest_file,
    write_entities_to_yaml,
)
from grai.core.models import Entity, PropertyType, SourceType


@pytest.fixture
def sample_manifest():
    """Sample dbt manifest data for testing."""
    return {
        "metadata": {
            "dbt_version": "1.7.0",
            "generated_at": "2025-01-01T00:00:00Z",
        },
        "nodes": {
            "model.ecommerce.fct_orders": {
                "resource_type": "model",
                "unique_id": "model.ecommerce.fct_orders",
                "name": "fct_orders",
                "alias": "fct_orders",
                "database": "analytics",
                "schema": "public",
                "package_name": "ecommerce",
                "original_file_path": "models/marts/fct_orders.sql",
                "description": "Fact table for orders",
                "config": {
                    "materialized": "table",
                },
                "columns": {
                    "order_id": {
                        "name": "order_id",
                        "data_type": "integer",
                        "description": "Primary key for orders",
                        "tests": ["unique", "not_null"],
                    },
                    "customer_id": {
                        "name": "customer_id",
                        "data_type": "integer",
                        "description": "Foreign key to customer",
                    },
                    "order_total": {
                        "name": "order_total",
                        "data_type": "decimal",
                        "description": "Total order amount",
                    },
                    "order_date": {
                        "name": "order_date",
                        "data_type": "date",
                        "description": "Date order was placed",
                    },
                },
            },
            "model.ecommerce.dim_customers": {
                "resource_type": "model",
                "unique_id": "model.ecommerce.dim_customers",
                "name": "dim_customers",
                "alias": "dim_customers",
                "database": "analytics",
                "schema": "public",
                "package_name": "ecommerce",
                "original_file_path": "models/marts/dim_customers.sql",
                "description": "Customer dimension table",
                "config": {
                    "materialized": "table",
                },
                "columns": {
                    "customer_id": {
                        "name": "customer_id",
                        "data_type": "integer",
                        "description": "Customer ID",
                        "tests": ["unique", "not_null"],
                    },
                    "customer_name": {
                        "name": "customer_name",
                        "data_type": "varchar",
                        "description": "Customer full name",
                    },
                    "email": {
                        "name": "email",
                        "data_type": "varchar",
                        "description": "Customer email",
                    },
                },
            },
        },
    }


class TestDbtManifestParser:
    """Tests for DbtManifestParser class."""

    def test_parser_initialization(self, sample_manifest):
        """Test parser initializes correctly with manifest data."""
        parser = DbtManifestParser(sample_manifest)

        assert len(parser.models) == 2
        assert "model.ecommerce.fct_orders" in parser.models
        assert "model.ecommerce.dim_customers" in parser.models

    def test_parse_models(self, sample_manifest):
        """Test parsing all models."""
        parser = DbtManifestParser(sample_manifest)
        entities = parser.parse_models()

        assert len(entities) == 2
        assert all(isinstance(e, Entity) for e in entities)

        # Check entity names
        entity_names = {e.entity for e in entities}
        assert entity_names == {"fct_orders", "dim_customers"}

    def test_parse_models_with_include_filter(self, sample_manifest):
        """Test parsing models with include filter."""
        parser = DbtManifestParser(sample_manifest)
        entities = parser.parse_models(include_patterns=["fct_"])

        assert len(entities) == 1
        assert entities[0].entity == "fct_orders"

    def test_parse_models_with_exclude_filter(self, sample_manifest):
        """Test parsing models with exclude filter."""
        parser = DbtManifestParser(sample_manifest)
        entities = parser.parse_models(exclude_patterns=["dim_"])

        assert len(entities) == 1
        assert entities[0].entity == "fct_orders"

    def test_model_to_entity(self, sample_manifest):
        """Test converting a dbt model to an entity."""
        parser = DbtManifestParser(sample_manifest)
        model = sample_manifest["nodes"]["model.ecommerce.fct_orders"]
        entity = parser._model_to_entity(model)

        assert entity is not None
        assert entity.entity == "fct_orders"
        assert entity.description == "Fact table for orders"

        # Check source config
        assert entity.source.name == "public.fct_orders"
        assert entity.source.type == SourceType.TABLE
        assert entity.source.database == "analytics"
        assert entity.source.db_schema == "public"
        assert entity.source.metadata["dbt_model"] == "fct_orders"
        assert entity.source.metadata["materialization"] == "table"

        # Check keys (inferred from tests)
        assert "order_id" in entity.keys

        # Check properties
        assert len(entity.properties) == 4
        prop_names = {p.name for p in entity.properties}
        assert prop_names == {"order_id", "customer_id", "order_total", "order_date"}

    def test_parse_columns(self, sample_manifest):
        """Test parsing columns into properties."""
        parser = DbtManifestParser(sample_manifest)
        columns = sample_manifest["nodes"]["model.ecommerce.fct_orders"]["columns"]
        properties = parser._parse_columns(columns)

        assert len(properties) == 4

        # Check order_id property
        order_id_prop = next(p for p in properties if p.name == "order_id")
        assert order_id_prop.type == PropertyType.INTEGER
        assert order_id_prop.description == "Primary key for orders"

        # Check order_total property (decimal -> float)
        order_total_prop = next(p for p in properties if p.name == "order_total")
        assert order_total_prop.type == PropertyType.FLOAT

        # Check order_date property
        order_date_prop = next(p for p in properties if p.name == "order_date")
        assert order_date_prop.type == PropertyType.DATE

    def test_type_mapping(self, sample_manifest):
        """Test data type mapping."""
        parser = DbtManifestParser(sample_manifest)

        assert parser._map_type("integer") == PropertyType.INTEGER
        assert parser._map_type("varchar") == PropertyType.STRING
        assert parser._map_type("decimal") == PropertyType.FLOAT
        assert parser._map_type("boolean") == PropertyType.BOOLEAN
        assert parser._map_type("date") == PropertyType.DATE
        assert parser._map_type("timestamp") == PropertyType.DATETIME
        assert parser._map_type("json") == PropertyType.JSON

        # Test unknown type defaults to string
        assert parser._map_type("custom_type") == PropertyType.STRING

    def test_infer_keys(self, sample_manifest):
        """Test inferring keys from dbt tests."""
        parser = DbtManifestParser(sample_manifest)
        model = sample_manifest["nodes"]["model.ecommerce.fct_orders"]
        keys = parser._infer_keys(model)

        # order_id has unique test
        assert "order_id" in keys

        # customer_id doesn't have unique test
        assert "customer_id" not in keys

    def test_infer_keys_from_dict_tests(self, sample_manifest):
        """Test inferring keys when tests are dicts."""
        # Modify sample to use dict-style tests
        model = sample_manifest["nodes"]["model.ecommerce.dim_customers"].copy()
        model["columns"]["customer_id"]["tests"] = [
            {"unique": {}},
            {"not_null": {}},
        ]

        parser = DbtManifestParser(sample_manifest)
        keys = parser._infer_keys(model)

        assert "customer_id" in keys


def test_parse_dbt_manifest(sample_manifest):
    """Test parse_dbt_manifest function."""
    entities = parse_dbt_manifest(sample_manifest)

    assert len(entities) == 2
    assert all(isinstance(e, Entity) for e in entities)


def test_parse_dbt_manifest_file(tmp_path, sample_manifest):
    """Test parsing manifest from file."""
    # Create temporary manifest file
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(sample_manifest))

    entities = parse_dbt_manifest_file(manifest_path)

    assert len(entities) == 2
    assert all(isinstance(e, Entity) for e in entities)


def test_parse_dbt_manifest_file_not_found():
    """Test error when manifest file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        parse_dbt_manifest_file(Path("nonexistent.json"))


def test_parse_dbt_manifest_file_with_filters(tmp_path, sample_manifest):
    """Test parsing manifest file with filters."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(sample_manifest))

    # Test include filter
    entities = parse_dbt_manifest_file(
        manifest_path,
        include_patterns=["fct_"],
    )
    assert len(entities) == 1
    assert entities[0].entity == "fct_orders"

    # Test exclude filter
    entities = parse_dbt_manifest_file(
        manifest_path,
        exclude_patterns=["fct_"],
    )
    assert len(entities) == 1
    assert entities[0].entity == "dim_customers"


def test_write_entities_to_yaml(tmp_path, sample_manifest):
    """Test writing entities to YAML files."""
    # Parse entities
    entities = parse_dbt_manifest(sample_manifest)

    # Write to YAML
    output_dir = tmp_path / "entities"
    created_files = write_entities_to_yaml(entities, output_dir)

    assert len(created_files) == 2
    assert all(f.exists() for f in created_files)

    # Check file names
    filenames = {f.name for f in created_files}
    assert filenames == {"fct_orders.yml", "dim_customers.yml"}

    # Verify file content (check one file)
    fct_orders_file = next(f for f in created_files if f.name == "fct_orders.yml")
    content = fct_orders_file.read_text()

    assert "entity: fct_orders" in content
    assert "order_id" in content
    assert "customer_id" in content


def test_write_entities_to_yaml_overwrite_protection(tmp_path, sample_manifest):
    """Test that existing files are not overwritten without force flag."""
    entities = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    # First write should succeed
    write_entities_to_yaml(entities, output_dir)

    # Second write without overwrite should fail
    with pytest.raises(FileExistsError):
        write_entities_to_yaml(entities, output_dir, overwrite=False)


def test_write_entities_to_yaml_with_overwrite(tmp_path, sample_manifest):
    """Test overwriting existing files with overwrite flag."""
    entities = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    # First write
    write_entities_to_yaml(entities, output_dir)

    # Second write with overwrite should succeed
    created_files = write_entities_to_yaml(entities, output_dir, overwrite=True)

    assert len(created_files) == 2
    assert all(f.exists() for f in created_files)


def test_entity_with_description(tmp_path, sample_manifest):
    """Test that entity descriptions are preserved."""
    entities = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    write_entities_to_yaml(entities, output_dir)

    # Check that description is in the YAML
    fct_orders_file = output_dir / "fct_orders.yml"
    content = fct_orders_file.read_text()

    assert "description: Fact table for orders" in content


def test_property_with_description(tmp_path, sample_manifest):
    """Test that property descriptions are preserved."""
    entities = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    write_entities_to_yaml(entities, output_dir)

    # Check that property description is in the YAML
    fct_orders_file = output_dir / "fct_orders.yml"
    content = fct_orders_file.read_text()

    assert "Primary key for orders" in content

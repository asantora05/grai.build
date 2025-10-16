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
        entities, relations = parser.parse_models()

        assert len(entities) == 2
        assert all(isinstance(e, Entity) for e in entities)

        # Check entity names
        entity_names = {e.entity for e in entities}
        assert entity_names == {"fct_orders", "dim_customers"}

    def test_parse_models_with_include_filter(self, sample_manifest):
        """Test parsing models with include filter."""
        parser = DbtManifestParser(sample_manifest)
        entities, relations = parser.parse_models(include_patterns=["fct_"])

        assert len(entities) == 1
        assert entities[0].entity == "fct_orders"

    def test_parse_models_with_exclude_filter(self, sample_manifest):
        """Test parsing models with exclude filter."""
        parser = DbtManifestParser(sample_manifest)
        entities, relations = parser.parse_models(exclude_patterns=["dim_"])

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
    entities, relations = parse_dbt_manifest(sample_manifest)

    assert len(entities) == 2
    assert all(isinstance(e, Entity) for e in entities)


def test_parse_dbt_manifest_file(tmp_path, sample_manifest):
    """Test parsing manifest from file."""
    # Create temporary manifest file
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(sample_manifest))

    entities, relations = parse_dbt_manifest_file(manifest_path)

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
    entities, relations = parse_dbt_manifest_file(
        manifest_path,
        include_patterns=["fct_"],
    )
    assert len(entities) == 1
    assert entities[0].entity == "fct_orders"

    # Test exclude filter
    entities, relations = parse_dbt_manifest_file(
        manifest_path,
        exclude_patterns=["fct_"],
    )
    assert len(entities) == 1
    assert entities[0].entity == "dim_customers"


def test_write_entities_to_yaml(tmp_path, sample_manifest):
    """Test writing entities to YAML files."""
    # Parse entities
    entities, relations = parse_dbt_manifest(sample_manifest)

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
    entities, relations = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    # First write should succeed
    write_entities_to_yaml(entities, output_dir)

    # Second write without overwrite should fail
    with pytest.raises(FileExistsError):
        write_entities_to_yaml(entities, output_dir, overwrite=False)


def test_write_entities_to_yaml_with_overwrite(tmp_path, sample_manifest):
    """Test overwriting existing files with overwrite flag."""
    entities, relations = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    # First write
    write_entities_to_yaml(entities, output_dir)

    # Second write with overwrite should succeed
    created_files = write_entities_to_yaml(entities, output_dir, overwrite=True)

    assert len(created_files) == 2
    assert all(f.exists() for f in created_files)


def test_entity_with_description(tmp_path, sample_manifest):
    """Test that entity descriptions are preserved."""
    entities, relations = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    write_entities_to_yaml(entities, output_dir)

    # Check that description is in the YAML
    fct_orders_file = output_dir / "fct_orders.yml"
    content = fct_orders_file.read_text()

    assert "description: Fact table for orders" in content


def test_property_with_description(tmp_path, sample_manifest):
    """Test that property descriptions are preserved."""
    entities, relations = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    write_entities_to_yaml(entities, output_dir)

    # Check that property description is in the YAML
    fct_orders_file = output_dir / "fct_orders.yml"
    content = fct_orders_file.read_text()

    assert "Primary key for orders" in content


def test_parse_columns_with_none_data_type():
    """Test parsing columns when data_type is None."""
    # Create a manifest with a model that has columns without data types
    manifest = {
        "nodes": {
            "model.test.airports": {
                "resource_type": "model",
                "unique_id": "model.test.airports",
                "name": "airports",
                "alias": "airports",
                "database": "test_db",
                "schema": "public",
                "package_name": "test",
                "original_file_path": "models/airports.sql",
                "description": "Airport reference data",
                "config": {
                    "materialized": "table",
                },
                "columns": {
                    "airport_code": {
                        "name": "airport_code",
                        "data_type": None,  # No data type specified
                        "description": "IATA airport code",
                        "tests": ["unique"],  # Add unique test to make it a key
                    },
                    "airport_name": {
                        "name": "airport_name",
                        # data_type key missing entirely
                        "description": "Full airport name",
                    },
                    "city": {
                        "name": "city",
                        "data_type": "varchar",
                        "description": "City name",
                    },
                },
            },
        },
    }

    parser = DbtManifestParser(manifest)
    entities, relations = parser.parse_models()

    assert len(entities) == 1
    entity = entities[0]

    # Check that all columns were parsed
    assert len(entity.properties) == 3

    # Check that columns with None data_type default to string
    airport_code_prop = next(p for p in entity.properties if p.name == "airport_code")
    assert airport_code_prop.type == PropertyType.STRING
    assert airport_code_prop.description == "IATA airport code"

    airport_name_prop = next(p for p in entity.properties if p.name == "airport_name")
    assert airport_name_prop.type == PropertyType.STRING
    assert airport_name_prop.description == "Full airport name"

    # Check that column with explicit data_type still works
    city_prop = next(p for p in entity.properties if p.name == "city")
    assert city_prop.type == PropertyType.STRING
    assert city_prop.description == "City name"

    # Verify that the key was inferred correctly
    assert "airport_code" in entity.keys


def test_parse_columns_with_empty_data_type():
    """Test parsing columns when data_type is an empty string."""
    manifest = {
        "nodes": {
            "model.test.test_model": {
                "resource_type": "model",
                "unique_id": "model.test.test_model",
                "name": "test_model",
                "alias": "test_model",
                "database": "test_db",
                "schema": "public",
                "package_name": "test",
                "original_file_path": "models/test_model.sql",
                "description": "Test model",
                "config": {},
                "columns": {
                    "col1": {
                        "name": "col1",
                        "data_type": "",  # Empty string
                        "description": "Column 1",
                        "tests": ["unique"],  # Add unique test to make it a key
                    },
                },
            },
        },
    }

    parser = DbtManifestParser(manifest)
    entities, relations = parser.parse_models()

    assert len(entities) == 1
    entity = entities[0]
    assert len(entity.properties) == 1

    # Empty string should be mapped appropriately
    col1_prop = entity.properties[0]
    assert col1_prop.type == PropertyType.STRING
    assert col1_prop.name == "col1"
    assert "col1" in entity.keys


def test_infer_keys_fallback_to_first_column():
    """Test that first column is used as key when no unique tests are found."""
    manifest = {
        "nodes": {
            "model.test.no_keys_model": {
                "resource_type": "model",
                "unique_id": "model.test.no_keys_model",
                "name": "no_keys_model",
                "alias": "no_keys_model",
                "database": "test_db",
                "schema": "public",
                "package_name": "test",
                "original_file_path": "models/no_keys_model.sql",
                "description": "Model without unique tests",
                "config": {},
                "columns": {
                    "id": {
                        "name": "id",
                        "data_type": "integer",
                        "description": "ID column (no unique test)",
                    },
                    "name": {
                        "name": "name",
                        "data_type": "varchar",
                        "description": "Name column",
                    },
                    "created_at": {
                        "name": "created_at",
                        "data_type": "timestamp",
                        "description": "Created timestamp",
                    },
                },
            },
        },
    }

    parser = DbtManifestParser(manifest)
    entities, relations = parser.parse_models()

    assert len(entities) == 1
    entity = entities[0]

    # Should have 3 properties
    assert len(entity.properties) == 3

    # First column should be used as fallback key
    assert len(entity.keys) == 1
    assert entity.keys[0] == "id"  # First column in the dict


def test_infer_keys_prefers_unique_tests_over_fallback():
    """Test that unique tests are preferred over first column fallback."""
    manifest = {
        "nodes": {
            "model.test.with_unique_test": {
                "resource_type": "model",
                "unique_id": "model.test.with_unique_test",
                "name": "with_unique_test",
                "alias": "with_unique_test",
                "database": "test_db",
                "schema": "public",
                "package_name": "test",
                "original_file_path": "models/with_unique_test.sql",
                "description": "Model with unique test on second column",
                "config": {},
                "columns": {
                    "name": {
                        "name": "name",
                        "data_type": "varchar",
                        "description": "Name (first column, no test)",
                    },
                    "email": {
                        "name": "email",
                        "data_type": "varchar",
                        "description": "Email (has unique test)",
                        "tests": ["unique"],
                    },
                },
            },
        },
    }

    parser = DbtManifestParser(manifest)
    entities, relations = parser.parse_models()

    assert len(entities) == 1
    entity = entities[0]

    # Should use the column with unique test, not the first column
    assert len(entity.keys) == 1
    assert entity.keys[0] == "email"  # Column with unique test, not first column


def test_write_entities_yaml_serializes_source_type_correctly(tmp_path, sample_manifest):
    """Test that SourceType enum is serialized as string, not Python object."""
    entities, relations = parse_dbt_manifest(sample_manifest)
    output_dir = tmp_path / "entities"

    created_files = write_entities_to_yaml(entities, output_dir)

    # Read back one of the files
    fct_orders_file = next(f for f in created_files if f.name == "fct_orders.yml")
    content = fct_orders_file.read_text()

    # Should NOT contain Python object notation
    assert "!!python/object/apply" not in content
    assert "SourceType" not in content

    # Should contain plain string type value
    assert "type: table" in content or "type: 'table'" in content

    # Verify the YAML can be loaded back
    import yaml

    with open(fct_orders_file) as f:
        loaded_data = yaml.safe_load(f)

    # Check that source.type is a plain string
    assert isinstance(loaded_data["source"]["type"], str)
    assert loaded_data["source"]["type"] == "table"


def test_parse_relation_from_meta():
    """Test parsing a relation from dbt meta field."""
    manifest = {
        "nodes": {
            "model.ecommerce.orders": {
                "resource_type": "model",
                "unique_id": "model.ecommerce.orders",
                "name": "orders",
                "alias": "orders",
                "database": "analytics",
                "schema": "public",
                "package_name": "ecommerce",
                "original_file_path": "models/orders.sql",
                "description": "Order transactions linking customers to products",
                "config": {"materialized": "table"},
                "meta": {
                    "grai": {
                        "type": "relation",
                        "relation_name": "PURCHASED",
                        "from_entity": "customer",
                        "from_key": "customer_id",
                        "to_entity": "product",
                        "to_key": "product_id",
                    }
                },
                "columns": {
                    "customer_id": {
                        "name": "customer_id",
                        "data_type": "integer",
                        "description": "Customer ID",
                    },
                    "product_id": {
                        "name": "product_id",
                        "data_type": "integer",
                        "description": "Product ID",
                    },
                    "order_date": {
                        "name": "order_date",
                        "data_type": "date",
                        "description": "Order date",
                    },
                    "quantity": {
                        "name": "quantity",
                        "data_type": "integer",
                        "description": "Quantity ordered",
                    },
                    "total_amount": {
                        "name": "total_amount",
                        "data_type": "decimal",
                        "description": "Total amount",
                    },
                },
            },
        },
    }

    parser = DbtManifestParser(manifest)
    entities, relations = parser.parse_models()

    # Should parse as relation, not entity
    assert len(entities) == 0
    assert len(relations) == 1

    relation = relations[0]
    assert relation.relation == "PURCHASED"
    assert relation.from_entity == "customer"
    assert relation.to_entity == "product"
    assert relation.mappings.from_key == "customer_id"
    assert relation.mappings.to_key == "product_id"

    # Properties should exclude the foreign keys
    assert len(relation.properties) == 3
    prop_names = {p.name for p in relation.properties}
    assert prop_names == {"order_date", "quantity", "total_amount"}
    assert "customer_id" not in prop_names
    assert "product_id" not in prop_names


def test_parse_relation_from_meta_missing_fields():
    """Test that relations with missing meta fields are skipped."""
    manifest = {
        "nodes": {
            "model.test.incomplete_relation": {
                "resource_type": "model",
                "unique_id": "model.test.incomplete_relation",
                "name": "incomplete_relation",
                "alias": "incomplete_relation",
                "database": "test_db",
                "schema": "public",
                "package_name": "test",
                "original_file_path": "models/incomplete.sql",
                "description": "Incomplete relation",
                "config": {},
                "meta": {
                    "grai": {
                        "type": "relation",
                        "relation_name": "INCOMPLETE",
                        # Missing from_entity, from_key, to_entity, to_key
                    }
                },
                "columns": {
                    "id": {
                        "name": "id",
                        "data_type": "integer",
                        "tests": ["unique"],
                    },
                },
            },
        },
    }

    parser = DbtManifestParser(manifest)
    entities, relations = parser.parse_models()

    # Should be skipped, not parsed as entity or relation
    assert len(entities) == 0
    assert len(relations) == 0

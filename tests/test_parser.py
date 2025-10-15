"""Tests for the YAML parser."""

import pytest

from grai.core.parser import (
    ParserError,
    ValidationParserError,
    YAMLParseError,
    load_entities_from_directory,
    load_project,
    load_project_manifest,
    load_relations_from_directory,
    parse_entity_file,
    parse_relation_file,
)


class TestParseEntityFile:
    """Test parsing entity files."""

    def test_parse_valid_entity_file(self, tmp_path):
        """Test parsing a valid entity YAML file."""
        entity_file = tmp_path / "customer.yml"
        entity_file.write_text(
            """
entity: customer
source: analytics.customers
keys:
  - customer_id
properties:
  - name: customer_id
    type: string
    required: true
  - name: name
    type: string
description: Customer entity
"""
        )

        entity = parse_entity_file(entity_file)
        assert entity.entity == "customer"
        assert entity.get_source_name() == "analytics.customers"
        # Verify it's a SourceConfig with inferred type
        source_config = entity.get_source_config()
        assert source_config.name == "analytics.customers"
        assert source_config.type.value == "table"  # Should infer from schema.table pattern
        assert entity.keys == ["customer_id"]
        assert len(entity.properties) == 2
        assert entity.description == "Customer entity"

    def test_parse_entity_file_not_found(self):
        """Test parsing a non-existent file."""
        with pytest.raises(YAMLParseError, match="File not found"):
            parse_entity_file("/nonexistent/file.yml")

    def test_parse_entity_invalid_yaml(self, tmp_path):
        """Test parsing invalid YAML syntax."""
        entity_file = tmp_path / "bad.yml"
        entity_file.write_text("entity: customer\n  bad: : indentation")

        with pytest.raises(YAMLParseError, match="Invalid YAML syntax"):
            parse_entity_file(entity_file)

    def test_parse_entity_missing_required_field(self, tmp_path):
        """Test parsing entity with missing required fields."""
        entity_file = tmp_path / "incomplete.yml"
        entity_file.write_text(
            """
entity: customer
# Missing 'source' and 'keys'
"""
        )

        with pytest.raises(ValidationParserError, match="Invalid entity definition"):
            parse_entity_file(entity_file)

    def test_parse_entity_empty_file(self, tmp_path):
        """Test parsing an empty YAML file."""
        entity_file = tmp_path / "empty.yml"
        entity_file.write_text("# Just comments\n")

        with pytest.raises(YAMLParseError, match="empty"):
            parse_entity_file(entity_file)


class TestParseRelationFile:
    """Test parsing relation files."""

    def test_parse_valid_relation_file(self, tmp_path):
        """Test parsing a valid relation YAML file."""
        relation_file = tmp_path / "purchased.yml"
        relation_file.write_text(
            """
relation: PURCHASED
from: customer
to: product
source: analytics.orders
mappings:
  from_key: customer_id
  to_key: product_id
properties:
  - name: order_id
    type: string
  - name: order_date
    type: datetime
description: Purchase relation
"""
        )

        relation = parse_relation_file(relation_file)
        assert relation.relation == "PURCHASED"
        assert relation.from_entity == "customer"
        assert relation.to_entity == "product"
        assert relation.get_source_name() == "analytics.orders"
        # Verify it's a SourceConfig with inferred type
        source_config = relation.get_source_config()
        assert source_config.name == "analytics.orders"
        assert source_config.type.value == "table"
        assert relation.mappings.from_key == "customer_id"
        assert relation.mappings.to_key == "product_id"
        assert len(relation.properties) == 2

    def test_parse_relation_lowercase_name(self, tmp_path):
        """Test that lowercase relation names are rejected."""
        relation_file = tmp_path / "bad_relation.yml"
        relation_file.write_text(
            """
relation: purchased
from: customer
to: product
source: analytics.orders
mappings:
  from_key: customer_id
  to_key: product_id
"""
        )

        with pytest.raises(ValidationParserError, match="uppercase"):
            parse_relation_file(relation_file)

    def test_parse_relation_missing_mappings(self, tmp_path):
        """Test parsing relation without mappings."""
        relation_file = tmp_path / "no_mappings.yml"
        relation_file.write_text(
            """
relation: PURCHASED
from: customer
to: product
source: analytics.orders
"""
        )

        with pytest.raises(ValidationParserError):
            parse_relation_file(relation_file)


class TestLoadEntitiesFromDirectory:
    """Test loading multiple entity files from a directory."""

    def test_load_entities_from_directory(self, tmp_path):
        """Test loading multiple entity files."""
        entities_dir = tmp_path / "entities"
        entities_dir.mkdir()

        # Create customer entity
        (entities_dir / "customer.yml").write_text(
            """
entity: customer
source: analytics.customers
keys: [customer_id]
"""
        )

        # Create product entity
        (entities_dir / "product.yml").write_text(
            """
entity: product
source: analytics.products
keys: [product_id]
"""
        )

        entities = load_entities_from_directory(entities_dir)
        assert len(entities) == 2
        entity_names = {e.entity for e in entities}
        assert entity_names == {"customer", "product"}

    def test_load_entities_empty_directory(self, tmp_path):
        """Test loading from an empty directory."""
        entities_dir = tmp_path / "empty"
        entities_dir.mkdir()

        entities = load_entities_from_directory(entities_dir)
        assert len(entities) == 0

    def test_load_entities_directory_not_found(self):
        """Test loading from non-existent directory."""
        with pytest.raises(ParserError, match="Directory not found"):
            load_entities_from_directory("/nonexistent/directory")

    def test_load_entities_with_error(self, tmp_path):
        """Test loading entities when one file has an error."""
        entities_dir = tmp_path / "entities"
        entities_dir.mkdir()

        # Valid entity
        (entities_dir / "customer.yml").write_text(
            """
entity: customer
source: analytics.customers
keys: [customer_id]
"""
        )

        # Invalid entity (missing required field)
        (entities_dir / "bad.yml").write_text(
            """
entity: bad_entity
# Missing source and keys
"""
        )

        with pytest.raises(ParserError, match="Failed to load entities"):
            load_entities_from_directory(entities_dir)


class TestLoadRelationsFromDirectory:
    """Test loading multiple relation files from a directory."""

    def test_load_relations_from_directory(self, tmp_path):
        """Test loading multiple relation files."""
        relations_dir = tmp_path / "relations"
        relations_dir.mkdir()

        # Create PURCHASED relation
        (relations_dir / "purchased.yml").write_text(
            """
relation: PURCHASED
from: customer
to: product
source: analytics.orders
mappings:
  from_key: customer_id
  to_key: product_id
"""
        )

        # Create REVIEWED relation
        (relations_dir / "reviewed.yml").write_text(
            """
relation: REVIEWED
from: customer
to: product
source: analytics.reviews
mappings:
  from_key: customer_id
  to_key: product_id
"""
        )

        relations = load_relations_from_directory(relations_dir)
        assert len(relations) == 2
        relation_names = {r.relation for r in relations}
        assert relation_names == {"PURCHASED", "REVIEWED"}


class TestLoadProjectManifest:
    """Test loading project manifest files."""

    def test_load_project_manifest(self, tmp_path):
        """Test loading a valid grai.yml manifest."""
        manifest_file = tmp_path / "grai.yml"
        manifest_file.write_text(
            """
name: my-project
version: 1.0.0
config:
  neo4j:
    uri: bolt://localhost:7687
"""
        )

        manifest = load_project_manifest(manifest_file)
        assert manifest["name"] == "my-project"
        assert manifest["version"] == "1.0.0"
        assert "config" in manifest
        assert manifest["config"]["neo4j"]["uri"] == "bolt://localhost:7687"

    def test_load_project_manifest_not_found(self):
        """Test loading non-existent manifest."""
        with pytest.raises(YAMLParseError, match="File not found"):
            load_project_manifest("/nonexistent/grai.yml")


class TestLoadProject:
    """Test loading complete projects."""

    def test_load_complete_project(self, tmp_path):
        """Test loading a complete project with entities and relations."""
        # Create project structure
        project_root = tmp_path / "my-project"
        project_root.mkdir()

        # Create grai.yml
        (project_root / "grai.yml").write_text(
            """
name: test-project
version: 1.0.0
config:
  neo4j:
    uri: bolt://localhost:7687
"""
        )

        # Create entities directory
        entities_dir = project_root / "entities"
        entities_dir.mkdir()
        (entities_dir / "customer.yml").write_text(
            """
entity: customer
source: analytics.customers
keys: [customer_id]
properties:
  - name: customer_id
    type: string
"""
        )

        # Create relations directory
        relations_dir = project_root / "relations"
        relations_dir.mkdir()
        (relations_dir / "purchased.yml").write_text(
            """
relation: PURCHASED
from: customer
to: product
source: analytics.orders
mappings:
  from_key: customer_id
  to_key: product_id
"""
        )

        # Load project
        project = load_project(project_root)

        assert project.name == "test-project"
        assert project.version == "1.0.0"
        assert len(project.entities) == 1
        assert len(project.relations) == 1
        assert project.entities[0].entity == "customer"
        assert project.relations[0].relation == "PURCHASED"
        assert "neo4j" in project.config

    def test_load_project_minimal(self, tmp_path):
        """Test loading a minimal project with just a manifest."""
        project_root = tmp_path / "minimal"
        project_root.mkdir()

        (project_root / "grai.yml").write_text(
            """
name: minimal-project
version: 0.1.0
"""
        )

        project = load_project(project_root)
        assert project.name == "minimal-project"
        assert project.version == "0.1.0"
        assert len(project.entities) == 0
        assert len(project.relations) == 0

    def test_load_project_not_found(self):
        """Test loading from non-existent project root."""
        with pytest.raises(ParserError, match="Project root not found"):
            load_project("/nonexistent/project")

    def test_load_project_missing_manifest(self, tmp_path):
        """Test loading project without grai.yml."""
        project_root = tmp_path / "no-manifest"
        project_root.mkdir()

        with pytest.raises(ParserError, match="Failed to load project manifest"):
            load_project(project_root)

    def test_load_project_custom_directories(self, tmp_path):
        """Test loading project with custom directory names."""
        project_root = tmp_path / "custom"
        project_root.mkdir()

        # Create grai.yml
        (project_root / "grai.yml").write_text(
            """
name: custom-project
version: 1.0.0
"""
        )

        # Create custom entities directory
        custom_entities = project_root / "my_entities"
        custom_entities.mkdir()
        (custom_entities / "customer.yml").write_text(
            """
entity: customer
source: analytics.customers
keys: [customer_id]
"""
        )

        # Load with custom directory name
        project = load_project(project_root, entities_dir="my_entities")
        assert len(project.entities) == 1
        assert project.entities[0].entity == "customer"

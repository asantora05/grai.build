"""
Tests for the IR Exporter module.

This module tests the Graph IR export functionality.
"""

import json

import pytest

from grai.core.exporter import export_to_ir, export_to_json, write_ir_file
from grai.core.exporter.ir_exporter import (
    get_entity_from_ir,
    get_relation_from_ir,
    load_ir_from_file,
    validate_ir_structure,
)
from grai.core.models import Entity, Project, Property, PropertyType, Relation, RelationMapping


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    customer = Entity(
        entity="customer",
        source="analytics.customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
            Property(name="email", type=PropertyType.STRING),
        ],
    )

    product = Entity(
        entity="product",
        source="analytics.products",
        keys=["product_id"],
        properties=[
            Property(name="product_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
            Property(name="price", type=PropertyType.FLOAT),
        ],
    )

    purchased = Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="analytics.orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[
            Property(name="order_date", type=PropertyType.DATE),
            Property(name="quantity", type=PropertyType.INTEGER),
        ],
    )

    return Project(
        name="test-graph",
        version="1.0.0",
        entities=[customer, product],
        relations=[purchased],
    )


class TestExportToIR:
    """Test export_to_ir function."""

    def test_export_basic_structure(self, sample_project):
        """Test that export creates the basic IR structure."""
        ir = export_to_ir(sample_project)

        assert "metadata" in ir
        assert "entities" in ir
        assert "relations" in ir
        assert "statistics" in ir

    def test_export_metadata(self, sample_project):
        """Test that metadata is exported correctly."""
        ir = export_to_ir(sample_project)
        metadata = ir["metadata"]

        assert metadata["name"] == "test-graph"
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] is None  # Project doesn't have description
        assert "exported_at" in metadata
        assert "exporter_version" in metadata

    def test_export_entities(self, sample_project):
        """Test that entities are exported correctly."""
        ir = export_to_ir(sample_project)
        entities = ir["entities"]

        assert len(entities) == 2

        customer = next(e for e in entities if e["name"] == "customer")
        # Source is now a dict with detailed config
        assert customer["source"]["name"] == "analytics.customers"
        assert customer["source"]["type"] == "table"  # Should be inferred
        assert customer["keys"] == ["customer_id"]
        assert len(customer["properties"]) == 3
        assert customer["metadata"]["property_count"] == 3
        assert customer["metadata"]["key_count"] == 1

    def test_export_relations(self, sample_project):
        """Test that relations are exported correctly."""
        ir = export_to_ir(sample_project)
        relations = ir["relations"]

        assert len(relations) == 1

        purchased = relations[0]
        assert purchased["name"] == "PURCHASED"
        assert purchased["from_entity"] == "customer"
        assert purchased["to_entity"] == "product"
        # Source is now a dict with detailed config
        assert purchased["source"]["name"] == "analytics.orders"
        assert purchased["source"]["type"] == "table"  # Should be inferred
        assert purchased["mappings"]["from_key"] == "customer_id"
        assert purchased["mappings"]["to_key"] == "product_id"
        assert len(purchased["properties"]) == 2

    def test_export_properties(self, sample_project):
        """Test that properties are exported correctly."""
        ir = export_to_ir(sample_project)

        customer = next(e for e in ir["entities"] if e["name"] == "customer")
        props = customer["properties"]

        email_prop = next(p for p in props if p["name"] == "email")
        assert email_prop["type"] == "string"
        assert email_prop["description"] is None

    def test_export_statistics(self, sample_project):
        """Test that statistics are calculated correctly."""
        ir = export_to_ir(sample_project)
        stats = ir["statistics"]

        assert stats["entity_count"] == 2
        assert stats["relation_count"] == 1
        assert stats["entity_properties"] == 6  # 3 + 3
        assert stats["relation_properties"] == 2
        assert stats["total_properties"] == 8
        assert stats["total_keys"] == 2


class TestExportToJSON:
    """Test export_to_json function."""

    def test_export_to_json_pretty(self, sample_project):
        """Test pretty-printed JSON export."""
        json_str = export_to_json(sample_project, pretty=True)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["metadata"]["name"] == "test-graph"

        # Should be pretty-printed (contains newlines and indentation)
        assert "\n" in json_str
        assert "  " in json_str

    def test_export_to_json_compact(self, sample_project):
        """Test compact JSON export."""
        json_str = export_to_json(sample_project, pretty=False)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["metadata"]["name"] == "test-graph"

        # Should be compact (fewer newlines)
        pretty_str = export_to_json(sample_project, pretty=True)
        assert len(json_str) < len(pretty_str)

    def test_export_custom_indent(self, sample_project):
        """Test JSON export with custom indentation."""
        json_str = export_to_json(sample_project, pretty=True, indent=4)

        # Should use 4-space indentation
        assert "\n    " in json_str

        parsed = json.loads(json_str)
        assert parsed["metadata"]["name"] == "test-graph"


class TestWriteIRFile:
    """Test write_ir_file function."""

    def test_write_ir_file(self, sample_project, tmp_path):
        """Test writing IR to a file."""
        output_path = tmp_path / "graph.json"
        write_ir_file(sample_project, output_path)

        assert output_path.exists()

        content = output_path.read_text()
        parsed = json.loads(content)

        assert parsed["metadata"]["name"] == "test-graph"
        assert len(parsed["entities"]) == 2

    def test_write_ir_file_creates_directory(self, sample_project, tmp_path):
        """Test that write_ir_file creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "graph.json"
        write_ir_file(sample_project, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_write_ir_file_compact(self, sample_project, tmp_path):
        """Test writing compact JSON."""
        output_path = tmp_path / "graph-compact.json"
        write_ir_file(sample_project, output_path, pretty=False)

        content = output_path.read_text()
        parsed = json.loads(content)

        assert parsed["metadata"]["name"] == "test-graph"
        # Compact format should be shorter
        pretty_path = tmp_path / "graph-pretty.json"
        write_ir_file(sample_project, pretty_path, pretty=True)
        assert len(content) < len(pretty_path.read_text())


class TestLoadIRFromFile:
    """Test load_ir_from_file function."""

    def test_load_ir_from_file(self, sample_project, tmp_path):
        """Test loading IR from a file."""
        output_path = tmp_path / "graph.json"
        write_ir_file(sample_project, output_path)

        loaded_ir = load_ir_from_file(output_path)

        assert loaded_ir["metadata"]["name"] == "test-graph"
        assert len(loaded_ir["entities"]) == 2
        assert len(loaded_ir["relations"]) == 1

    def test_load_ir_file_not_found(self, tmp_path):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_ir_from_file(tmp_path / "nonexistent.json")

    def test_load_ir_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        invalid_path = tmp_path / "invalid.json"
        invalid_path.write_text("{ invalid json")

        with pytest.raises(json.JSONDecodeError):
            load_ir_from_file(invalid_path)


class TestValidateIRStructure:
    """Test validate_ir_structure function."""

    def test_validate_valid_ir(self, sample_project):
        """Test validating a valid IR structure."""
        ir = export_to_ir(sample_project)
        assert validate_ir_structure(ir) is True

    def test_validate_not_dict(self):
        """Test validation fails for non-dictionary."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            validate_ir_structure([])

    def test_validate_missing_top_level_field(self, sample_project):
        """Test validation fails for missing top-level field."""
        ir = export_to_ir(sample_project)
        del ir["entities"]

        with pytest.raises(ValueError, match="missing required fields"):
            validate_ir_structure(ir)

    def test_validate_missing_metadata_field(self, sample_project):
        """Test validation fails for missing metadata field."""
        ir = export_to_ir(sample_project)
        del ir["metadata"]["name"]

        with pytest.raises(ValueError, match="Metadata missing required fields"):
            validate_ir_structure(ir)

    def test_validate_entities_not_list(self, sample_project):
        """Test validation fails if entities is not a list."""
        ir = export_to_ir(sample_project)
        ir["entities"] = {}

        with pytest.raises(ValueError, match="entities.*must be a list"):
            validate_ir_structure(ir)

    def test_validate_relations_not_list(self, sample_project):
        """Test validation fails if relations is not a list."""
        ir = export_to_ir(sample_project)
        ir["relations"] = {}

        with pytest.raises(ValueError, match="relations.*must be a list"):
            validate_ir_structure(ir)


class TestGetEntityFromIR:
    """Test get_entity_from_ir function."""

    def test_get_existing_entity(self, sample_project):
        """Test getting an existing entity."""
        ir = export_to_ir(sample_project)
        customer = get_entity_from_ir(ir, "customer")

        assert customer is not None
        assert customer["name"] == "customer"
        # Source is now a dict with detailed config
        assert customer["source"]["name"] == "analytics.customers"

    def test_get_nonexistent_entity(self, sample_project):
        """Test getting a non-existent entity."""
        ir = export_to_ir(sample_project)
        result = get_entity_from_ir(ir, "nonexistent")

        assert result is None


class TestGetRelationFromIR:
    """Test get_relation_from_ir function."""

    def test_get_existing_relation(self, sample_project):
        """Test getting an existing relation."""
        ir = export_to_ir(sample_project)
        purchased = get_relation_from_ir(ir, "PURCHASED")

        assert purchased is not None
        assert purchased["name"] == "PURCHASED"
        assert purchased["from_entity"] == "customer"
        assert purchased["to_entity"] == "product"

    def test_get_nonexistent_relation(self, sample_project):
        """Test getting a non-existent relation."""
        ir = export_to_ir(sample_project)
        result = get_relation_from_ir(ir, "NONEXISTENT")

        assert result is None


class TestIRRoundTrip:
    """Test round-trip export and load."""

    def test_round_trip(self, sample_project, tmp_path):
        """Test that IR can be written and loaded back."""
        output_path = tmp_path / "graph.json"

        # Export
        write_ir_file(sample_project, output_path)

        # Load
        loaded_ir = load_ir_from_file(output_path)

        # Validate
        assert validate_ir_structure(loaded_ir)

        # Check content
        assert loaded_ir["metadata"]["name"] == "test-graph"
        assert len(loaded_ir["entities"]) == 2
        assert len(loaded_ir["relations"]) == 1

        # Check specific entity
        customer = get_entity_from_ir(loaded_ir, "customer")
        assert customer["keys"] == ["customer_id"]
        assert len(customer["properties"]) == 3

        # Check specific relation
        purchased = get_relation_from_ir(loaded_ir, "PURCHASED")
        assert purchased["mappings"]["from_key"] == "customer_id"

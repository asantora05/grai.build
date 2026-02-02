"""
Tests for migration generator functionality.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import yaml

from grai.core.migrations.generator import MigrationGenerator
from grai.core.migrations.models import (
    ChangeType,
    EntityChange,
    PropertyChange,
    RelationChange,
    SchemaChanges,
)
from grai.core.models import Entity, Property, PropertyType, Relation, RelationMapping


class TestMigrationGeneratorInit:
    """Tests for MigrationGenerator initialization."""

    def test_init_creates_migrations_dir(self):
        """Test that init creates migrations directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            generator = MigrationGenerator(project_root)

            assert generator.migrations_dir.exists()
            assert generator.migrations_dir == project_root / "migrations"

    def test_init_uses_existing_migrations_dir(self):
        """Test that init works with existing migrations directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()
            (migrations_dir / "existing.yml").touch()

            generator = MigrationGenerator(project_root)

            assert generator.migrations_dir.exists()
            assert (generator.migrations_dir / "existing.yml").exists()


class TestGenerateVersion:
    """Tests for version generation."""

    def test_generate_version_format(self):
        """Test that version follows expected format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))
            version = generator._generate_version()

            # Should be YYYYMMDD_HHmmss format
            assert len(version) == 15
            assert version[8] == "_"
            assert version[:8].isdigit()
            assert version[9:].isdigit()

    def test_generate_version_uses_current_time(self):
        """Test that version reflects current time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            with patch("grai.core.migrations.generator.datetime") as mock_dt:
                mock_dt.now.return_value = datetime(2025, 1, 15, 10, 30, 45)
                version = generator._generate_version()

            assert version == "20250115_103045"


class TestSlugify:
    """Tests for text slugification."""

    def test_slugify_simple_text(self):
        """Test slugifying simple text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            result = generator._slugify("add customer entity")
            assert result == "add_customer_entity"

    def test_slugify_special_characters(self):
        """Test slugifying text with special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            result = generator._slugify("add 'customer' entity!")
            assert result == "add_customer_entity"

    def test_slugify_max_length(self):
        """Test slugify respects max length."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            long_text = "this is a very long description that should be truncated"
            result = generator._slugify(long_text, max_length=20)

            assert len(result) <= 20

    def test_slugify_consecutive_underscores(self):
        """Test that consecutive underscores are collapsed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            result = generator._slugify("add   multiple   spaces")
            assert "__" not in result


class TestCalculateChecksum:
    """Tests for checksum calculation."""

    def test_checksum_is_deterministic(self):
        """Test that same migration produces same checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            from grai.core.migrations.models import Migration

            migration = Migration(
                version="20250115_120000",
                description="Test migration",
                changes=SchemaChanges(entities=[], relations=[]),
                up_cypher=["MATCH (n) RETURN n"],
            )

            checksum1 = generator._calculate_checksum(migration)
            checksum2 = generator._calculate_checksum(migration)

            assert checksum1 == checksum2

    def test_checksum_differs_for_different_migrations(self):
        """Test that different migrations have different checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            from grai.core.migrations.models import Migration

            migration1 = Migration(
                version="20250115_120000",
                description="Test migration 1",
                changes=SchemaChanges(entities=[], relations=[]),
                up_cypher=["MATCH (n) RETURN n"],
            )

            migration2 = Migration(
                version="20250115_120001",
                description="Test migration 2",
                changes=SchemaChanges(entities=[], relations=[]),
                up_cypher=["MATCH (n) RETURN n", "CREATE (n:Test)"],
            )

            assert generator._calculate_checksum(migration1) != generator._calculate_checksum(
                migration2
            )


class TestGetLastSchemaState:
    """Tests for getting last schema state."""

    def test_empty_migrations_returns_empty_lists(self):
        """Test that empty migrations dir returns empty schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entities, relations = generator._get_last_schema_state()

            assert entities == []
            assert relations == []

    def test_with_existing_migrations(self):
        """Test loading state from existing migration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            generator = MigrationGenerator(project_root)

            # Create a migration file
            migration_data = {
                "version": "20250115_120000",
                "description": "Initial migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "abc123",
                "changes": {"entities": [], "relations": []},
                "up": [],
                "down": [],
            }

            migration_file = generator.migrations_dir / "20250115_120000_initial.yml"
            with open(migration_file, "w") as f:
                yaml.safe_dump(migration_data, f)

            # For now, returns empty (TODO in implementation)
            entities, relations = generator._get_last_schema_state()
            assert entities == []
            assert relations == []


class TestGenerateUpCypher:
    """Tests for generating up (apply) Cypher statements."""

    def test_generate_add_entity_cypher(self):
        """Test Cypher generation for adding an entity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.ADDED,
                new_keys=["customer_id"],
                properties_added=[{"name": "customer_id", "type": "string"}],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 1
            assert "CREATE CONSTRAINT customer_unique" in cypher[0]
            assert "n.customer_id" in cypher[0]

    def test_generate_remove_entity_cypher(self):
        """Test Cypher generation for removing an entity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="old_entity",
                change_type=ChangeType.REMOVED,
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 2
            assert "MATCH (n:old_entity) DETACH DELETE n" in cypher[0]
            assert "DROP CONSTRAINT old_entity_unique IF EXISTS" in cypher[1]

    def test_generate_modify_entity_add_property_cypher(self):
        """Test Cypher generation for adding a property to entity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.MODIFIED,
                properties_added=[{"name": "email", "type": "string"}],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 1
            assert "MATCH (n:customer) SET n.email = null" in cypher[0]

    def test_generate_modify_entity_remove_property_cypher(self):
        """Test Cypher generation for removing a property from entity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.MODIFIED,
                properties_removed=["old_field"],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 1
            assert "MATCH (n:customer) REMOVE n.old_field" in cypher[0]

    def test_generate_modify_entity_keys_changed_cypher(self):
        """Test Cypher generation for changing entity keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.MODIFIED,
                keys_changed=True,
                old_keys=["customer_id"],
                new_keys=["customer_id", "tenant_id"],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 2
            assert "DROP CONSTRAINT customer_unique IF EXISTS" in cypher[0]
            assert "CREATE CONSTRAINT customer_unique" in cypher[1]
            assert "n.customer_id" in cypher[1]
            assert "n.tenant_id" in cypher[1]

    def test_generate_add_relation_cypher(self):
        """Test Cypher generation for adding a relation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            relation_change = RelationChange(
                name="PURCHASED",
                change_type=ChangeType.ADDED,
                new_from="customer",
                new_to="product",
            )

            changes = SchemaChanges(entities=[], relations=[relation_change])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 1
            assert "PURCHASED" in cypher[0]

    def test_generate_remove_relation_cypher(self):
        """Test Cypher generation for removing a relation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            relation_change = RelationChange(
                name="OLD_RELATION",
                change_type=ChangeType.REMOVED,
            )

            changes = SchemaChanges(entities=[], relations=[relation_change])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 1
            assert "MATCH ()-[r:OLD_RELATION]->() DELETE r" in cypher[0]

    def test_generate_modify_relation_cypher(self):
        """Test Cypher generation for modifying a relation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            relation_change = RelationChange(
                name="PURCHASED",
                change_type=ChangeType.MODIFIED,
                properties_added=[{"name": "quantity", "type": "integer"}],
                properties_removed=["old_prop"],
            )

            changes = SchemaChanges(entities=[], relations=[relation_change])
            cypher = generator._generate_up_cypher(changes)

            assert len(cypher) == 2
            assert "SET r.quantity = null" in cypher[0]
            assert "REMOVE r.old_prop" in cypher[1]


class TestGenerateDownCypher:
    """Tests for generating down (rollback) Cypher statements."""

    def test_generate_down_reverses_add_entity(self):
        """Test that down Cypher removes added entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.ADDED,
                new_keys=["customer_id"],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_down_cypher(changes)

            # Down should remove the added entity
            assert any("DETACH DELETE" in c for c in cypher)

    def test_generate_down_reverses_remove_entity(self):
        """Test that down Cypher re-adds removed entities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.REMOVED,
                old_keys=["customer_id"],
                new_keys=["customer_id"],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_down_cypher(changes)

            # Down should recreate the constraint
            assert any("CREATE CONSTRAINT" in c for c in cypher)

    def test_generate_down_reverses_property_changes(self):
        """Test that down Cypher reverses property changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.MODIFIED,
                properties_added=[{"name": "email", "type": "string"}],
                properties_removed=["old_field"],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_down_cypher(changes)

            # Down should remove added property and restore removed one
            assert any("REMOVE n.email" in c for c in cypher)
            assert any("SET n.old_field = null" in c for c in cypher)

    def test_generate_down_reverses_key_changes(self):
        """Test that down Cypher reverses key changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.MODIFIED,
                keys_changed=True,
                old_keys=["customer_id"],
                new_keys=["customer_id", "tenant_id"],
            )

            changes = SchemaChanges(entities=[entity_change], relations=[])
            cypher = generator._generate_down_cypher(changes)

            # Should restore old key constraint
            assert any("DROP CONSTRAINT" in c for c in cypher)
            key_constraint = [c for c in cypher if "CREATE CONSTRAINT" in c]
            assert len(key_constraint) == 1
            assert "n.tenant_id" not in key_constraint[0]

    def test_generate_down_reverses_relation_changes(self):
        """Test that down Cypher reverses relation changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            relation_change = RelationChange(
                name="PURCHASED",
                change_type=ChangeType.MODIFIED,
                properties_added=[{"name": "quantity", "type": "integer"}],
                properties_removed=["old_prop"],
            )

            changes = SchemaChanges(entities=[], relations=[relation_change])
            cypher = generator._generate_down_cypher(changes)

            # Should reverse property changes
            assert any("REMOVE r.quantity" in c for c in cypher)
            assert any("SET r.old_prop = null" in c for c in cypher)


class TestGenerate:
    """Tests for the main generate method."""

    def test_generate_creates_migration(self):
        """Test that generate creates a migration object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity = Entity(
                entity="customer",
                source="customers",
                keys=["customer_id"],
                properties=[
                    Property(name="customer_id", type=PropertyType.STRING),
                ],
            )

            migration = generator.generate(
                current_entities=[entity],
                current_relations=[],
                description="Add customer entity",
            )

            assert migration.version is not None
            assert migration.description == "Add customer entity"
            assert migration.checksum is not None
            assert len(migration.up_cypher) > 0

    def test_generate_auto_description(self):
        """Test that generate creates auto description when not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity = Entity(
                entity="customer",
                source="customers",
                keys=["customer_id"],
                properties=[
                    Property(name="customer_id", type=PropertyType.STRING),
                ],
            )

            migration = generator.generate(
                current_entities=[entity],
                current_relations=[],
            )

            # Auto-generated description should mention entity
            assert "entities added" in migration.description


class TestSaveMigration:
    """Tests for saving migrations to files."""

    def test_save_migration_creates_file(self):
        """Test that save_migration creates a YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            from grai.core.migrations.models import Migration

            migration = Migration(
                version="20250115_120000",
                description="Test migration",
                changes=SchemaChanges(entities=[], relations=[]),
                up_cypher=["MATCH (n) RETURN n"],
                down_cypher=["MATCH (n) DELETE n"],
            )

            filepath = generator.save_migration(migration)

            assert filepath.exists()
            assert filepath.suffix == ".yml"
            assert "20250115_120000" in filepath.name

    def test_save_migration_content(self):
        """Test that saved migration has correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.ADDED,
                properties_added=[{"name": "customer_id", "type": "string"}],
                new_keys=["customer_id"],
            )

            from grai.core.migrations.models import Migration

            migration = Migration(
                version="20250115_120000",
                description="Add customer",
                changes=SchemaChanges(entities=[entity_change], relations=[]),
                up_cypher=["CREATE CONSTRAINT..."],
                down_cypher=["DROP CONSTRAINT..."],
                checksum="abc123",
            )

            filepath = generator.save_migration(migration)

            with open(filepath) as f:
                data = yaml.safe_load(f)

            assert data["version"] == "20250115_120000"
            assert data["description"] == "Add customer"
            assert data["checksum"] == "abc123"
            assert len(data["changes"]["entities"]) == 1
            assert data["changes"]["entities"][0]["name"] == "customer"
            assert data["up"] == ["CREATE CONSTRAINT..."]
            assert data["down"] == ["DROP CONSTRAINT..."]

    def test_save_migration_with_property_modifications(self):
        """Test saving migration with property modifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            prop_change = PropertyChange(
                name="age",
                old_type="string",
                new_type="integer",
                change_type=ChangeType.MODIFIED,
            )

            entity_change = EntityChange(
                name="customer",
                change_type=ChangeType.MODIFIED,
                properties_modified=[prop_change],
            )

            from grai.core.migrations.models import Migration

            migration = Migration(
                version="20250115_120000",
                description="Modify customer",
                changes=SchemaChanges(entities=[entity_change], relations=[]),
            )

            filepath = generator.save_migration(migration)

            with open(filepath) as f:
                data = yaml.safe_load(f)

            props_modified = data["changes"]["entities"][0]["properties_modified"]
            assert len(props_modified) == 1
            assert props_modified[0]["name"] == "age"
            assert props_modified[0]["old_type"] == "string"
            assert props_modified[0]["new_type"] == "integer"

    def test_save_migration_with_relation_changes(self):
        """Test saving migration with relation changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = MigrationGenerator(Path(tmpdir))

            relation_change = RelationChange(
                name="PURCHASED",
                change_type=ChangeType.ADDED,
                new_from="customer",
                new_to="product",
                properties_added=[{"name": "quantity", "type": "integer"}],
            )

            from grai.core.migrations.models import Migration

            migration = Migration(
                version="20250115_120000",
                description="Add PURCHASED relation",
                changes=SchemaChanges(entities=[], relations=[relation_change]),
            )

            filepath = generator.save_migration(migration)

            with open(filepath) as f:
                data = yaml.safe_load(f)

            relations = data["changes"]["relations"]
            assert len(relations) == 1
            assert relations[0]["name"] == "PURCHASED"
            assert relations[0]["new_from"] == "customer"
            assert relations[0]["new_to"] == "product"


class TestFullWorkflow:
    """Integration tests for the full migration generation workflow."""

    def test_generate_and_save_workflow(self):
        """Test complete workflow of generating and saving a migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            generator = MigrationGenerator(project_root)

            # Create entities
            customer = Entity(
                entity="customer",
                source="customers",
                keys=["customer_id"],
                properties=[
                    Property(name="customer_id", type=PropertyType.STRING),
                    Property(name="name", type=PropertyType.STRING),
                ],
            )

            product = Entity(
                entity="product",
                source="products",
                keys=["product_id"],
                properties=[
                    Property(name="product_id", type=PropertyType.STRING),
                    Property(name="name", type=PropertyType.STRING),
                ],
            )

            # Create relation
            purchased = Relation(
                relation="PURCHASED",
                from_entity="customer",
                to_entity="product",
                source="orders",
                mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
                properties=[
                    Property(name="order_date", type=PropertyType.DATETIME),
                ],
            )

            # Generate migration
            migration = generator.generate(
                current_entities=[customer, product],
                current_relations=[purchased],
                description="Initial schema setup",
            )

            # Save migration
            filepath = generator.save_migration(migration)

            # Verify file exists and is valid YAML
            assert filepath.exists()
            with open(filepath) as f:
                data = yaml.safe_load(f)

            assert data["version"] == migration.version
            assert data["description"] == "Initial schema setup"
            # Entity changes include both added entities
            assert len(data["changes"]["entities"]) == 2
            # Relation changes include the added relation
            assert len(data["changes"]["relations"]) == 1
            # Verify the entity names
            entity_names = {e["name"] for e in data["changes"]["entities"]}
            assert "customer" in entity_names
            assert "product" in entity_names

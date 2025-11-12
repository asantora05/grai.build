"""
Migration generator for creating migration files from schema changes.

This module generates migration files by comparing the current schema
with the last known state and creating appropriate up/down Cypher scripts.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

from grai.core.migrations.differ import diff_schemas
from grai.core.migrations.models import ChangeType, Migration, SchemaChanges
from grai.core.models import Entity, Relation


class MigrationGenerator:
    """
    Generates migration files from schema changes.

    This class compares the current schema (entities and relations) with
    the last known state and creates a migration file with up/down scripts.
    """

    def __init__(self, project_root: Path):
        """
        Initialize the migration generator.

        Args:
            project_root: Path to the project root directory.
        """
        self.project_root = project_root
        self.migrations_dir = project_root / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)

    def generate(
        self,
        current_entities: List[Entity],
        current_relations: List[Relation],
        description: Optional[str] = None,
    ) -> Migration:
        """
        Generate a new migration from current schema state.

        Args:
            current_entities: Current entity definitions.
            current_relations: Current relation definitions.
            description: Optional description for the migration.

        Returns:
            Migration object representing the changes.
        """
        # Get the last known schema state
        previous_entities, previous_relations = self._get_last_schema_state()

        # Compute differences
        changes = diff_schemas(
            old_entities=previous_entities,
            old_relations=previous_relations,
            new_entities=current_entities,
            new_relations=current_relations,
        )

        # Generate migration version (timestamp)
        version = self._generate_version()

        # Generate description if not provided
        if not description:
            description = changes.summary()

        # Generate Cypher scripts
        up_cypher = self._generate_up_cypher(changes)
        down_cypher = self._generate_down_cypher(changes)

        # Create migration object
        migration = Migration(
            version=version,
            description=description,
            changes=changes,
            up_cypher=up_cypher,
            down_cypher=down_cypher,
        )

        # Calculate checksum
        migration.checksum = self._calculate_checksum(migration)

        return migration

    def save_migration(self, migration: Migration) -> Path:
        """
        Save migration to a YAML file.

        Args:
            migration: Migration to save.

        Returns:
            Path to the saved migration file.
        """
        filename = f"{migration.version}_{self._slugify(migration.description)}.yml"
        filepath = self.migrations_dir / filename

        # Convert to dict for YAML serialization
        migration_dict = {
            "version": migration.version,
            "description": migration.description,
            "author": migration.author,
            "timestamp": migration.timestamp.isoformat(),
            "checksum": migration.checksum,
            "changes": {
                "entities": [
                    {
                        "name": e.name,
                        "change_type": e.change_type.value,
                        "properties_added": e.properties_added,
                        "properties_modified": [
                            {
                                "name": p.name,
                                "old_type": p.old_type,
                                "new_type": p.new_type,
                                "old_required": p.old_required,
                                "new_required": p.new_required,
                                "change_type": p.change_type.value,
                            }
                            for p in e.properties_modified
                        ],
                        "properties_removed": e.properties_removed,
                        "keys_changed": e.keys_changed,
                        "old_keys": e.old_keys,
                        "new_keys": e.new_keys,
                    }
                    for e in migration.changes.entities
                ],
                "relations": [
                    {
                        "name": r.name,
                        "change_type": r.change_type.value,
                        "from_entity_changed": r.from_entity_changed,
                        "to_entity_changed": r.to_entity_changed,
                        "old_from": r.old_from,
                        "new_from": r.new_from,
                        "old_to": r.old_to,
                        "new_to": r.new_to,
                        "properties_added": r.properties_added,
                        "properties_modified": [
                            {
                                "name": p.name,
                                "old_type": p.old_type,
                                "new_type": p.new_type,
                                "old_required": p.old_required,
                                "new_required": p.new_required,
                                "change_type": p.change_type.value,
                            }
                            for p in r.properties_modified
                        ],
                        "properties_removed": r.properties_removed,
                    }
                    for r in migration.changes.relations
                ],
            },
            "up": migration.up_cypher,
            "down": migration.down_cypher,
        }

        with open(filepath, "w") as f:
            yaml.safe_dump(migration_dict, f, default_flow_style=False, sort_keys=False)

        return filepath

    def _get_last_schema_state(self) -> tuple[List[Entity], List[Relation]]:
        """
        Get the schema state from the last migration.

        Returns:
            Tuple of (entities, relations) from last migration, or empty lists if none.
        """
        # List all migration files
        migration_files = sorted(self.migrations_dir.glob("*.yml"))

        if not migration_files:
            # No previous migrations, return empty state
            return [], []

        # Load the last migration
        last_migration_file = migration_files[-1]
        with open(last_migration_file) as f:
            _ = yaml.safe_load(f)

        # Reconstruct entities and relations from the migration
        # For now, return empty lists - we'll implement state reconstruction later
        # TODO: Implement proper state reconstruction from migration history
        return [], []

    def _generate_version(self) -> str:
        """
        Generate a migration version string (timestamp-based).

        Returns:
            Version string in format YYYYMMDDHHmmss.
        """
        now = datetime.now()
        return now.strftime("%Y%m%d_%H%M%S")

    def _calculate_checksum(self, migration: Migration) -> str:
        """
        Calculate checksum for migration integrity.

        Args:
            migration: Migration to calculate checksum for.

        Returns:
            SHA256 checksum hex string.
        """
        # Create a deterministic string representation
        content = f"{migration.version}|{migration.description}|{len(migration.up_cypher)}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _slugify(self, text: str, max_length: int = 50) -> str:
        """
        Convert text to a URL-friendly slug.

        Args:
            text: Text to slugify.
            max_length: Maximum length of slug.

        Returns:
            Slugified text.
        """
        # Replace spaces and special chars with underscores
        slug = "".join(c if c.isalnum() or c == "_" else "_" for c in text.lower())
        # Remove consecutive underscores
        slug = "_".join(filter(None, slug.split("_")))
        # Truncate to max length
        return slug[:max_length]

    def _generate_up_cypher(self, changes: SchemaChanges) -> List[str]:
        """
        Generate Cypher statements to apply the migration (up).

        Args:
            changes: Schema changes to apply.

        Returns:
            List of Cypher statements.
        """
        cypher_statements = []

        # Process entity changes
        for entity_change in changes.entities:
            if entity_change.change_type == ChangeType.ADDED:
                cypher_statements.extend(self._generate_add_entity_cypher(entity_change))
            elif entity_change.change_type == ChangeType.REMOVED:
                cypher_statements.extend(self._generate_remove_entity_cypher(entity_change))
            elif entity_change.change_type == ChangeType.MODIFIED:
                cypher_statements.extend(self._generate_modify_entity_cypher(entity_change))

        # Process relation changes
        for relation_change in changes.relations:
            if relation_change.change_type == ChangeType.ADDED:
                cypher_statements.extend(self._generate_add_relation_cypher(relation_change))
            elif relation_change.change_type == ChangeType.REMOVED:
                cypher_statements.extend(self._generate_remove_relation_cypher(relation_change))
            elif relation_change.change_type == ChangeType.MODIFIED:
                cypher_statements.extend(self._generate_modify_relation_cypher(relation_change))

        return cypher_statements

    def _generate_down_cypher(self, changes: SchemaChanges) -> List[str]:
        """
        Generate Cypher statements to rollback the migration (down).

        Args:
            changes: Schema changes to rollback.

        Returns:
            List of Cypher statements.
        """
        cypher_statements = []

        # Reverse the changes - added becomes removed, removed becomes added
        for entity_change in changes.entities:
            if entity_change.change_type == ChangeType.ADDED:
                cypher_statements.extend(self._generate_remove_entity_cypher(entity_change))
            elif entity_change.change_type == ChangeType.REMOVED:
                cypher_statements.extend(self._generate_add_entity_cypher(entity_change))
            elif entity_change.change_type == ChangeType.MODIFIED:
                # For modifications, reverse the property changes
                cypher_statements.extend(self._generate_reverse_modify_entity_cypher(entity_change))

        for relation_change in changes.relations:
            if relation_change.change_type == ChangeType.ADDED:
                cypher_statements.extend(self._generate_remove_relation_cypher(relation_change))
            elif relation_change.change_type == ChangeType.REMOVED:
                cypher_statements.extend(self._generate_add_relation_cypher(relation_change))
            elif relation_change.change_type == ChangeType.MODIFIED:
                cypher_statements.extend(
                    self._generate_reverse_modify_relation_cypher(relation_change)
                )

        return cypher_statements

    def _generate_add_entity_cypher(self, entity_change) -> List[str]:
        """Generate Cypher for adding an entity (creating constraint)."""
        statements = []
        entity_name = entity_change.name

        # Add constraint for keys
        if entity_change.new_keys:
            key_props = ", ".join(f"n.{key}" for key in entity_change.new_keys)
            statements.append(
                f"CREATE CONSTRAINT {entity_name}_unique IF NOT EXISTS "
                f"FOR (n:{entity_name}) REQUIRE ({key_props}) IS UNIQUE"
            )

        return statements

    def _generate_remove_entity_cypher(self, entity_change) -> List[str]:
        """Generate Cypher for removing an entity."""
        statements = []
        entity_name = entity_change.name

        # Remove all nodes of this type
        statements.append(f"MATCH (n:{entity_name}) DETACH DELETE n")

        # Drop constraint
        statements.append(f"DROP CONSTRAINT {entity_name}_unique IF EXISTS")

        return statements

    def _generate_modify_entity_cypher(self, entity_change) -> List[str]:
        """Generate Cypher for modifying an entity."""
        statements = []
        entity_name = entity_change.name

        # Add new properties (set to null initially)
        for prop in entity_change.properties_added:
            prop_name = prop["name"]
            statements.append(f"MATCH (n:{entity_name}) SET n.{prop_name} = null")

        # Remove properties
        for prop_name in entity_change.properties_removed:
            statements.append(f"MATCH (n:{entity_name}) REMOVE n.{prop_name}")

        # Handle key changes
        if entity_change.keys_changed:
            # Drop old constraint
            statements.append(f"DROP CONSTRAINT {entity_name}_unique IF EXISTS")
            # Create new constraint
            if entity_change.new_keys:
                key_props = ", ".join(f"n.{key}" for key in entity_change.new_keys)
                statements.append(
                    f"CREATE CONSTRAINT {entity_name}_unique IF NOT EXISTS "
                    f"FOR (n:{entity_name}) REQUIRE ({key_props}) IS UNIQUE"
                )

        return statements

    def _generate_reverse_modify_entity_cypher(self, entity_change) -> List[str]:
        """Generate Cypher to reverse entity modifications."""
        statements = []
        entity_name = entity_change.name

        # Reverse: remove added properties
        for prop in entity_change.properties_added:
            prop_name = prop["name"]
            statements.append(f"MATCH (n:{entity_name}) REMOVE n.{prop_name}")

        # Reverse: add back removed properties (set to null)
        for prop_name in entity_change.properties_removed:
            statements.append(f"MATCH (n:{entity_name}) SET n.{prop_name} = null")

        # Reverse key changes
        if entity_change.keys_changed:
            statements.append(f"DROP CONSTRAINT {entity_name}_unique IF EXISTS")
            if entity_change.old_keys:
                key_props = ", ".join(f"n.{key}" for key in entity_change.old_keys)
                statements.append(
                    f"CREATE CONSTRAINT {entity_name}_unique IF NOT EXISTS "
                    f"FOR (n:{entity_name}) REQUIRE ({key_props}) IS UNIQUE"
                )

        return statements

    def _generate_add_relation_cypher(self, relation_change) -> List[str]:
        """Generate Cypher for adding a relation."""
        # For now, just return a comment - actual relation creation happens via data loading
        return [f"// Relation {relation_change.name} added - schema only"]

    def _generate_remove_relation_cypher(self, relation_change) -> List[str]:
        """Generate Cypher for removing a relation."""
        statements = []
        relation_name = relation_change.name

        # Delete all relationships of this type
        statements.append(f"MATCH ()-[r:{relation_name}]->() DELETE r")

        return statements

    def _generate_modify_relation_cypher(self, relation_change) -> List[str]:
        """Generate Cypher for modifying a relation."""
        statements = []
        relation_name = relation_change.name

        # Add new properties to existing relationships
        for prop in relation_change.properties_added:
            prop_name = prop["name"]
            statements.append(f"MATCH ()-[r:{relation_name}]->() SET r.{prop_name} = null")

        # Remove properties from relationships
        for prop_name in relation_change.properties_removed:
            statements.append(f"MATCH ()-[r:{relation_name}]->() REMOVE r.{prop_name}")

        return statements

    def _generate_reverse_modify_relation_cypher(self, relation_change) -> List[str]:
        """Generate Cypher to reverse relation modifications."""
        statements = []
        relation_name = relation_change.name

        # Reverse: remove added properties
        for prop in relation_change.properties_added:
            prop_name = prop["name"]
            statements.append(f"MATCH ()-[r:{relation_name}]->() REMOVE r.{prop_name}")

        # Reverse: add back removed properties
        for prop_name in relation_change.properties_removed:
            statements.append(f"MATCH ()-[r:{relation_name}]->() SET r.{prop_name} = null")

        return statements

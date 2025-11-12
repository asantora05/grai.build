"""
Schema differ for detecting changes between schema versions.

This module compares two schema states and generates a structured
representation of the differences.
"""

from typing import List, Optional

from grai.core.migrations.models import (
    ChangeType,
    EntityChange,
    PropertyChange,
    RelationChange,
    SchemaChanges,
)
from grai.core.models import Entity, Relation


class SchemaDiffer:
    """
    Compares two schema states and generates change descriptions.

    This is used by the migration generator to detect what has changed
    between the last migration and the current schema definition.
    """

    def __init__(
        self,
        old_entities: Optional[List[Entity]] = None,
        old_relations: Optional[List[Relation]] = None,
        new_entities: Optional[List[Entity]] = None,
        new_relations: Optional[List[Relation]] = None,
    ):
        """
        Initialize the differ with old and new schema states.

        Args:
            old_entities: Entities from previous schema state.
            old_relations: Relations from previous schema state.
            new_entities: Entities from current schema state.
            new_relations: Relations from current schema state.
        """
        self.old_entities = {e.name: e for e in (old_entities or [])}
        self.old_relations = {r.name: r for r in (old_relations or [])}
        self.new_entities = {e.name: e for e in (new_entities or [])}
        self.new_relations = {r.name: r for r in (new_relations or [])}

    def diff(self) -> SchemaChanges:
        """
        Compute the differences between old and new schemas.

        Returns:
            SchemaChanges object containing all detected changes.
        """
        entity_changes = self._diff_entities()
        relation_changes = self._diff_relations()

        return SchemaChanges(entities=entity_changes, relations=relation_changes)

    def _diff_entities(self) -> List[EntityChange]:
        """Compute changes to entities."""
        changes = []

        # Find added entities
        for name, entity in self.new_entities.items():
            if name not in self.old_entities:
                changes.append(
                    EntityChange(
                        name=name,
                        change_type=ChangeType.ADDED,
                        properties_added=[p.model_dump() for p in entity.properties],
                        new_keys=entity.keys,
                    )
                )

        # Find removed entities
        for name in self.old_entities:
            if name not in self.new_entities:
                old_entity = self.old_entities[name]
                changes.append(
                    EntityChange(
                        name=name,
                        change_type=ChangeType.REMOVED,
                        properties_removed=[p.name for p in old_entity.properties],
                        old_keys=old_entity.keys,
                    )
                )

        # Find modified entities
        for name in set(self.old_entities.keys()) & set(self.new_entities.keys()):
            old_entity = self.old_entities[name]
            new_entity = self.new_entities[name]

            entity_change = self._diff_entity_properties(old_entity, new_entity)
            if entity_change:
                changes.append(entity_change)

        return changes

    def _diff_entity_properties(
        self, old_entity: Entity, new_entity: Entity
    ) -> Optional[EntityChange]:
        """Compare properties of a single entity."""
        old_props = {p.name: p for p in old_entity.properties}
        new_props = {p.name: p for p in new_entity.properties}

        properties_added = []
        properties_removed = []
        properties_modified = []

        # Find added properties
        for name, prop in new_props.items():
            if name not in old_props:
                properties_added.append(prop.model_dump())

        # Find removed properties
        for name in old_props:
            if name not in new_props:
                properties_removed.append(name)

        # Find modified properties
        for name in set(old_props.keys()) & set(new_props.keys()):
            old_prop = old_props[name]
            new_prop = new_props[name]

            if old_prop.type != new_prop.type or old_prop.required != new_prop.required:
                properties_modified.append(
                    PropertyChange(
                        name=name,
                        old_type=old_prop.type.value if old_prop.type else None,
                        new_type=new_prop.type.value if new_prop.type else None,
                        old_required=old_prop.required,
                        new_required=new_prop.required,
                        change_type=ChangeType.MODIFIED,
                    )
                )

        # Check if keys changed
        keys_changed = set(old_entity.keys or []) != set(new_entity.keys or [])

        # Only create change if something actually changed
        if properties_added or properties_removed or properties_modified or keys_changed:
            return EntityChange(
                name=new_entity.name,
                change_type=ChangeType.MODIFIED,
                properties_added=properties_added,
                properties_modified=properties_modified,
                properties_removed=properties_removed,
                keys_changed=keys_changed,
                old_keys=old_entity.keys,
                new_keys=new_entity.keys,
            )

        return None

    def _diff_relations(self) -> List[RelationChange]:
        """Compute changes to relations."""
        changes = []

        # Find added relations
        for name, relation in self.new_relations.items():
            if name not in self.old_relations:
                changes.append(
                    RelationChange(
                        name=name,
                        change_type=ChangeType.ADDED,
                        new_from=relation.from_entity,
                        new_to=relation.to_entity,
                        properties_added=[p.model_dump() for p in relation.properties],
                    )
                )

        # Find removed relations
        for name in self.old_relations:
            if name not in self.new_relations:
                old_relation = self.old_relations[name]
                changes.append(
                    RelationChange(
                        name=name,
                        change_type=ChangeType.REMOVED,
                        old_from=old_relation.from_entity,
                        old_to=old_relation.to_entity,
                        properties_removed=[p.name for p in old_relation.properties],
                    )
                )

        # Find modified relations
        for name in set(self.old_relations.keys()) & set(self.new_relations.keys()):
            old_relation = self.old_relations[name]
            new_relation = self.new_relations[name]

            relation_change = self._diff_relation_properties(old_relation, new_relation)
            if relation_change:
                changes.append(relation_change)

        return changes

    def _diff_relation_properties(
        self, old_relation: Relation, new_relation: Relation
    ) -> Optional[RelationChange]:
        """Compare properties of a single relation."""
        old_props = {p.name: p for p in old_relation.properties}
        new_props = {p.name: p for p in new_relation.properties}

        properties_added = []
        properties_removed = []
        properties_modified = []

        # Find added properties
        for name, prop in new_props.items():
            if name not in old_props:
                properties_added.append(prop.model_dump())

        # Find removed properties
        for name in old_props:
            if name not in new_props:
                properties_removed.append(name)

        # Find modified properties
        for name in set(old_props.keys()) & set(new_props.keys()):
            old_prop = old_props[name]
            new_prop = new_props[name]

            if old_prop.type != new_prop.type or old_prop.required != new_prop.required:
                properties_modified.append(
                    PropertyChange(
                        name=name,
                        old_type=old_prop.type.value if old_prop.type else None,
                        new_type=new_prop.type.value if new_prop.type else None,
                        old_required=old_prop.required,
                        new_required=new_prop.required,
                        change_type=ChangeType.MODIFIED,
                    )
                )

        # Check if from/to entities changed
        from_changed = old_relation.from_entity != new_relation.from_entity
        to_changed = old_relation.to_entity != new_relation.to_entity

        # Only create change if something actually changed
        if (
            properties_added
            or properties_removed
            or properties_modified
            or from_changed
            or to_changed
        ):
            return RelationChange(
                name=new_relation.name,
                change_type=ChangeType.MODIFIED,
                from_entity_changed=from_changed,
                to_entity_changed=to_changed,
                old_from=old_relation.from_entity if from_changed else None,
                new_from=new_relation.from_entity if from_changed else None,
                old_to=old_relation.to_entity if to_changed else None,
                new_to=new_relation.to_entity if to_changed else None,
                properties_added=properties_added,
                properties_modified=properties_modified,
                properties_removed=properties_removed,
            )

        return None


def diff_schemas(
    old_entities: Optional[List[Entity]] = None,
    old_relations: Optional[List[Relation]] = None,
    new_entities: Optional[List[Entity]] = None,
    new_relations: Optional[List[Relation]] = None,
) -> SchemaChanges:
    """
    Convenience function to compute schema differences.

    Args:
        old_entities: Entities from previous schema state.
        old_relations: Relations from previous schema state.
        new_entities: Entities from current schema state.
        new_relations: Relations from current schema state.

    Returns:
        SchemaChanges object containing all detected changes.
    """
    differ = SchemaDiffer(old_entities, old_relations, new_entities, new_relations)
    return differ.diff()

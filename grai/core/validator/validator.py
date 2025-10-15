"""
Project validator for grai.build.

This module provides functions to validate that entity and relation definitions
are consistent, that all references exist, and that key mappings are valid.
"""

from typing import Dict, List, Optional

from grai.core.models import Entity, Project, Relation


class ValidationError(Exception):
    """Base exception for validation errors."""

    def __init__(self, message: str, context: Optional[str] = None):
        """
        Initialize validation error.

        Args:
            message: Error message.
            context: Optional context (e.g., entity or relation name).
        """
        self.context = context
        if context:
            super().__init__(f"{context}: {message}")
        else:
            super().__init__(message)


class EntityReferenceError(ValidationError):
    """Exception raised when an entity reference is invalid."""

    pass


class KeyMappingError(ValidationError):
    """Exception raised when a key mapping is invalid."""

    pass


class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        valid: Whether validation passed.
        errors: List of validation errors.
        warnings: List of validation warnings.
    """

    def __init__(self):
        """Initialize validation result."""
        self.valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str, context: Optional[str] = None) -> None:
        """
        Add an error to the result.

        Args:
            message: Error message.
            context: Optional context.
        """
        self.valid = False
        if context:
            self.errors.append(f"{context}: {message}")
        else:
            self.errors.append(message)

    def add_warning(self, message: str, context: Optional[str] = None) -> None:
        """
        Add a warning to the result.

        Args:
            message: Warning message.
            context: Optional context.
        """
        if context:
            self.warnings.append(f"{context}: {message}")
        else:
            self.warnings.append(message)

    def __bool__(self) -> bool:
        """Return whether validation passed."""
        return self.valid

    def __str__(self) -> str:
        """Return string representation of validation result."""
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  • {error}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  • {warning}")
        if not self.errors and not self.warnings:
            lines.append("✅ Validation passed with no errors or warnings")
        return "\n".join(lines)


def build_entity_index(entities: List[Entity]) -> Dict[str, Entity]:
    """
    Build an index of entities by name for quick lookup.

    Args:
        entities: List of entities.

    Returns:
        Dictionary mapping entity names to Entity objects.
    """
    return {entity.entity: entity for entity in entities}


def validate_entity_references(
    relations: List[Relation],
    entity_index: Dict[str, Entity],
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    """
    Validate that all entity references in relations exist.

    Args:
        relations: List of relations to validate.
        entity_index: Index of entities by name.
        result: Optional existing ValidationResult to add to.

    Returns:
        ValidationResult with any errors found.
    """
    if result is None:
        result = ValidationResult()

    for relation in relations:
        # Check from_entity exists
        if relation.from_entity not in entity_index:
            result.add_error(
                f"References non-existent entity '{relation.from_entity}'",
                context=f"Relation {relation.relation}",
            )

        # Check to_entity exists
        if relation.to_entity not in entity_index:
            result.add_error(
                f"References non-existent entity '{relation.to_entity}'",
                context=f"Relation {relation.relation}",
            )

    return result


def validate_key_mappings(
    relations: List[Relation],
    entity_index: Dict[str, Entity],
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    """
    Validate that key mappings in relations reference valid entity keys.

    Args:
        relations: List of relations to validate.
        entity_index: Index of entities by name.
        result: Optional existing ValidationResult to add to.

    Returns:
        ValidationResult with any errors found.
    """
    if result is None:
        result = ValidationResult()

    for relation in relations:
        # Skip if entities don't exist (caught by entity_references validation)
        if relation.from_entity not in entity_index or relation.to_entity not in entity_index:
            continue

        from_entity = entity_index[relation.from_entity]
        to_entity = entity_index[relation.to_entity]

        # Check from_key exists in from_entity
        if relation.mappings.from_key not in from_entity.keys:
            result.add_error(
                f"Key '{relation.mappings.from_key}' not found in entity '{relation.from_entity}' keys: {from_entity.keys}",
                context=f"Relation {relation.relation}",
            )

        # Check to_key exists in to_entity
        if relation.mappings.to_key not in to_entity.keys:
            result.add_error(
                f"Key '{relation.mappings.to_key}' not found in entity '{relation.to_entity}' keys: {to_entity.keys}",
                context=f"Relation {relation.relation}",
            )

    return result


def validate_property_definitions(
    entities: List[Entity],
    relations: List[Relation],
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    """
    Validate property definitions in entities and relations.

    Args:
        entities: List of entities to validate.
        relations: List of relations to validate.
        result: Optional existing ValidationResult to add to.

    Returns:
        ValidationResult with any errors or warnings found.
    """
    if result is None:
        result = ValidationResult()

    # Validate entities
    for entity in entities:
        # Check for duplicate property names
        property_names = [p.name for p in entity.properties]
        duplicates = set([name for name in property_names if property_names.count(name) > 1])
        if duplicates:
            result.add_error(
                f"Duplicate property names: {', '.join(duplicates)}",
                context=f"Entity {entity.entity}",
            )

        # Check that all keys have corresponding properties
        property_name_set = set(property_names)
        for key in entity.keys:
            if key not in property_name_set:
                result.add_warning(
                    f"Key '{key}' does not have a corresponding property definition",
                    context=f"Entity {entity.entity}",
                )

    # Validate relations
    for relation in relations:
        # Check for duplicate property names
        property_names = [p.name for p in relation.properties]
        duplicates = set([name for name in property_names if property_names.count(name) > 1])
        if duplicates:
            result.add_error(
                f"Duplicate property names: {', '.join(duplicates)}",
                context=f"Relation {relation.relation}",
            )

    return result


def validate_unique_names(
    entities: List[Entity],
    relations: List[Relation],
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    """
    Validate that entity and relation names are unique.

    Args:
        entities: List of entities to check.
        relations: List of relations to check.
        result: Optional existing ValidationResult to add to.

    Returns:
        ValidationResult with any duplicate names found.
    """
    if result is None:
        result = ValidationResult()

    # Check for duplicate entity names
    entity_names = [e.entity for e in entities]
    duplicate_entities = set([name for name in entity_names if entity_names.count(name) > 1])
    if duplicate_entities:
        result.add_error(f"Duplicate entity names: {', '.join(duplicate_entities)}")

    # Check for duplicate relation names
    relation_names = [r.relation for r in relations]
    duplicate_relations = set([name for name in relation_names if relation_names.count(name) > 1])
    if duplicate_relations:
        result.add_error(f"Duplicate relation names: {', '.join(duplicate_relations)}")

    return result


def validate_sources(
    entities: List[Entity],
    relations: List[Relation],
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    """
    Validate that sources are properly defined.

    Args:
        entities: List of entities to check.
        relations: List of relations to check.
        result: Optional existing ValidationResult to add to.

    Returns:
        ValidationResult with any source issues found.
    """
    if result is None:
        result = ValidationResult()

    # Check entities have valid sources
    for entity in entities:
        source_name = entity.get_source_name()
        if not source_name or not source_name.strip():
            result.add_error(
                "Entity has empty or missing source",
                context=f"Entity {entity.entity}",
            )

    # Check relations have valid sources
    for relation in relations:
        source_name = relation.get_source_name()
        if not source_name or not source_name.strip():
            result.add_error(
                "Relation has empty or missing source",
                context=f"Relation {relation.relation}",
            )

    return result


def validate_project(
    project: Project,
    strict: bool = True,
) -> ValidationResult:
    """
    Validate an entire project for consistency and correctness.

    Args:
        project: The project to validate.
        strict: If True, warnings will be treated as errors.

    Returns:
        ValidationResult with all errors and warnings.

    Raises:
        ValidationError: If strict=True and validation fails.
    """
    result = ValidationResult()

    # Build entity index for quick lookups
    entity_index = build_entity_index(project.entities)

    # Run all validations
    validate_unique_names(project.entities, project.relations, result)
    validate_sources(project.entities, project.relations, result)
    validate_entity_references(project.relations, entity_index, result)
    validate_key_mappings(project.relations, entity_index, result)
    validate_property_definitions(project.entities, project.relations, result)

    # Note: We don't check for circular dependencies because they are
    # normal and expected in graph structures (e.g., bidirectional relationships,
    # social networks, organizational hierarchies, etc.)

    # In strict mode, treat warnings as errors
    if strict and result.warnings:
        for warning in result.warnings:
            result.add_error(f"[Strict mode] {warning}")
        result.warnings.clear()

    return result


def validate_entity(entity: Entity) -> ValidationResult:
    """
    Validate a single entity.

    Args:
        entity: The entity to validate.

    Returns:
        ValidationResult with any errors or warnings.
    """
    result = ValidationResult()

    # Check for empty keys
    if not entity.keys:
        result.add_error("Entity must have at least one key", context=f"Entity {entity.entity}")

    # Check for duplicate property names
    property_names = [p.name for p in entity.properties]
    duplicates = set([name for name in property_names if property_names.count(name) > 1])
    if duplicates:
        result.add_error(
            f"Duplicate property names: {', '.join(duplicates)}",
            context=f"Entity {entity.entity}",
        )

    # Check that keys have properties
    property_name_set = set(property_names)
    for key in entity.keys:
        if key not in property_name_set:
            result.add_warning(
                f"Key '{key}' does not have a corresponding property definition",
                context=f"Entity {entity.entity}",
            )

    # Check source
    source_name = entity.get_source_name()
    if not source_name or not source_name.strip():
        result.add_error("Entity has empty or missing source", context=f"Entity {entity.entity}")

    return result


def validate_relation(
    relation: Relation,
    entity_index: Optional[Dict[str, Entity]] = None,
) -> ValidationResult:
    """
    Validate a single relation.

    Args:
        relation: The relation to validate.
        entity_index: Optional index of entities for reference checking.

    Returns:
        ValidationResult with any errors or warnings.
    """
    result = ValidationResult()

    # Check for duplicate property names
    property_names = [p.name for p in relation.properties]
    duplicates = set([name for name in property_names if property_names.count(name) > 1])
    if duplicates:
        result.add_error(
            f"Duplicate property names: {', '.join(duplicates)}",
            context=f"Relation {relation.relation}",
        )

    # Check source
    source_name = relation.get_source_name()
    if not source_name or not source_name.strip():
        result.add_error(
            "Relation has empty or missing source",
            context=f"Relation {relation.relation}",
        )

    # If entity_index provided, check references
    if entity_index is not None:
        if relation.from_entity not in entity_index:
            result.add_error(
                f"References non-existent entity '{relation.from_entity}'",
                context=f"Relation {relation.relation}",
            )

        if relation.to_entity not in entity_index:
            result.add_error(
                f"References non-existent entity '{relation.to_entity}'",
                context=f"Relation {relation.relation}",
            )

        # Check key mappings if entities exist
        if relation.from_entity in entity_index and relation.to_entity in entity_index:
            from_entity = entity_index[relation.from_entity]
            to_entity = entity_index[relation.to_entity]

            if relation.mappings.from_key not in from_entity.keys:
                result.add_error(
                    f"Key '{relation.mappings.from_key}' not found in entity '{relation.from_entity}' keys: {from_entity.keys}",
                    context=f"Relation {relation.relation}",
                )

            if relation.mappings.to_key not in to_entity.keys:
                result.add_error(
                    f"Key '{relation.mappings.to_key}' not found in entity '{relation.to_entity}' keys: {to_entity.keys}",
                    context=f"Relation {relation.relation}",
                )

    return result

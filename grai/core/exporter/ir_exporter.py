"""
Graph IR (Intermediate Representation) Exporter.

This module generates a JSON representation of the complete graph structure
including entities, relations, properties, constraints, and metadata.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from grai.core.models import Entity, Project, Property, Relation


def export_to_ir(project: Project) -> Dict[str, Any]:
    """
    Export a Project to Graph IR (Intermediate Representation).

    Args:
        project: The Project to export

    Returns:
        Dictionary containing the complete graph structure

    Example:
        >>> project = load_project(Path("."))
        >>> ir = export_to_ir(project)
        >>> print(ir["metadata"]["name"])
        'my-graph'
    """
    return {
        "metadata": _export_metadata(project),
        "entities": [_export_entity(entity) for entity in project.entities],
        "relations": [_export_relation(relation) for relation in project.relations],
        "statistics": _export_statistics(project),
    }


def _export_metadata(project: Project) -> Dict[str, Any]:
    """
    Export project metadata.

    Args:
        project: The Project

    Returns:
        Dictionary with metadata fields
    """
    return {
        "name": project.name,
        "version": project.version,
        "description": getattr(project, "description", None),
        "exported_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "exporter_version": "0.2.0",
    }


def _export_entity(entity: Entity) -> Dict[str, Any]:
    """
    Export an Entity to IR format.

    Args:
        entity: The Entity to export

    Returns:
        Dictionary with entity structure
    """
    source_config = entity.get_source_config()
    return {
        "name": entity.entity,
        "source": {
            "name": source_config.name,
            "type": source_config.type.value if source_config.type else None,
            "connection": source_config.connection,
            "schema": source_config.db_schema,
            "database": source_config.database,
            "format": source_config.format,
            "metadata": source_config.metadata,
        },
        "keys": entity.keys,
        "properties": [_export_property(prop) for prop in entity.properties],
        "metadata": {
            "property_count": len(entity.properties),
            "key_count": len(entity.keys),
            "has_source": bool(source_config.name),
        },
    }


def _export_relation(relation: Relation) -> Dict[str, Any]:
    """
    Export a Relation to IR format.

    Args:
        relation: The Relation to export

    Returns:
        Dictionary with relation structure
    """
    source_config = relation.get_source_config()
    return {
        "name": relation.relation,
        "from_entity": relation.from_entity,
        "to_entity": relation.to_entity,
        "source": {
            "name": source_config.name,
            "type": source_config.type.value if source_config.type else None,
            "connection": source_config.connection,
            "schema": source_config.db_schema,
            "database": source_config.database,
            "format": source_config.format,
            "metadata": source_config.metadata,
        },
        "mappings": {
            "from_key": relation.mappings.from_key,
            "to_key": relation.mappings.to_key,
        },
        "properties": [_export_property(prop) for prop in relation.properties],
        "metadata": {
            "property_count": len(relation.properties),
            "has_source": bool(source_config.name),
            "direction": f"{relation.from_entity} -> {relation.to_entity}",
        },
    }


def _export_property(prop: Property) -> Dict[str, Any]:
    """
    Export a Property to IR format.

    Args:
        prop: The Property to export

    Returns:
        Dictionary with property structure
    """
    return {
        "name": prop.name,
        "type": prop.type.value,
        "description": prop.description,
    }


def _export_statistics(project: Project) -> Dict[str, Any]:
    """
    Export project statistics.

    Args:
        project: The Project

    Returns:
        Dictionary with statistics
    """
    total_entity_properties = sum(len(e.properties) for e in project.entities)
    total_relation_properties = sum(len(r.properties) for r in project.relations)

    return {
        "entity_count": len(project.entities),
        "relation_count": len(project.relations),
        "total_properties": total_entity_properties + total_relation_properties,
        "entity_properties": total_entity_properties,
        "relation_properties": total_relation_properties,
        "total_keys": sum(len(e.keys) for e in project.entities),
    }


def export_to_json(
    project: Project,
    pretty: bool = True,
    indent: int = 2,
) -> str:
    """
    Export a Project to JSON string.

    Args:
        project: The Project to export
        pretty: Whether to pretty-print the JSON
        indent: Number of spaces for indentation (if pretty=True)

    Returns:
        JSON string representation of the graph

    Example:
        >>> project = load_project(Path("."))
        >>> json_str = export_to_json(project)
        >>> print(json_str[:100])
        '{
          "metadata": {
            "name": "my-graph",
        '
    """
    ir = export_to_ir(project)

    if pretty:
        return json.dumps(ir, indent=indent, ensure_ascii=False)
    else:
        return json.dumps(ir, ensure_ascii=False)


def write_ir_file(
    project: Project,
    output_path: Path,
    pretty: bool = True,
    indent: int = 2,
) -> None:
    """
    Write Graph IR to a JSON file.

    Args:
        project: The Project to export
        output_path: Path to write the JSON file
        pretty: Whether to pretty-print the JSON
        indent: Number of spaces for indentation

    Raises:
        OSError: If file cannot be written

    Example:
        >>> project = load_project(Path("."))
        >>> write_ir_file(project, Path("graph.json"))
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    json_content = export_to_json(project, pretty=pretty, indent=indent)
    output_path.write_text(json_content, encoding="utf-8")


def load_ir_from_file(input_path: Path) -> Dict[str, Any]:
    """
    Load Graph IR from a JSON file.

    Args:
        input_path: Path to the JSON file

    Returns:
        Dictionary containing the graph structure

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON

    Example:
        >>> ir = load_ir_from_file(Path("graph.json"))
        >>> print(ir["metadata"]["name"])
        'my-graph'
    """
    if not input_path.exists():
        raise FileNotFoundError(f"IR file not found: {input_path}")

    content = input_path.read_text(encoding="utf-8")
    return json.loads(content)


def validate_ir_structure(ir: Dict[str, Any]) -> bool:
    """
    Validate that a dictionary has the expected IR structure.

    Args:
        ir: The IR dictionary to validate

    Returns:
        True if structure is valid

    Raises:
        ValueError: If structure is invalid

    Example:
        >>> ir = export_to_ir(project)
        >>> validate_ir_structure(ir)
        True
    """
    required_top_level = {"metadata", "entities", "relations", "statistics"}

    if not isinstance(ir, dict):
        raise ValueError("IR must be a dictionary")

    missing = required_top_level - set(ir.keys())
    if missing:
        raise ValueError(f"IR missing required fields: {missing}")

    # Validate metadata
    required_metadata = {"name", "version", "exported_at"}
    metadata_keys = set(ir["metadata"].keys())
    missing_metadata = required_metadata - metadata_keys
    if missing_metadata:
        raise ValueError(f"Metadata missing required fields: {missing_metadata}")

    # Validate entities and relations are lists
    if not isinstance(ir["entities"], list):
        raise ValueError("IR 'entities' must be a list")

    if not isinstance(ir["relations"], list):
        raise ValueError("IR 'relations' must be a list")

    return True


def get_entity_from_ir(ir: Dict[str, Any], entity_name: str) -> Optional[Dict[str, Any]]:
    """
    Get an entity by name from IR.

    Args:
        ir: The IR dictionary
        entity_name: Name of the entity to find

    Returns:
        Entity dictionary or None if not found

    Example:
        >>> ir = export_to_ir(project)
        >>> customer = get_entity_from_ir(ir, "customer")
        >>> print(customer["name"])
        'customer'
    """
    for entity in ir["entities"]:
        if entity["name"] == entity_name:
            return entity
    return None


def get_relation_from_ir(ir: Dict[str, Any], relation_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a relation by name from IR.

    Args:
        ir: The IR dictionary
        relation_name: Name of the relation to find

    Returns:
        Relation dictionary or None if not found

    Example:
        >>> ir = export_to_ir(project)
        >>> purchased = get_relation_from_ir(ir, "PURCHASED")
        >>> print(purchased["from_entity"])
        'customer'
    """
    for relation in ir["relations"]:
        if relation["name"] == relation_name:
            return relation
    return None

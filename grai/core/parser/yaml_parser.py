"""
YAML parser for grai.build.

This module provides functions to parse YAML files containing entity and relation
definitions and convert them into Pydantic models.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import ValidationError

from grai.core.models import Entity, Project, Property, Relation, RelationMapping


class ParserError(Exception):
    """Base exception for parser errors."""

    def __init__(self, message: str, file_path: Optional[Path] = None):
        """
        Initialize parser error.

        Args:
            message: Error message.
            file_path: Optional path to the file that caused the error.
        """
        self.file_path = file_path
        if file_path:
            super().__init__(f"{file_path}: {message}")
        else:
            super().__init__(message)


class YAMLParseError(ParserError):
    """Exception raised when YAML parsing fails."""

    pass


class ValidationParserError(ParserError):
    """Exception raised when Pydantic validation fails."""

    pass


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        YAMLParseError: If the file cannot be read or parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if content is None:
                raise YAMLParseError("File is empty or contains only comments", file_path)
            if not isinstance(content, dict):
                raise YAMLParseError(
                    f"Expected YAML object (dict), got {type(content).__name__}", file_path
                )
            return content
    except FileNotFoundError:
        raise YAMLParseError(f"File not found: {file_path}", file_path)
    except yaml.YAMLError as e:
        raise YAMLParseError(f"Invalid YAML syntax: {e}", file_path)
    except Exception as e:
        raise YAMLParseError(f"Failed to read file: {e}", file_path)


def parse_property(data: Dict[str, Any]) -> Property:
    """
    Parse a property definition from a dictionary.

    Args:
        data: Dictionary containing property data.

    Returns:
        Property instance.

    Raises:
        ValidationParserError: If validation fails.
    """
    try:
        return Property(**data)
    except ValidationError as e:
        raise ValidationParserError(f"Invalid property definition: {e}")


def parse_entity(data: Dict[str, Any], file_path: Optional[Path] = None) -> Entity:
    """
    Parse an entity definition from a dictionary.

    Args:
        data: Dictionary containing entity data.
        file_path: Optional path to the source file for error messages.

    Returns:
        Entity instance.

    Raises:
        ValidationParserError: If validation fails.
    """
    try:
        # Parse properties if they exist
        if "properties" in data and isinstance(data["properties"], list):
            data["properties"] = [parse_property(prop) for prop in data["properties"]]

        return Entity(**data)
    except ValidationError as e:
        raise ValidationParserError(f"Invalid entity definition: {e}", file_path)
    except ValidationParserError:
        raise
    except Exception as e:
        raise ValidationParserError(f"Failed to parse entity: {e}", file_path)


def parse_relation(data: Dict[str, Any], file_path: Optional[Path] = None) -> Relation:
    """
    Parse a relation definition from a dictionary.

    Args:
        data: Dictionary containing relation data.
        file_path: Optional path to the source file for error messages.

    Returns:
        Relation instance.

    Raises:
        ValidationParserError: If validation fails.
    """
    try:
        # Parse properties if they exist
        if "properties" in data and isinstance(data["properties"], list):
            data["properties"] = [parse_property(prop) for prop in data["properties"]]

        # Parse mappings if they exist
        if "mappings" in data and isinstance(data["mappings"], dict):
            data["mappings"] = RelationMapping(**data["mappings"])

        return Relation(**data)
    except ValidationError as e:
        raise ValidationParserError(f"Invalid relation definition: {e}", file_path)
    except ValidationParserError:
        raise
    except Exception as e:
        raise ValidationParserError(f"Failed to parse relation: {e}", file_path)


def parse_entity_file(file_path: Union[str, Path]) -> Entity:
    """
    Parse an entity definition from a YAML file.

    Args:
        file_path: Path to the entity YAML file.

    Returns:
        Entity instance.

    Raises:
        ParserError: If parsing fails.
    """
    path = Path(file_path)
    data = load_yaml_file(path)
    return parse_entity(data, path)


def parse_relation_file(file_path: Union[str, Path]) -> Relation:
    """
    Parse a relation definition from a YAML file.

    Args:
        file_path: Path to the relation YAML file.

    Returns:
        Relation instance.

    Raises:
        ParserError: If parsing fails.
    """
    path = Path(file_path)
    data = load_yaml_file(path)
    return parse_relation(data, path)


def discover_yaml_files(directory: Path, pattern: str = "*.yml") -> List[Path]:
    """
    Recursively discover YAML files in a directory.

    Args:
        directory: Directory to search.
        pattern: Glob pattern for file matching (default: "*.yml").

    Returns:
        List of paths to YAML files.
    """
    if not directory.exists():
        return []

    if not directory.is_dir():
        return []

    # Use rglob for recursive search
    yaml_files = list(directory.glob(pattern))
    yaml_files.extend(directory.glob(pattern.replace(".yml", ".yaml")))

    return sorted(yaml_files)


def load_entities_from_directory(directory: Union[str, Path]) -> List[Entity]:
    """
    Load all entity definitions from a directory.

    Args:
        directory: Path to directory containing entity YAML files.

    Returns:
        List of Entity instances.

    Raises:
        ParserError: If parsing any file fails.
    """
    path = Path(directory)
    if not path.exists():
        raise ParserError(f"Directory not found: {path}")

    yaml_files = discover_yaml_files(path)
    entities = []
    errors = []

    for file_path in yaml_files:
        try:
            entity = parse_entity_file(file_path)
            entities.append(entity)
        except ParserError as e:
            errors.append(str(e))

    if errors:
        error_msg = "\n".join(errors)
        raise ParserError(f"Failed to load entities:\n{error_msg}")

    return entities


def load_relations_from_directory(directory: Union[str, Path]) -> List[Relation]:
    """
    Load all relation definitions from a directory.

    Args:
        directory: Path to directory containing relation YAML files.

    Returns:
        List of Relation instances.

    Raises:
        ParserError: If parsing any file fails.
    """
    path = Path(directory)
    if not path.exists():
        raise ParserError(f"Directory not found: {path}")

    yaml_files = discover_yaml_files(path)
    relations = []
    errors = []

    for file_path in yaml_files:
        try:
            relation = parse_relation_file(file_path)
            relations.append(relation)
        except ParserError as e:
            errors.append(str(e))

    if errors:
        error_msg = "\n".join(errors)
        raise ParserError(f"Failed to load relations:\n{error_msg}")

    return relations


def load_project_manifest(file_path: Union[str, Path] = "grai.yml") -> Dict[str, Any]:
    """
    Load the project manifest (grai.yml).

    Args:
        file_path: Path to the grai.yml file (default: "grai.yml").

    Returns:
        Dictionary containing project configuration.

    Raises:
        ParserError: If the file cannot be loaded.
    """
    path = Path(file_path)
    return load_yaml_file(path)


def load_project(
    project_root: Union[str, Path],
    entities_dir: str = "entities",
    relations_dir: str = "relations",
    manifest_file: str = "grai.yml",
) -> Project:
    """
    Load a complete grai.build project from a directory structure.

    Expected structure:
        project_root/
        ├── grai.yml
        ├── entities/
        │   ├── entity1.yml
        │   └── entity2.yml
        └── relations/
            └── relation1.yml

    Args:
        project_root: Root directory of the project.
        entities_dir: Subdirectory containing entity definitions (default: "entities").
        relations_dir: Subdirectory containing relation definitions (default: "relations").
        manifest_file: Name of the project manifest file (default: "grai.yml").

    Returns:
        Project instance with all entities and relations loaded.

    Raises:
        ParserError: If loading fails.
    """
    root = Path(project_root)

    if not root.exists():
        raise ParserError(f"Project root not found: {root}")

    # Load manifest
    manifest_path = root / manifest_file
    try:
        manifest = load_project_manifest(manifest_path)
    except ParserError as e:
        raise ParserError(f"Failed to load project manifest: {e}")

    # Load entities
    entities_path = root / entities_dir
    entities = []
    if entities_path.exists():
        try:
            entities = load_entities_from_directory(entities_path)
        except ParserError as e:
            raise ParserError(f"Failed to load entities: {e}")

    # Load relations
    relations_path = root / relations_dir
    relations = []
    if relations_path.exists():
        try:
            relations = load_relations_from_directory(relations_path)
        except ParserError as e:
            raise ParserError(f"Failed to load relations: {e}")

    # Create project
    try:
        project = Project(
            name=manifest.get("name", "unnamed-project"),
            version=manifest.get("version", "1.0.0"),
            entities=entities,
            relations=relations,
            config=manifest.get("config", {}),
        )
        return project
    except ValidationError as e:
        raise ValidationParserError(f"Invalid project configuration: {e}")

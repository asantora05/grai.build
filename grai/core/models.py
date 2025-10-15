"""
Core Pydantic models for grai.build.

This module defines the data structures for entities, relations, and properties
that form the foundation of the declarative knowledge graph modeling.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PropertyType(str, Enum):
    """Supported property types for entity and relation attributes."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"


class SourceType(str, Enum):
    """Supported source types for entities and relations."""

    DATABASE = "database"
    TABLE = "table"
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    API = "api"
    STREAM = "stream"
    OTHER = "other"


class SourceConfig(BaseModel):
    """
    Configuration for entity/relation data sources.

    Supports both simple string format (backward compatible) and detailed config.

    Attributes:
        name: Source identifier (e.g., table name, file path, API endpoint).
        type: Type of data source.
        connection: Optional connection string or identifier.
        schema: Optional database schema name.
        database: Optional database name.
        format: Optional data format details.
        metadata: Optional additional source metadata.
    """

    name: str = Field(..., min_length=1, description="Source identifier")
    type: Optional[SourceType] = Field(default=None, description="Source type")
    connection: Optional[str] = Field(default=None, description="Connection identifier")
    db_schema: Optional[str] = Field(default=None, description="Database schema")
    database: Optional[str] = Field(default=None, description="Database name")
    format: Optional[str] = Field(default=None, description="Data format details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_string(cls, source: str) -> "SourceConfig":
        """
        Create a SourceConfig from a simple string.

        Maintains backward compatibility with existing entity definitions.

        Args:
            source: Simple source string (e.g., "analytics.customers")

        Returns:
            SourceConfig with inferred type if possible.
        """
        # Try to infer type from string
        source_type = None
        if "." in source:
            # Likely a database table (schema.table)
            source_type = SourceType.TABLE
        elif source.endswith(".csv"):
            source_type = SourceType.CSV
        elif source.endswith(".json"):
            source_type = SourceType.JSON
        elif source.endswith(".parquet"):
            source_type = SourceType.PARQUET
        elif source.startswith("http://") or source.startswith("https://"):
            source_type = SourceType.API

        return cls(name=source, type=source_type)


class Property(BaseModel):
    """
    Represents a property (attribute) of an entity or relation.

    Attributes:
        name: The property name.
        type: The data type of the property.
        required: Whether this property must have a value.
        description: Optional description of the property.
        default: Optional default value for the property.
    """

    name: str = Field(..., min_length=1, description="Property name")
    type: PropertyType = Field(..., description="Property data type")
    required: bool = Field(default=False, description="Whether the property is required")
    description: Optional[str] = Field(default=None, description="Property description")
    default: Optional[Any] = Field(default=None, description="Default value")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that property name is a valid identifier."""
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Property name must be alphanumeric with underscores: {v}")
        return v


class Entity(BaseModel):
    """
    Represents a node/entity in the knowledge graph.

    Attributes:
        entity: The entity type name (becomes the node label in Neo4j).
        source: The data source - can be a string or SourceConfig object.
        keys: List of property names that uniquely identify this entity.
        properties: List of properties/attributes for this entity.
        description: Optional description of the entity.
        metadata: Optional additional metadata.
    """

    entity: str = Field(..., min_length=1, description="Entity type name")
    source: Union[str, SourceConfig] = Field(..., description="Data source identifier or config")
    keys: List[str] = Field(..., min_length=1, description="Key properties for uniqueness")
    properties: List[Property] = Field(
        default_factory=list, description="Entity properties/attributes"
    )
    description: Optional[str] = Field(default=None, description="Entity description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Union[str, SourceConfig]) -> SourceConfig:
        """Convert string source to SourceConfig for consistency."""
        if isinstance(v, str):
            return SourceConfig.from_string(v)
        return v

    @field_validator("entity")
    @classmethod
    def validate_entity_name(cls, v: str) -> str:
        """Validate that entity name is a valid identifier."""
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Entity name must be alphanumeric with underscores: {v}")
        return v

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, v: List[str]) -> List[str]:
        """Validate that all keys are non-empty."""
        if not all(k.strip() for k in v):
            raise ValueError("All keys must be non-empty strings")
        return v

    def get_property(self, name: str) -> Optional[Property]:
        """
        Get a property by name.

        Args:
            name: The property name to look up.

        Returns:
            The Property object if found, None otherwise.
        """
        return next((p for p in self.properties if p.name == name), None)

    def get_key_properties(self) -> List[Property]:
        """
        Get all properties that are designated as keys.

        Returns:
            List of Property objects that are keys.
        """
        return [p for p in self.properties if p.name in self.keys]

    def get_source_name(self) -> str:
        """
        Get the source name as a string.

        Returns:
            Source name string.
        """
        if isinstance(self.source, SourceConfig):
            return self.source.name
        return str(self.source)

    def get_source_config(self) -> SourceConfig:
        """
        Get the full source configuration.

        Returns:
            SourceConfig object.
        """
        if isinstance(self.source, SourceConfig):
            return self.source
        return SourceConfig.from_string(str(self.source))


class RelationMapping(BaseModel):
    """
    Defines how entities are connected in a relation.

    Attributes:
        from_key: The key property name on the source entity.
        to_key: The key property name on the target entity.
    """

    from_key: str = Field(..., min_length=1, description="Source entity key property")
    to_key: str = Field(..., min_length=1, description="Target entity key property")


class Relation(BaseModel):
    """
    Represents an edge/relation in the knowledge graph.

    Attributes:
        relation: The relation type name (becomes the edge label in Neo4j).
        from_entity: The source entity type.
        to_entity: The target entity type.
        source: The data source - can be a string or SourceConfig object.
        mappings: How source and target entities connect via keys.
        properties: List of properties/attributes for this relation.
        description: Optional description of the relation.
        metadata: Optional additional metadata.
    """

    relation: str = Field(..., min_length=1, description="Relation type name")
    from_entity: str = Field(..., min_length=1, alias="from", description="Source entity type")
    to_entity: str = Field(..., min_length=1, alias="to", description="Target entity type")
    source: Union[str, SourceConfig] = Field(..., description="Data source identifier or config")
    mappings: RelationMapping = Field(..., description="Key mappings between entities")
    properties: List[Property] = Field(
        default_factory=list, description="Relation properties/attributes"
    )
    description: Optional[str] = Field(default=None, description="Relation description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Union[str, SourceConfig]) -> SourceConfig:
        """Convert string source to SourceConfig for consistency."""
        if isinstance(v, str):
            return SourceConfig.from_string(v)
        return v

    @field_validator("relation")
    @classmethod
    def validate_relation_name(cls, v: str) -> str:
        """Validate that relation name is uppercase and valid."""
        if not v.isupper():
            raise ValueError(f"Relation name should be uppercase: {v}")
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Relation name must be alphanumeric with underscores: {v}")
        return v

    def get_property(self, name: str) -> Optional[Property]:
        """
        Get a property by name.

        Args:
            name: The property name to look up.

        Returns:
            The Property object if found, None otherwise.
        """
        return next((p for p in self.properties if p.name == name), None)

    def get_source_name(self) -> str:
        """
        Get the source name as a string.

        Returns:
            Source name string.
        """
        if isinstance(self.source, SourceConfig):
            return self.source.name
        return str(self.source)

    def get_source_config(self) -> SourceConfig:
        """
        Get the full source configuration.

        Returns:
            SourceConfig object.
        """
        if isinstance(self.source, SourceConfig):
            return self.source
        return SourceConfig.from_string(str(self.source))


class Project(BaseModel):
    """
    Represents a complete grai.build project configuration.

    Attributes:
        name: The project name.
        version: The project version.
        entities: List of entity definitions in the project.
        relations: List of relation definitions in the project.
        config: Optional project-level configuration.
    """

    name: str = Field(..., min_length=1, description="Project name")
    version: str = Field(default="1.0.0", description="Project version")
    entities: List[Entity] = Field(default_factory=list, description="Entity definitions")
    relations: List[Relation] = Field(default_factory=list, description="Relation definitions")
    config: Dict[str, Any] = Field(default_factory=dict, description="Project configuration")

    def get_entity(self, name: str) -> Optional[Entity]:
        """
        Get an entity by name.

        Args:
            name: The entity name to look up.

        Returns:
            The Entity object if found, None otherwise.
        """
        return next((e for e in self.entities if e.entity == name), None)

    def get_relation(self, name: str) -> Optional[Relation]:
        """
        Get a relation by name.

        Args:
            name: The relation name to look up.

        Returns:
            The Relation object if found, None otherwise.
        """
        return next((r for r in self.relations if r.relation == name), None)

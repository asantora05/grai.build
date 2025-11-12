"""
Migration models for schema versioning and change management.

This module defines the Pydantic models used to represent migrations,
schema changes, and migration history.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MigrationStatus(str, Enum):
    """Status of a migration."""

    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ChangeType(str, Enum):
    """Type of schema change."""

    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"


class PropertyChange(BaseModel):
    """Represents a change to a property."""

    name: str = Field(..., description="Property name")
    old_type: Optional[str] = Field(None, description="Previous type (for modifications)")
    new_type: Optional[str] = Field(None, description="New type (for modifications)")
    old_required: Optional[bool] = Field(None, description="Previous required status")
    new_required: Optional[bool] = Field(None, description="New required status")
    change_type: ChangeType = Field(..., description="Type of change")


class EntityChange(BaseModel):
    """Represents changes to an entity."""

    name: str = Field(..., description="Entity name")
    change_type: ChangeType = Field(..., description="Type of change")
    properties_added: List[Dict[str, Any]] = Field(
        default_factory=list, description="Properties added"
    )
    properties_modified: List[PropertyChange] = Field(
        default_factory=list, description="Properties modified"
    )
    properties_removed: List[str] = Field(default_factory=list, description="Properties removed")
    keys_changed: bool = Field(default=False, description="Whether keys were changed")
    old_keys: Optional[List[str]] = Field(None, description="Previous keys")
    new_keys: Optional[List[str]] = Field(None, description="New keys")


class RelationChange(BaseModel):
    """Represents changes to a relation."""

    name: str = Field(..., description="Relation name")
    change_type: ChangeType = Field(..., description="Type of change")
    from_entity_changed: bool = Field(default=False, description="Whether from entity changed")
    to_entity_changed: bool = Field(default=False, description="Whether to entity changed")
    old_from: Optional[str] = Field(None, description="Previous from entity")
    new_from: Optional[str] = Field(None, description="New from entity")
    old_to: Optional[str] = Field(None, description="Previous to entity")
    new_to: Optional[str] = Field(None, description="New to entity")
    properties_added: List[Dict[str, Any]] = Field(
        default_factory=list, description="Properties added"
    )
    properties_modified: List[PropertyChange] = Field(
        default_factory=list, description="Properties modified"
    )
    properties_removed: List[str] = Field(default_factory=list, description="Properties removed")


class SchemaChanges(BaseModel):
    """Collection of all schema changes in a migration."""

    entities: List[EntityChange] = Field(default_factory=list, description="Entity changes")
    relations: List[RelationChange] = Field(default_factory=list, description="Relation changes")

    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.entities) > 0 or len(self.relations) > 0

    def summary(self) -> str:
        """Generate a human-readable summary of changes."""
        parts = []

        entities_added = sum(1 for e in self.entities if e.change_type == ChangeType.ADDED)
        entities_modified = sum(1 for e in self.entities if e.change_type == ChangeType.MODIFIED)
        entities_removed = sum(1 for e in self.entities if e.change_type == ChangeType.REMOVED)

        relations_added = sum(1 for r in self.relations if r.change_type == ChangeType.ADDED)
        relations_modified = sum(1 for r in self.relations if r.change_type == ChangeType.MODIFIED)
        relations_removed = sum(1 for r in self.relations if r.change_type == ChangeType.REMOVED)

        if entities_added:
            parts.append(f"{entities_added} entities added")
        if entities_modified:
            parts.append(f"{entities_modified} entities modified")
        if entities_removed:
            parts.append(f"{entities_removed} entities removed")
        if relations_added:
            parts.append(f"{relations_added} relations added")
        if relations_modified:
            parts.append(f"{relations_modified} relations modified")
        if relations_removed:
            parts.append(f"{relations_removed} relations removed")

        return ", ".join(parts) if parts else "No changes"


class Migration(BaseModel):
    """
    Represents a schema migration.

    Attributes:
        version: Unique version identifier (timestamp-based).
        description: Human-readable description of the migration.
        author: Who created the migration (user or 'auto-generated').
        timestamp: When the migration was created.
        changes: Structured representation of schema changes.
        up_cypher: Cypher statements to apply the migration.
        down_cypher: Cypher statements to rollback the migration.
        checksum: Hash of the migration content for integrity checking.
    """

    version: str = Field(..., pattern=r"^\d{8}_\d{6}$", description="Migration version")
    description: str = Field(..., min_length=1, description="Migration description")
    author: str = Field(default="auto-generated", description="Migration author")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    changes: SchemaChanges = Field(..., description="Schema changes")
    up_cypher: List[str] = Field(default_factory=list, description="Cypher to apply migration")
    down_cypher: List[str] = Field(default_factory=list, description="Cypher to rollback migration")
    checksum: Optional[str] = Field(None, description="Migration content checksum")

    model_config = {"json_schema_extra": {"example": {"version": "20251112_120000"}}}


class MigrationHistory(BaseModel):
    """
    Represents a migration's execution history.

    This is stored in Neo4j as __GraiMigration nodes.
    """

    version: str = Field(..., description="Migration version")
    description: str = Field(..., description="Migration description")
    applied_at: datetime = Field(..., description="When migration was applied")
    status: MigrationStatus = Field(..., description="Migration status")
    checksum: str = Field(..., description="Migration content checksum")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = {"json_schema_extra": {"example": {"version": "20251112_120000"}}}

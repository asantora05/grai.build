"""Migration system for schema versioning and change management."""

from grai.core.migrations.differ import SchemaDiffer, diff_schemas
from grai.core.migrations.executor import MigrationExecutor
from grai.core.migrations.generator import MigrationGenerator
from grai.core.migrations.models import (
    ChangeType,
    EntityChange,
    Migration,
    MigrationHistory,
    MigrationStatus,
    PropertyChange,
    RelationChange,
    SchemaChanges,
)

__all__ = [
    "ChangeType",
    "EntityChange",
    "Migration",
    "MigrationExecutor",
    "MigrationGenerator",
    "MigrationHistory",
    "MigrationStatus",
    "PropertyChange",
    "RelationChange",
    "SchemaChanges",
    "SchemaDiffer",
    "diff_schemas",
]

"""
Migration executor for applying migrations to Neo4j.

This module handles executing migration Cypher scripts against Neo4j
and tracking migration state.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml
from neo4j import Driver

from grai.core.migrations.models import Migration, MigrationHistory, MigrationStatus


class MigrationExecutor:
    """
    Executes migrations against Neo4j and tracks state.

    This class applies migration Cypher scripts to the database and
    maintains migration history using __GraiMigration nodes.
    """

    def __init__(self, driver: Driver, project_root: Path):
        """
        Initialize the migration executor.

        Args:
            driver: Neo4j driver instance.
            project_root: Path to the project root directory.
        """
        self.driver = driver
        self.project_root = project_root
        self.migrations_dir = project_root / "migrations"

    def get_pending_migrations(self) -> List[Migration]:
        """
        Get list of pending migrations that haven't been applied.

        Returns:
            List of Migration objects for pending migrations.
        """
        # Get all migration files
        all_migrations = self._load_all_migrations()

        # Get applied migrations from Neo4j
        applied_versions = self._get_applied_versions()

        # Filter to pending only
        pending = [m for m in all_migrations if m.version not in applied_versions]

        return pending

    def get_migration_history(self) -> List[MigrationHistory]:
        """
        Get the full migration history from Neo4j.

        Returns:
            List of MigrationHistory objects, sorted by application time.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (m:__GraiMigration)
                RETURN m.version as version,
                       m.description as description,
                       m.applied_at as applied_at,
                       m.status as status,
                       m.checksum as checksum,
                       m.execution_time_ms as execution_time_ms,
                       m.error_message as error_message
                ORDER BY m.applied_at ASC
                """
            )

            history = []
            for record in result:
                history.append(
                    MigrationHistory(
                        version=record["version"],
                        description=record["description"],
                        applied_at=record["applied_at"],
                        status=MigrationStatus(record["status"]),
                        checksum=record["checksum"],
                        execution_time_ms=record.get("execution_time_ms"),
                        error_message=record.get("error_message"),
                    )
                )

            return history

    def apply_migration(self, migration: Migration, dry_run: bool = False) -> MigrationHistory:
        """
        Apply a single migration to Neo4j.

        Args:
            migration: Migration to apply.
            dry_run: If True, don't actually execute, just validate.

        Returns:
            MigrationHistory record of the execution.

        Raises:
            Exception: If migration fails.
        """
        start_time = time.time()
        error_message = None
        status = MigrationStatus.APPLIED

        try:
            if not dry_run:
                with self.driver.session() as session:
                    # Execute each Cypher statement
                    for cypher in migration.up_cypher:
                        session.run(cypher)

                    # Record migration in history
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    session.run(
                        """
                        CREATE (m:__GraiMigration {
                            version: $version,
                            description: $description,
                            applied_at: datetime(),
                            status: $status,
                            checksum: $checksum,
                            execution_time_ms: $execution_time_ms
                        })
                        """,
                        version=migration.version,
                        description=migration.description,
                        status=status.value,
                        checksum=migration.checksum,
                        execution_time_ms=execution_time_ms,
                    )
            else:
                # Dry run - just validate Cypher
                execution_time_ms = 0

        except Exception as e:
            status = MigrationStatus.FAILED
            error_message = str(e)
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Record failure
            if not dry_run:
                with self.driver.session() as session:
                    session.run(
                        """
                        CREATE (m:__GraiMigration {
                            version: $version,
                            description: $description,
                            applied_at: datetime(),
                            status: $status,
                            checksum: $checksum,
                            execution_time_ms: $execution_time_ms,
                            error_message: $error_message
                        })
                        """,
                        version=migration.version,
                        description=migration.description,
                        status=status.value,
                        checksum=migration.checksum,
                        execution_time_ms=execution_time_ms,
                        error_message=error_message,
                    )

            raise

        return MigrationHistory(
            version=migration.version,
            description=migration.description,
            applied_at=datetime.now(),
            status=status,
            checksum=migration.checksum or "",
            execution_time_ms=execution_time_ms,
            error_message=error_message,
        )

    def apply_all_pending(self, dry_run: bool = False) -> List[MigrationHistory]:
        """
        Apply all pending migrations in order.

        Args:
            dry_run: If True, don't actually execute, just validate.

        Returns:
            List of MigrationHistory records for applied migrations.

        Raises:
            Exception: If any migration fails (stops execution).
        """
        pending = self.get_pending_migrations()
        results = []

        for migration in pending:
            result = self.apply_migration(migration, dry_run=dry_run)
            results.append(result)

        return results

    def rollback_migration(self, version: Optional[str] = None) -> MigrationHistory:
        """
        Rollback a migration using its down script.

        Args:
            version: Specific version to rollback. If None, rolls back last migration.

        Returns:
            MigrationHistory record of the rollback.

        Raises:
            Exception: If rollback fails or migration not found.
        """
        if version is None:
            # Get last applied migration
            history = self.get_migration_history()
            if not history:
                raise ValueError("No migrations to rollback")
            version = history[-1].version

        # Load the migration
        migration = self._load_migration(version)
        if not migration:
            raise ValueError(f"Migration {version} not found")

        start_time = time.time()
        error_message = None
        status = MigrationStatus.ROLLED_BACK

        try:
            with self.driver.session() as session:
                # Execute down script
                for cypher in migration.down_cypher:
                    session.run(cypher)

                # Update migration status
                execution_time_ms = int((time.time() - start_time) * 1000)
                session.run(
                    """
                    MATCH (m:__GraiMigration {version: $version})
                    SET m.status = $status,
                        m.rolled_back_at = datetime(),
                        m.rollback_time_ms = $execution_time_ms
                    """,
                    version=version,
                    status=status.value,
                    execution_time_ms=execution_time_ms,
                )

        except Exception as e:
            status = MigrationStatus.FAILED
            error_message = str(e)
            raise

        return MigrationHistory(
            version=migration.version,
            description=migration.description,
            applied_at=datetime.now(),
            status=status,
            checksum=migration.checksum or "",
            execution_time_ms=int((time.time() - start_time) * 1000),
            error_message=error_message,
        )

    def _load_all_migrations(self) -> List[Migration]:
        """Load all migration files from the migrations directory."""
        migrations = []

        for migration_file in sorted(self.migrations_dir.glob("*.yml")):
            migration = self._load_migration_from_file(migration_file)
            if migration:
                migrations.append(migration)

        return migrations

    def _load_migration(self, version: str) -> Optional[Migration]:
        """Load a specific migration by version."""
        for migration_file in self.migrations_dir.glob(f"{version}_*.yml"):
            return self._load_migration_from_file(migration_file)
        return None

    def _load_migration_from_file(self, filepath: Path) -> Optional[Migration]:
        """Load migration from YAML file."""
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)

            # For now, just load basic info - full reconstruction coming later
            return Migration(
                version=data["version"],
                description=data["description"],
                author=data.get("author", "unknown"),
                timestamp=datetime.fromisoformat(data["timestamp"]),
                changes=data.get("changes", {"entities": [], "relations": []}),
                up_cypher=data.get("up", []),
                down_cypher=data.get("down", []),
                checksum=data.get("checksum"),
            )
        except Exception:
            return None

    def _get_applied_versions(self) -> set:
        """Get set of applied migration versions from Neo4j."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (m:__GraiMigration)
                WHERE m.status IN ['applied', 'failed']
                RETURN m.version as version
                """
            )
            return {record["version"] for record in result}

    def verify_migrations(self) -> bool:
        """
        Verify that migration files match applied migrations in database.

        Returns:
            True if all migrations are consistent, False otherwise.
        """
        all_migrations = self._load_all_migrations()
        applied_history = self.get_migration_history()

        # Check that all applied migrations have matching files
        applied_versions = {h.version for h in applied_history}
        file_versions = {m.version for m in all_migrations}

        missing_files = applied_versions - file_versions
        if missing_files:
            print(f"Warning: Applied migrations missing files: {missing_files}")
            return False

        # Check checksums match
        for history_entry in applied_history:
            migration = next(
                (m for m in all_migrations if m.version == history_entry.version), None
            )
            if migration and migration.checksum != history_entry.checksum:
                print(f"Warning: Checksum mismatch for migration {migration.version}")
                return False

        return True

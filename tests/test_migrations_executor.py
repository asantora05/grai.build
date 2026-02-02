"""
Tests for migration executor functionality.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
import yaml

from grai.core.migrations.executor import MigrationExecutor
from grai.core.migrations.models import (
    Migration,
    MigrationStatus,
    SchemaChanges,
)


def create_mock_driver():
    """Create a mock Neo4j driver."""
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = Mock(return_value=session)
    driver.session.return_value.__exit__ = Mock(return_value=False)
    return driver, session


class TestMigrationExecutorInit:
    """Tests for MigrationExecutor initialization."""

    def test_init_sets_attributes(self):
        """Test that init sets driver and project_root."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            executor = MigrationExecutor(driver, project_root)

            assert executor.driver == driver
            assert executor.project_root == project_root
            assert executor.migrations_dir == project_root / "migrations"


class TestLoadMigrationFromFile:
    """Tests for loading migrations from YAML files."""

    def test_load_valid_migration_file(self):
        """Test loading a valid migration YAML file."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            migration_data = {
                "version": "20250115_120000",
                "description": "Test migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "abc123",
                "changes": {"entities": [], "relations": []},
                "up": ["CREATE CONSTRAINT test_unique FOR (n:Test) REQUIRE n.id IS UNIQUE"],
                "down": ["DROP CONSTRAINT test_unique"],
            }

            filepath = migrations_dir / "20250115_120000_test.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            migration = executor._load_migration_from_file(filepath)

            assert migration is not None
            assert migration.version == "20250115_120000"
            assert migration.description == "Test migration"
            assert len(migration.up_cypher) == 1
            assert len(migration.down_cypher) == 1

    def test_load_invalid_migration_file_returns_none(self):
        """Test that invalid migration file returns None."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Invalid YAML
            filepath = migrations_dir / "invalid.yml"
            with open(filepath, "w") as f:
                f.write("invalid: yaml: content: [")

            executor = MigrationExecutor(driver, project_root)
            migration = executor._load_migration_from_file(filepath)

            assert migration is None

    def test_load_migration_file_missing_fields_returns_none(self):
        """Test that migration file with missing required fields returns None."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Missing version field
            migration_data = {"description": "Test migration"}
            filepath = migrations_dir / "incomplete.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            migration = executor._load_migration_from_file(filepath)

            assert migration is None


class TestLoadAllMigrations:
    """Tests for loading all migrations."""

    def test_load_all_migrations_empty_dir(self):
        """Test loading from empty migrations directory."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            executor = MigrationExecutor(driver, project_root)
            migrations = executor._load_all_migrations()

            assert migrations == []

    def test_load_all_migrations_multiple_files(self):
        """Test loading multiple migration files in order."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Create multiple migration files
            for i, version in enumerate(["20250115_120000", "20250115_130000", "20250116_100000"]):
                migration_data = {
                    "version": version,
                    "description": f"Migration {i + 1}",
                    "author": "test",
                    "timestamp": "2025-01-15T12:00:00",
                    "checksum": f"checksum{i}",
                    "changes": {"entities": [], "relations": []},
                    "up": [],
                    "down": [],
                }
                filepath = migrations_dir / f"{version}_migration_{i}.yml"
                with open(filepath, "w") as f:
                    yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            migrations = executor._load_all_migrations()

            assert len(migrations) == 3
            # Should be sorted by filename (version)
            assert migrations[0].version == "20250115_120000"
            assert migrations[1].version == "20250115_130000"
            assert migrations[2].version == "20250116_100000"


class TestLoadMigration:
    """Tests for loading a specific migration by version."""

    def test_load_migration_found(self):
        """Test loading a specific migration that exists."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            migration_data = {
                "version": "20250115_120000",
                "description": "Target migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "abc123",
                "changes": {"entities": [], "relations": []},
                "up": ["CYPHER UP"],
                "down": ["CYPHER DOWN"],
            }
            filepath = migrations_dir / "20250115_120000_target.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            migration = executor._load_migration("20250115_120000")

            assert migration is not None
            assert migration.version == "20250115_120000"
            assert migration.description == "Target migration"

    def test_load_migration_not_found(self):
        """Test loading a migration that doesn't exist."""
        driver, _ = create_mock_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            executor = MigrationExecutor(driver, project_root)
            migration = executor._load_migration("nonexistent_version")

            assert migration is None


class TestGetAppliedVersions:
    """Tests for getting applied migration versions from Neo4j."""

    def test_get_applied_versions(self):
        """Test getting applied versions from database."""
        driver, session = create_mock_driver()

        # Mock the query result
        mock_result = [
            {"version": "20250115_120000"},
            {"version": "20250115_130000"},
        ]
        session.run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = MigrationExecutor(driver, Path(tmpdir))
            versions = executor._get_applied_versions()

            assert versions == {"20250115_120000", "20250115_130000"}

    def test_get_applied_versions_empty(self):
        """Test getting versions when none are applied."""
        driver, session = create_mock_driver()
        session.run.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = MigrationExecutor(driver, Path(tmpdir))
            versions = executor._get_applied_versions()

            assert versions == set()


class TestGetPendingMigrations:
    """Tests for getting pending migrations."""

    def test_get_pending_migrations(self):
        """Test getting pending migrations filters applied ones."""
        driver, session = create_mock_driver()

        # Mock applied versions
        session.run.return_value = [{"version": "20250115_120000"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Create migration files
            for version in ["20250115_120000", "20250115_130000"]:
                migration_data = {
                    "version": version,
                    "description": f"Migration {version}",
                    "author": "test",
                    "timestamp": "2025-01-15T12:00:00",
                    "checksum": "abc",
                    "changes": {"entities": [], "relations": []},
                    "up": [],
                    "down": [],
                }
                filepath = migrations_dir / f"{version}_test.yml"
                with open(filepath, "w") as f:
                    yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            pending = executor.get_pending_migrations()

            # Only the second migration should be pending
            assert len(pending) == 1
            assert pending[0].version == "20250115_130000"


class TestGetMigrationHistory:
    """Tests for getting migration history from Neo4j."""

    def test_get_migration_history(self):
        """Test getting migration history."""
        driver, session = create_mock_driver()

        # Mock history records
        mock_records = [
            {
                "version": "20250115_120000",
                "description": "First migration",
                "applied_at": datetime(2025, 1, 15, 12, 0, 0),
                "status": "applied",
                "checksum": "abc123",
                "execution_time_ms": 150,
                "error_message": None,
            },
            {
                "version": "20250115_130000",
                "description": "Second migration",
                "applied_at": datetime(2025, 1, 15, 13, 0, 0),
                "status": "applied",
                "checksum": "def456",
                "execution_time_ms": 200,
                "error_message": None,
            },
        ]

        # Create mock records that support .get()
        mock_result = []
        for record in mock_records:
            mock_record = MagicMock()
            mock_record.__getitem__ = lambda self, key, r=record: r[key]
            mock_record.get = lambda key, default=None, r=record: r.get(key, default)
            mock_result.append(mock_record)

        session.run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = MigrationExecutor(driver, Path(tmpdir))
            history = executor.get_migration_history()

            assert len(history) == 2
            assert history[0].version == "20250115_120000"
            assert history[0].status == MigrationStatus.APPLIED
            assert history[1].version == "20250115_130000"


class TestApplyMigration:
    """Tests for applying a migration."""

    def test_apply_migration_success(self):
        """Test successful migration application."""
        driver, session = create_mock_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = MigrationExecutor(driver, Path(tmpdir))

            migration = Migration(
                version="20250115_120000",
                description="Test migration",
                changes=SchemaChanges(entities=[], relations=[]),
                up_cypher=["CREATE (n:Test {id: 1})"],
                down_cypher=["MATCH (n:Test) DELETE n"],
                checksum="abc123",
            )

            result = executor.apply_migration(migration)

            assert result.version == "20250115_120000"
            assert result.status == MigrationStatus.APPLIED
            assert result.checksum == "abc123"

            # Verify Cypher was executed
            session.run.assert_called()

    def test_apply_migration_dry_run(self):
        """Test dry run doesn't execute Cypher."""
        driver, session = create_mock_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = MigrationExecutor(driver, Path(tmpdir))

            migration = Migration(
                version="20250115_120000",
                description="Test migration",
                changes=SchemaChanges(entities=[], relations=[]),
                up_cypher=["CREATE (n:Test {id: 1})"],
                checksum="abc123",
            )

            result = executor.apply_migration(migration, dry_run=True)

            assert result.version == "20250115_120000"
            assert result.status == MigrationStatus.APPLIED
            assert result.execution_time_ms == 0

            # Verify session was not used
            driver.session.assert_not_called()

    def test_apply_migration_failure(self):
        """Test migration failure handling."""
        driver, session = create_mock_driver()
        session.run.side_effect = Exception("Database error")

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = MigrationExecutor(driver, Path(tmpdir))

            migration = Migration(
                version="20250115_120000",
                description="Failing migration",
                changes=SchemaChanges(entities=[], relations=[]),
                up_cypher=["INVALID CYPHER"],
                checksum="abc123",
            )

            with pytest.raises(Exception, match="Database error"):
                executor.apply_migration(migration)


class TestApplyAllPending:
    """Tests for applying all pending migrations."""

    def test_apply_all_pending(self):
        """Test applying multiple pending migrations."""
        driver, session = create_mock_driver()
        session.run.return_value = []  # No applied migrations

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Create two migration files
            for i, version in enumerate(["20250115_120000", "20250115_130000"]):
                migration_data = {
                    "version": version,
                    "description": f"Migration {i + 1}",
                    "author": "test",
                    "timestamp": "2025-01-15T12:00:00",
                    "checksum": f"checksum{i}",
                    "changes": {"entities": [], "relations": []},
                    "up": [f"CREATE (n:Test{i})"],
                    "down": [f"MATCH (n:Test{i}) DELETE n"],
                }
                filepath = migrations_dir / f"{version}_migration.yml"
                with open(filepath, "w") as f:
                    yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            results = executor.apply_all_pending()

            assert len(results) == 2
            assert results[0].version == "20250115_120000"
            assert results[1].version == "20250115_130000"

    def test_apply_all_pending_dry_run(self):
        """Test dry run of all pending migrations."""
        driver, session = create_mock_driver()
        session.run.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            migration_data = {
                "version": "20250115_120000",
                "description": "Test migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "abc",
                "changes": {"entities": [], "relations": []},
                "up": ["CREATE (n:Test)"],
                "down": [],
            }
            filepath = migrations_dir / "20250115_120000_test.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            results = executor.apply_all_pending(dry_run=True)

            assert len(results) == 1
            assert results[0].execution_time_ms == 0


class TestRollbackMigration:
    """Tests for rolling back migrations."""

    def test_rollback_last_migration(self):
        """Test rolling back the last applied migration."""
        driver, session = create_mock_driver()

        # Mock history
        mock_record = MagicMock()
        mock_record.__getitem__ = lambda self, key: {
            "version": "20250115_120000",
            "description": "Test migration",
            "applied_at": datetime(2025, 1, 15, 12, 0, 0),
            "status": "applied",
            "checksum": "abc123",
            "execution_time_ms": 100,
            "error_message": None,
        }[key]
        mock_record.get = lambda key, default=None: {
            "execution_time_ms": 100,
            "error_message": None,
        }.get(key, default)

        session.run.return_value = [mock_record]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Create migration file
            migration_data = {
                "version": "20250115_120000",
                "description": "Test migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "abc123",
                "changes": {"entities": [], "relations": []},
                "up": ["CREATE (n:Test)"],
                "down": ["MATCH (n:Test) DELETE n"],
            }
            filepath = migrations_dir / "20250115_120000_test.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            result = executor.rollback_migration()

            assert result.version == "20250115_120000"
            assert result.status == MigrationStatus.ROLLED_BACK

    def test_rollback_specific_version(self):
        """Test rolling back a specific version."""
        driver, session = create_mock_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            migration_data = {
                "version": "20250115_120000",
                "description": "Specific migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "abc123",
                "changes": {"entities": [], "relations": []},
                "up": ["CREATE (n:Test)"],
                "down": ["MATCH (n:Test) DELETE n"],
            }
            filepath = migrations_dir / "20250115_120000_specific.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            result = executor.rollback_migration(version="20250115_120000")

            assert result.version == "20250115_120000"
            assert result.status == MigrationStatus.ROLLED_BACK

    def test_rollback_no_migrations_raises_error(self):
        """Test rollback with no migrations raises error."""
        driver, session = create_mock_driver()
        session.run.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "migrations").mkdir()

            executor = MigrationExecutor(driver, project_root)

            with pytest.raises(ValueError, match="No migrations to rollback"):
                executor.rollback_migration()

    def test_rollback_migration_not_found_raises_error(self):
        """Test rollback with nonexistent version raises error."""
        driver, session = create_mock_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "migrations").mkdir()

            executor = MigrationExecutor(driver, project_root)

            with pytest.raises(ValueError, match="not found"):
                executor.rollback_migration(version="nonexistent")


class TestVerifyMigrations:
    """Tests for migration verification."""

    def test_verify_migrations_consistent(self):
        """Test verification when all migrations are consistent."""
        driver, session = create_mock_driver()

        # Mock applied history
        mock_record = MagicMock()
        mock_record.__getitem__ = lambda self, key: {
            "version": "20250115_120000",
            "description": "Test migration",
            "applied_at": datetime(2025, 1, 15, 12, 0, 0),
            "status": "applied",
            "checksum": "abc123",
            "execution_time_ms": 100,
            "error_message": None,
        }[key]
        mock_record.get = lambda key, default=None: {
            "execution_time_ms": 100,
            "error_message": None,
        }.get(key, default)

        session.run.return_value = [mock_record]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Create matching migration file
            migration_data = {
                "version": "20250115_120000",
                "description": "Test migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "abc123",
                "changes": {"entities": [], "relations": []},
                "up": [],
                "down": [],
            }
            filepath = migrations_dir / "20250115_120000_test.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            result = executor.verify_migrations()

            assert result is True

    def test_verify_migrations_missing_file(self):
        """Test verification fails when migration file is missing."""
        driver, session = create_mock_driver()

        # Mock applied history with version that has no file
        mock_record = MagicMock()
        mock_record.__getitem__ = lambda self, key: {
            "version": "20250115_120000",
            "description": "Missing file",
            "applied_at": datetime(2025, 1, 15, 12, 0, 0),
            "status": "applied",
            "checksum": "abc123",
            "execution_time_ms": 100,
            "error_message": None,
        }[key]
        mock_record.get = lambda key, default=None: {
            "execution_time_ms": 100,
            "error_message": None,
        }.get(key, default)

        session.run.return_value = [mock_record]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "migrations").mkdir()

            executor = MigrationExecutor(driver, project_root)
            result = executor.verify_migrations()

            assert result is False

    def test_verify_migrations_checksum_mismatch(self):
        """Test verification fails when checksum doesn't match."""
        driver, session = create_mock_driver()

        mock_record = MagicMock()
        mock_record.__getitem__ = lambda self, key: {
            "version": "20250115_120000",
            "description": "Test migration",
            "applied_at": datetime(2025, 1, 15, 12, 0, 0),
            "status": "applied",
            "checksum": "original_checksum",
            "execution_time_ms": 100,
            "error_message": None,
        }[key]
        mock_record.get = lambda key, default=None: {
            "execution_time_ms": 100,
            "error_message": None,
        }.get(key, default)

        session.run.return_value = [mock_record]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            migrations_dir = project_root / "migrations"
            migrations_dir.mkdir()

            # Create migration file with different checksum
            migration_data = {
                "version": "20250115_120000",
                "description": "Test migration",
                "author": "test",
                "timestamp": "2025-01-15T12:00:00",
                "checksum": "modified_checksum",
                "changes": {"entities": [], "relations": []},
                "up": [],
                "down": [],
            }
            filepath = migrations_dir / "20250115_120000_test.yml"
            with open(filepath, "w") as f:
                yaml.safe_dump(migration_data, f)

            executor = MigrationExecutor(driver, project_root)
            result = executor.verify_migrations()

            assert result is False

"""
Tests for build cache functionality.

Tests incremental build caching, file hash tracking, and change detection.
"""

from datetime import UTC, datetime

import pytest

from grai.core.cache import (
    BuildCache,
    CacheEntry,
    clear_cache,
    compute_file_hash,
    get_cache_path,
    get_changed_files,
    is_file_modified,
    load_cache,
    save_cache,
    should_rebuild,
    update_cache,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory with sample files."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create grai.yml
    (project_dir / "grai.yml").write_text(
        """name: test-project
version: 1.0.0
"""
    )

    # Create entities directory
    entities_dir = project_dir / "entities"
    entities_dir.mkdir()

    (entities_dir / "customer.yml").write_text(
        """entity: customer
source: customers
keys: [id]
properties:
  - name: name
    type: string
"""
    )

    # Create relations directory
    relations_dir = project_dir / "relations"
    relations_dir.mkdir()

    (relations_dir / "purchased.yml").write_text(
        """relation: PURCHASED
from: customer
to: product
source: orders
"""
    )

    return project_dir


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_compute_hash_success(self, tmp_path):
        """Test computing hash of a file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!")

        hash_value = compute_file_hash(file_path)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters

    def test_compute_hash_consistent(self, tmp_path):
        """Test that hash is consistent for same content."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Same content")

        hash1 = compute_file_hash(file_path)
        hash2 = compute_file_hash(file_path)

        assert hash1 == hash2

    def test_compute_hash_different_content(self, tmp_path):
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("Content A")
        file2.write_text("Content B")

        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)

        assert hash1 != hash2

    def test_compute_hash_file_not_found(self, tmp_path):
        """Test error when file doesn't exist."""
        file_path = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_hash(file_path)


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            path="entities/customer.yml",
            hash="abc123",
            last_modified="2025-10-14T12:00:00Z",
            size=1024,
        )

        assert entry.path == "entities/customer.yml"
        assert entry.hash == "abc123"
        assert entry.size == 1024
        assert entry.dependencies == []

    def test_cache_entry_to_dict(self):
        """Test converting cache entry to dict."""
        entry = CacheEntry(
            path="test.yml",
            hash="def456",
            last_modified="2025-10-14T12:00:00Z",
            size=512,
            dependencies=["dep1.yml"],
        )

        data = entry.to_dict()

        assert data["path"] == "test.yml"
        assert data["hash"] == "def456"
        assert data["size"] == 512
        assert data["dependencies"] == ["dep1.yml"]

    def test_cache_entry_from_dict(self):
        """Test creating cache entry from dict."""
        data = {
            "path": "test.yml",
            "hash": "ghi789",
            "last_modified": "2025-10-14T12:00:00Z",
            "size": 256,
            "dependencies": [],
        }

        entry = CacheEntry.from_dict(data)

        assert entry.path == "test.yml"
        assert entry.hash == "ghi789"
        assert entry.size == 256


class TestBuildCache:
    """Tests for BuildCache dataclass."""

    def test_build_cache_creation(self):
        """Test creating a build cache."""
        cache = BuildCache()

        assert cache.version == "1.0.0"
        assert isinstance(cache.entries, dict)
        assert len(cache.entries) == 0

    def test_build_cache_with_entries(self):
        """Test build cache with entries."""
        entry = CacheEntry(
            path="test.yml",
            hash="abc",
            last_modified="2025-10-14T12:00:00Z",
            size=100,
        )

        cache = BuildCache(entries={"test.yml": entry})

        assert "test.yml" in cache.entries
        assert cache.entries["test.yml"].hash == "abc"

    def test_build_cache_to_dict(self):
        """Test converting build cache to dict."""
        entry = CacheEntry(
            path="test.yml",
            hash="xyz",
            last_modified="2025-10-14T12:00:00Z",
            size=200,
        )

        cache = BuildCache(
            project_name="test-project",
            project_version="1.0.0",
            entries={"test.yml": entry},
        )

        data = cache.to_dict()

        assert data["version"] == "1.0.0"
        assert data["project_name"] == "test-project"
        assert "test.yml" in data["entries"]

    def test_build_cache_from_dict(self):
        """Test creating build cache from dict."""
        data = {
            "version": "1.0.0",
            "created_at": "2025-10-14T10:00:00Z",
            "last_updated": "2025-10-14T12:00:00Z",
            "project_name": "my-project",
            "project_version": "2.0.0",
            "entries": {
                "test.yml": {
                    "path": "test.yml",
                    "hash": "aaa",
                    "last_modified": "2025-10-14T12:00:00Z",
                    "size": 150,
                    "dependencies": [],
                }
            },
        }

        cache = BuildCache.from_dict(data)

        assert cache.version == "1.0.0"
        assert cache.project_name == "my-project"
        assert "test.yml" in cache.entries


class TestCachePersistence:
    """Tests for cache loading and saving."""

    def test_get_cache_path(self, tmp_path):
        """Test getting cache file path."""
        path = get_cache_path(tmp_path)

        assert path == tmp_path / ".grai" / "cache.json"

    def test_save_and_load_cache(self, tmp_path):
        """Test saving and loading cache."""
        entry = CacheEntry(
            path="test.yml",
            hash="save_test",
            last_modified="2025-10-14T12:00:00Z",
            size=500,
        )

        cache = BuildCache(
            project_name="test",
            entries={"test.yml": entry},
        )

        # Save cache
        save_cache(cache, tmp_path)

        # Load cache
        loaded_cache = load_cache(tmp_path)

        assert loaded_cache is not None
        assert loaded_cache.project_name == "test"
        assert "test.yml" in loaded_cache.entries
        assert loaded_cache.entries["test.yml"].hash == "save_test"

    def test_load_cache_not_found(self, tmp_path):
        """Test loading cache when file doesn't exist."""
        cache = load_cache(tmp_path)

        assert cache is None

    def test_load_cache_invalid_json(self, tmp_path):
        """Test loading cache with invalid JSON."""
        cache_path = get_cache_path(tmp_path)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("invalid json{")

        cache = load_cache(tmp_path)

        assert cache is None

    def test_clear_cache_success(self, tmp_path):
        """Test clearing cache."""
        # Create cache
        cache = BuildCache()
        save_cache(cache, tmp_path)

        # Clear cache
        result = clear_cache(tmp_path)

        assert result is True
        assert not get_cache_path(tmp_path).exists()

    def test_clear_cache_not_found(self, tmp_path):
        """Test clearing cache when none exists."""
        result = clear_cache(tmp_path)

        assert result is False


class TestFileModification:
    """Tests for file modification detection."""

    def test_is_file_modified_no_cache(self, tmp_path):
        """Test file is considered modified when no cache exists."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        is_modified = is_file_modified(file_path, None)

        assert is_modified is True

    def test_is_file_modified_unchanged(self, tmp_path):
        """Test file is not modified when hash matches."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        # Create cache entry
        file_hash = compute_file_hash(file_path)
        stat = file_path.stat()

        entry = CacheEntry(
            path="test.txt",
            hash=file_hash,
            last_modified=datetime.now(UTC).isoformat(),
            size=stat.st_size,
        )

        is_modified = is_file_modified(file_path, entry)

        assert is_modified is False

    def test_is_file_modified_content_changed(self, tmp_path):
        """Test file is modified when content changes."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("original")

        # Create cache entry with original hash
        original_hash = compute_file_hash(file_path)
        entry = CacheEntry(
            path="test.txt",
            hash=original_hash,
            last_modified=datetime.now(UTC).isoformat(),
            size=file_path.stat().st_size,
        )

        # Modify file
        file_path.write_text("modified content")

        is_modified = is_file_modified(file_path, entry)

        assert is_modified is True

    def test_is_file_modified_size_changed(self, tmp_path):
        """Test file is modified when size changes."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("short")

        entry = CacheEntry(
            path="test.txt",
            hash="dummy_hash",
            last_modified=datetime.now(UTC).isoformat(),
            size=1000,  # Wrong size
        )

        is_modified = is_file_modified(file_path, entry)

        assert is_modified is True

    def test_is_file_modified_deleted(self, tmp_path):
        """Test deleted file is considered modified."""
        file_path = tmp_path / "deleted.txt"

        entry = CacheEntry(
            path="deleted.txt",
            hash="hash",
            last_modified=datetime.now(UTC).isoformat(),
            size=100,
        )

        is_modified = is_file_modified(file_path, entry)

        assert is_modified is True


class TestChangeDetection:
    """Tests for detecting changed files."""

    def test_get_changed_files_no_cache(self, temp_project):
        """Test all files are new when no cache exists."""
        changes = get_changed_files(temp_project, None)

        assert len(changes["added"]) == 3  # grai.yml, customer.yml, purchased.yml
        assert len(changes["modified"]) == 0
        assert len(changes["deleted"]) == 0

    def test_get_changed_files_no_changes(self, temp_project):
        """Test no changes when cache is current."""
        # Create cache
        cache = update_cache(temp_project)

        # Check for changes
        changes = get_changed_files(temp_project, cache)

        assert len(changes["added"]) == 0
        assert len(changes["modified"]) == 0
        assert len(changes["deleted"]) == 0

    def test_get_changed_files_modified(self, temp_project):
        """Test detecting modified files."""
        # Create cache
        cache = update_cache(temp_project)

        # Modify a file
        (temp_project / "entities" / "customer.yml").write_text(
            """entity: customer
source: customers_v2
keys: [id]
"""
        )

        # Check for changes
        changes = get_changed_files(temp_project, cache)

        assert len(changes["modified"]) == 1
        assert len(changes["added"]) == 0
        assert len(changes["deleted"]) == 0

    def test_get_changed_files_added(self, temp_project):
        """Test detecting added files."""
        # Create cache
        cache = update_cache(temp_project)

        # Add new file
        (temp_project / "entities" / "product.yml").write_text(
            """entity: product
source: products
keys: [id]
"""
        )

        # Check for changes
        changes = get_changed_files(temp_project, cache)

        assert len(changes["added"]) == 1
        assert len(changes["modified"]) == 0
        assert len(changes["deleted"]) == 0

    def test_get_changed_files_deleted(self, temp_project):
        """Test detecting deleted files."""
        # Create cache
        cache = update_cache(temp_project)

        # Delete a file
        (temp_project / "relations" / "purchased.yml").unlink()

        # Check for changes
        changes = get_changed_files(temp_project, cache)

        assert len(changes["deleted"]) == 1
        assert len(changes["added"]) == 0
        assert len(changes["modified"]) == 0


class TestShouldRebuild:
    """Tests for should_rebuild function."""

    def test_should_rebuild_no_cache(self, temp_project):
        """Test rebuild needed when no cache exists."""
        needs_rebuild, changes = should_rebuild(temp_project)

        assert needs_rebuild is True
        assert len(changes["added"]) > 0

    def test_should_rebuild_no_changes(self, temp_project):
        """Test no rebuild when nothing changed."""
        # Create cache
        update_cache(temp_project)

        # Check rebuild
        needs_rebuild, changes = should_rebuild(temp_project)

        assert needs_rebuild is False
        assert len(changes["added"]) == 0
        assert len(changes["modified"]) == 0

    def test_should_rebuild_with_changes(self, temp_project):
        """Test rebuild needed when files change."""
        # Create cache
        update_cache(temp_project)

        # Modify file
        (temp_project / "grai.yml").write_text("name: updated\nversion: 2.0.0\n")

        # Check rebuild
        needs_rebuild, changes = should_rebuild(temp_project)

        assert needs_rebuild is True
        assert len(changes["modified"]) > 0


class TestUpdateCache:
    """Tests for update_cache function."""

    def test_update_cache_creates_new(self, temp_project):
        """Test creating new cache."""
        cache = update_cache(temp_project, "test-project", "1.0.0")

        assert cache.project_name == "test-project"
        assert cache.project_version == "1.0.0"
        assert len(cache.entries) == 3  # grai.yml, customer.yml, purchased.yml

    def test_update_cache_saves_to_disk(self, temp_project):
        """Test cache is saved to disk."""
        update_cache(temp_project)

        cache_path = get_cache_path(temp_project)
        assert cache_path.exists()

        # Load and verify
        loaded = load_cache(temp_project)
        assert loaded is not None
        assert len(loaded.entries) == 3

    def test_update_cache_replaces_old(self, temp_project):
        """Test updating existing cache."""
        # Create initial cache
        update_cache(temp_project, "old-name", "1.0.0")

        # Update cache
        cache2 = update_cache(temp_project, "new-name", "2.0.0")

        assert cache2.project_name == "new-name"
        assert cache2.project_version == "2.0.0"

    def test_update_cache_includes_all_files(self, temp_project):
        """Test cache includes all project files."""
        cache = update_cache(temp_project)

        # Check that all expected files are cached
        paths = set(cache.entries.keys())
        assert "grai.yml" in paths
        assert "entities/customer.yml" in paths
        assert "relations/purchased.yml" in paths

    def test_update_cache_correct_hashes(self, temp_project):
        """Test cache contains correct file hashes."""
        cache = update_cache(temp_project)

        # Verify hash for grai.yml
        grai_file = temp_project / "grai.yml"
        expected_hash = compute_file_hash(grai_file)

        assert cache.entries["grai.yml"].hash == expected_hash


class TestCacheIntegration:
    """Integration tests for cache functionality."""

    def test_full_workflow(self, temp_project):
        """Test complete cache workflow."""
        # 1. Initial build - no cache
        needs_rebuild, changes = should_rebuild(temp_project)
        assert needs_rebuild is True

        # 2. Update cache after build
        cache = update_cache(temp_project, "test", "1.0.0")
        assert len(cache.entries) == 3

        # 3. Check rebuild - should be up to date
        needs_rebuild, changes = should_rebuild(temp_project)
        assert needs_rebuild is False

        # 4. Modify a file
        (temp_project / "entities" / "customer.yml").write_text("modified")

        # 5. Check rebuild - should need rebuild
        needs_rebuild, changes = should_rebuild(temp_project)
        assert needs_rebuild is True
        assert len(changes["modified"]) == 1

        # 6. Update cache again
        cache = update_cache(temp_project)

        # 7. Check rebuild - should be up to date again
        needs_rebuild, changes = should_rebuild(temp_project)
        assert needs_rebuild is False

    def test_cache_persistence_across_loads(self, temp_project):
        """Test cache persists across program runs."""
        # Create and save cache
        cache1 = update_cache(temp_project, "persistent", "1.0.0")

        # Simulate program restart - load cache
        cache2 = load_cache(temp_project)

        assert cache2 is not None
        assert cache2.project_name == "persistent"
        assert len(cache2.entries) == len(cache1.entries)

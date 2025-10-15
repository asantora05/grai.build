"""
Build cache for incremental compilation.

This module provides functionality to track file changes and enable fast incremental builds
by computing file hashes and comparing them against cached values.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class CacheEntry:
    """
    Represents a cached file entry with metadata.

    Attributes:
        path: Relative path to the file
        hash: SHA256 hash of file contents
        last_modified: Timestamp of last modification
        size: File size in bytes
        dependencies: List of files this file depends on
    """

    path: str
    hash: str
    last_modified: str
    size: int
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create CacheEntry from dictionary."""
        return cls(**data)


@dataclass
class BuildCache:
    """
    Build cache containing file hashes and metadata.

    Attributes:
        version: Cache format version
        created_at: Cache creation timestamp
        last_updated: Last update timestamp
        entries: Dictionary mapping file paths to cache entries
        project_name: Name of the project
        project_version: Version of the project
    """

    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    entries: Dict[str, CacheEntry] = field(default_factory=dict)
    project_name: Optional[str] = None
    project_version: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "entries": {path: entry.to_dict() for path, entry in self.entries.items()},
            "project_name": self.project_name,
            "project_version": self.project_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BuildCache":
        """Create BuildCache from dictionary."""
        entries = {
            path: CacheEntry.from_dict(entry_data)
            for path, entry_data in data.get("entries", {}).items()
        }
        return cls(
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", datetime.now(UTC).isoformat()),
            last_updated=data.get("last_updated", datetime.now(UTC).isoformat()),
            entries=entries,
            project_name=data.get("project_name"),
            project_version=data.get("project_version"),
        )


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal SHA256 hash string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for memory efficiency
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_cache_path(project_dir: Path) -> Path:
    """
    Get the path to the cache file for a project.

    Args:
        project_dir: Project directory

    Returns:
        Path to .grai/cache.json
    """
    return project_dir / ".grai" / "cache.json"


def load_cache(project_dir: Path) -> Optional[BuildCache]:
    """
    Load build cache from disk.

    Args:
        project_dir: Project directory

    Returns:
        BuildCache if cache exists and is valid, None otherwise
    """
    cache_path = get_cache_path(project_dir)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)
        return BuildCache.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError):
        # Invalid cache, return None
        return None


def save_cache(cache: BuildCache, project_dir: Path) -> None:
    """
    Save build cache to disk.

    Args:
        cache: BuildCache to save
        project_dir: Project directory
    """
    cache_path = get_cache_path(project_dir)

    # Create .grai directory if it doesn't exist
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Update last_updated timestamp
    cache.last_updated = datetime.now(UTC).isoformat()

    # Write cache
    with open(cache_path, "w") as f:
        json.dump(cache.to_dict(), f, indent=2)


def clear_cache(project_dir: Path) -> bool:
    """
    Clear the build cache.

    Args:
        project_dir: Project directory

    Returns:
        True if cache was deleted, False if no cache existed
    """
    cache_path = get_cache_path(project_dir)

    if cache_path.exists():
        cache_path.unlink()
        return True

    return False


def is_file_modified(file_path: Path, cache_entry: Optional[CacheEntry]) -> bool:
    """
    Check if a file has been modified since last cache.

    Args:
        file_path: Path to the file
        cache_entry: Cache entry for the file (None if not cached)

    Returns:
        True if file is new or modified, False if unchanged
    """
    # If no cache entry, file is new
    if cache_entry is None:
        return True

    # If file doesn't exist, it was deleted
    if not file_path.exists():
        return True

    # Check if size changed (fast check)
    stat = file_path.stat()
    if stat.st_size != cache_entry.size:
        return True

    # Compute and compare hash
    current_hash = compute_file_hash(file_path)
    return current_hash != cache_entry.hash


def get_changed_files(project_dir: Path, cache: Optional[BuildCache]) -> Dict[str, Set[Path]]:
    """
    Get all files that have changed since last build.

    Args:
        project_dir: Project directory
        cache: Build cache (None for first build)

    Returns:
        Dictionary with keys: 'added', 'modified', 'deleted' mapping to sets of file paths
    """
    changes: Dict[str, Set[Path]] = {
        "added": set(),
        "modified": set(),
        "deleted": set(),
    }

    # If no cache, all files are new
    if cache is None:
        # Find all YAML files
        for pattern in ["entities/*.yml", "relations/*.yml", "grai.yml"]:
            for file_path in project_dir.glob(pattern):
                if file_path.is_file():
                    changes["added"].add(file_path)
        return changes

    # Track seen files
    seen_files: Set[str] = set()

    # Check all current files
    for pattern in ["entities/*.yml", "relations/*.yml", "grai.yml"]:
        for file_path in project_dir.glob(pattern):
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(project_dir))
            seen_files.add(rel_path)

            cache_entry = cache.entries.get(rel_path)

            if cache_entry is None:
                changes["added"].add(file_path)
            elif is_file_modified(file_path, cache_entry):
                changes["modified"].add(file_path)

    # Check for deleted files
    for cached_path in cache.entries.keys():
        if cached_path not in seen_files:
            changes["deleted"].add(project_dir / cached_path)

    return changes


def should_rebuild(
    project_dir: Path, cache: Optional[BuildCache] = None
) -> tuple[bool, Dict[str, Set[Path]]]:
    """
    Determine if project needs to be rebuilt.

    Args:
        project_dir: Project directory
        cache: Build cache (will load from disk if None)

    Returns:
        Tuple of (should_rebuild: bool, changes: Dict[str, Set[Path]])
    """
    # Load cache if not provided
    if cache is None:
        cache = load_cache(project_dir)

    # Get changed files
    changes = get_changed_files(project_dir, cache)

    # Rebuild if any changes
    has_changes = any(len(files) > 0 for files in changes.values())

    return has_changes, changes


def update_cache(
    project_dir: Path, project_name: Optional[str] = None, project_version: Optional[str] = None
) -> BuildCache:
    """
    Update cache with current file hashes.

    Args:
        project_dir: Project directory
        project_name: Project name (optional)
        project_version: Project version (optional)

    Returns:
        Updated BuildCache
    """
    # Load existing cache or create new one
    cache = load_cache(project_dir) or BuildCache()

    # Update project info if provided
    if project_name:
        cache.project_name = project_name
    if project_version:
        cache.project_version = project_version

    # Clear old entries
    cache.entries.clear()

    # Add all current files
    for pattern in ["entities/*.yml", "relations/*.yml", "grai.yml"]:
        for file_path in project_dir.glob(pattern):
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(project_dir))
            stat = file_path.stat()

            # Create cache entry
            entry = CacheEntry(
                path=rel_path,
                hash=compute_file_hash(file_path),
                last_modified=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                size=stat.st_size,
            )

            cache.entries[rel_path] = entry

    # Save cache
    save_cache(cache, project_dir)

    return cache

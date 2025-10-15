"""
Cache module for incremental builds.

Exports cache management functions for tracking file changes and build artifacts.
"""

from .build_cache import (
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

__all__ = [
    "BuildCache",
    "CacheEntry",
    "compute_file_hash",
    "should_rebuild",
    "get_cache_path",
    "load_cache",
    "save_cache",
    "clear_cache",
    "get_changed_files",
    "is_file_modified",
    "update_cache",
]

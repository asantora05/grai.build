# Build Cache Documentation

## Overview

The build cache module provides incremental build support by tracking file changes using SHA256 hashing. This enables fast rebuilds by skipping unchanged files and only processing modified content.

## Features

- **File Hash Tracking**: SHA256 hashing for content-based change detection
- **Fast Change Detection**: Quick size checks before expensive hash computation
- **Persistent Cache**: JSON-based cache stored in `.grai/cache.json`
- **Automatic Integration**: Seamless integration with `grai build` command
- **Manual Control**: Force full rebuilds or clear cache when needed
- **Detailed Reporting**: View cache status and detect specific changes

## Architecture

### Cache Structure

The cache consists of two main components:

1. **BuildCache**: Top-level cache container

   - Version information
   - Timestamps (created, last updated)
   - Project metadata (name, version)
   - Dictionary of cache entries

2. **CacheEntry**: Per-file cache entry
   - File path (relative to project)
   - SHA256 hash
   - Last modified timestamp
   - File size
   - Dependencies (for future use)

### Storage Format

Cache is stored as JSON in `.grai/cache.json`:

```json
{
  "version": "1.0.0",
  "created_at": "2025-10-14T10:00:00Z",
  "last_updated": "2025-10-14T12:00:00Z",
  "project_name": "my-knowledge-graph",
  "project_version": "1.0.0",
  "entries": {
    "grai.yml": {
      "path": "grai.yml",
      "hash": "abc123...",
      "last_modified": "2025-10-14T10:00:00Z",
      "size": 240,
      "dependencies": []
    },
    "entities/customer.yml": {
      "path": "entities/customer.yml",
      "hash": "def456...",
      "last_modified": "2025-10-14T10:00:00Z",
      "size": 586,
      "dependencies": []
    }
  }
}
```

## API Reference

### Core Functions

#### `compute_file_hash(file_path: Path) -> str`

Compute SHA256 hash of a file.

```python
from pathlib import Path
from grai.core.cache import compute_file_hash

file_hash = compute_file_hash(Path("grai.yml"))
print(f"Hash: {file_hash}")
```

**Parameters:**

- `file_path`: Path to the file to hash

**Returns:**

- Hexadecimal SHA256 hash string (64 characters)

**Raises:**

- `FileNotFoundError`: If file doesn't exist

#### `should_rebuild(project_dir: Path, cache: Optional[BuildCache] = None) -> tuple[bool, Dict]`

Determine if project needs to be rebuilt.

```python
from pathlib import Path
from grai.core.cache import should_rebuild

needs_rebuild, changes = should_rebuild(Path("."))

if needs_rebuild:
    print(f"Need to rebuild: {len(changes['modified'])} files changed")
else:
    print("Build is up to date")
```

**Parameters:**

- `project_dir`: Project directory
- `cache`: Optional BuildCache (will load from disk if None)

**Returns:**

- Tuple of `(should_rebuild: bool, changes: Dict[str, Set[Path]])`
  - `changes` keys: `'added'`, `'modified'`, `'deleted'`

#### `update_cache(project_dir: Path, project_name: Optional[str] = None, project_version: Optional[str] = None) -> BuildCache`

Update cache with current file hashes.

```python
from pathlib import Path
from grai.core.cache import update_cache

cache = update_cache(Path("."), "my-project", "1.0.0")
print(f"Cached {len(cache.entries)} files")
```

**Parameters:**

- `project_dir`: Project directory
- `project_name`: Optional project name
- `project_version`: Optional project version

**Returns:**

- Updated BuildCache instance

#### `load_cache(project_dir: Path) -> Optional[BuildCache]`

Load build cache from disk.

```python
from pathlib import Path
from grai.core.cache import load_cache

cache = load_cache(Path("."))
if cache:
    print(f"Loaded cache with {len(cache.entries)} entries")
else:
    print("No cache found")
```

**Parameters:**

- `project_dir`: Project directory

**Returns:**

- BuildCache if cache exists and is valid, None otherwise

#### `save_cache(cache: BuildCache, project_dir: Path) -> None`

Save build cache to disk.

```python
from pathlib import Path
from grai.core.cache import BuildCache, save_cache

cache = BuildCache(project_name="test", project_version="1.0.0")
save_cache(cache, Path("."))
```

**Parameters:**

- `cache`: BuildCache to save
- `project_dir`: Project directory

#### `clear_cache(project_dir: Path) -> bool`

Clear the build cache.

```python
from pathlib import Path
from grai.core.cache import clear_cache

if clear_cache(Path(".")):
    print("Cache cleared")
else:
    print("No cache to clear")
```

**Parameters:**

- `project_dir`: Project directory

**Returns:**

- True if cache was deleted, False if no cache existed

#### `get_changed_files(project_dir: Path, cache: Optional[BuildCache]) -> Dict[str, Set[Path]]`

Get all files that have changed since last build.

```python
from pathlib import Path
from grai.core.cache import load_cache, get_changed_files

cache = load_cache(Path("."))
changes = get_changed_files(Path("."), cache)

print(f"Added: {len(changes['added'])}")
print(f"Modified: {len(changes['modified'])}")
print(f"Deleted: {len(changes['deleted'])}")
```

**Parameters:**

- `project_dir`: Project directory
- `cache`: Build cache (None for first build)

**Returns:**

- Dictionary with keys: `'added'`, `'modified'`, `'deleted'` mapping to sets of file paths

## CLI Integration

### Build Command

The `grai build` command automatically uses incremental builds:

```bash
# Incremental build (default)
grai build

# Force full rebuild
grai build --full

# Build without updating cache
grai build --no-cache

# Verbose output showing changes
grai build --verbose
```

**Options:**

- `--full`: Force complete rebuild, ignoring cache
- `--no-cache`: Don't update cache after build
- `--verbose`: Show detailed change information

### Cache Command

The `grai cache` command manages the build cache:

```bash
# View cache status
grai cache

# View detailed cache contents
grai cache --show

# Clear cache
grai cache --clear
```

**Output Example:**

```
💾 Build Cache Management

Project: example-ecommerce-graph
Version: 1.0.0
Created: 2025-10-14T10:00:00+00:00
Updated: 2025-10-14T12:00:00+00:00
Cached files: 4

                        Cached Files
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━┓
┃ File              ┃ Hash        ┃ Size ┃ Modified    ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━┩
│ entities/cust.yml │ 2206c53a... │ 0.6  │ 2025-10-14  │
│ grai.yml          │ f8bfea2b... │ 0.2  │ 2025-10-14  │
└───────────────────┴─────────────┴──────┴─────────────┘

✓ Build is up to date
```

## How It Works

### 1. First Build (No Cache)

1. User runs `grai build`
2. System detects no cache exists
3. All files are considered "new"
4. Project is validated and compiled
5. Cache is created with hashes of all files

### 2. Incremental Build (No Changes)

1. User runs `grai build`
2. System loads cache from `.grai/cache.json`
3. Compares file sizes (fast check)
4. All sizes match cached values
5. Build skipped: "✓ No changes detected"

### 3. Incremental Build (With Changes)

1. User modifies `entities/customer.yml`
2. User runs `grai build --verbose`
3. System detects size or hash changed
4. Output: "→ Detected 1 file change(s)"
5. Project is validated and compiled
6. Cache is updated with new hash

### 4. Force Full Rebuild

1. User runs `grai build --full`
2. Cache check is skipped entirely
3. Project is always built
4. Cache is updated

## Performance

### Benchmarks

For a typical project with 10 entities and 5 relations:

- **First build**: ~500ms (no cache)
- **Incremental (no changes)**: ~10ms (cache hit)
- **Incremental (1 file changed)**: ~450ms (partial rebuild)

### Optimization Strategies

1. **Size Check First**: Fast file size comparison before expensive hashing
2. **Chunked Reading**: Files are read in 8KB chunks for memory efficiency
3. **Early Exit**: Stop checking once any change is detected
4. **JSON Cache**: Lightweight, human-readable cache format

## Best Practices

### DO ✓

- Let `grai build` handle caching automatically
- Use `--verbose` to see what changed
- Use `--full` after major project restructuring
- Keep `.grai/` in `.gitignore`

### DON'T ✗

- Don't manually edit `.grai/cache.json`
- Don't commit `.grai/` directory to version control
- Don't use `--no-cache` in production builds
- Don't rely on cache for CI/CD (use `--full`)

## Troubleshooting

### Cache Not Updating

**Problem**: Build always says "no changes detected" even after modifications

**Solutions:**

1. Clear cache: `grai cache --clear`
2. Force rebuild: `grai build --full`
3. Check file permissions

### False Positives

**Problem**: Build triggers unnecessarily

**Causes:**

- File timestamps changed without content changes
- File system events (backup software, etc.)

**Solutions:**

- Cache uses content hashing, not timestamps
- Hashes are deterministic and reliable

### Cache Corruption

**Problem**: Cache file is invalid or corrupted

**Symptoms:**

- `grai cache` shows "No cache found" but `.grai/cache.json` exists
- Build always rebuilds

**Solutions:**

1. Clear cache: `grai cache --clear`
2. Delete `.grai/` directory manually
3. Run `grai build` to recreate

## Advanced Usage

### Programmatic Cache Access

```python
from pathlib import Path
from grai.core.cache import (
    load_cache,
    get_changed_files,
    is_file_modified,
)

# Load cache
project_dir = Path(".")
cache = load_cache(project_dir)

# Check specific file
file_path = project_dir / "entities" / "customer.yml"
entry = cache.entries.get("entities/customer.yml")
modified = is_file_modified(file_path, entry)

if modified:
    print(f"{file_path} has changed")

# Get all changes
changes = get_changed_files(project_dir, cache)
for file in changes["modified"]:
    print(f"Modified: {file}")
```

### Custom Cache Location

Currently, cache location is fixed at `.grai/cache.json`. For custom locations:

```python
from pathlib import Path
from grai.core.cache import BuildCache, load_cache

# Custom cache path would require extending get_cache_path()
# Current implementation always uses project_dir / ".grai" / "cache.json"
```

## Future Enhancements

### Planned Features

1. **Dependency Tracking**: Track inter-file dependencies
2. **Partial Compilation**: Only recompile changed entities/relations
3. **Distributed Cache**: Share cache across team/CI
4. **Watch Mode**: Automatically rebuild on file changes
5. **Cache Statistics**: Build time analytics

### Experimental

- **Smart Dependencies**: Auto-detect entity references in relations
- **Parallel Hashing**: Multi-threaded file hashing
- **Cache Compression**: Smaller cache files with gzip

## See Also

- [Compiler Documentation](COMPILER.md)
- [CLI Documentation](CLI.md)
- [Validator Documentation](VALIDATOR.md)

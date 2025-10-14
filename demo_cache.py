#!/usr/bin/env python3
"""
Demo script for incremental builds with caching.

Demonstrates:
- First build with no cache
- Incremental build with no changes
- Detecting file modifications
- Cache management
- Force full rebuild
"""

from pathlib import Path
from grai.core.parser import load_project
from grai.core.cache import (
    should_rebuild,
    update_cache,
    load_cache,
    clear_cache,
    get_changed_files,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_incremental_builds():
    """Demonstrate incremental builds with caching."""
    project_dir = Path("templates")
    
    if not project_dir.exists():
        print("Error: templates directory not found")
        return
    
    print_section("Incremental Builds Demo")
    print("\nThis demo shows how grai.build tracks file changes for fast rebuilds.\n")
    
    # Step 1: Clear any existing cache
    print_section("1. Clear Existing Cache")
    if clear_cache(project_dir):
        print("✓ Cleared existing cache")
    else:
        print("✓ No cache to clear")
    
    # Step 2: Check if rebuild needed (should be yes, no cache)
    print_section("2. Check Rebuild Status (No Cache)")
    needs_rebuild, changes = should_rebuild(project_dir)
    print(f"Needs rebuild: {needs_rebuild}")
    print(f"New files: {len(changes['added'])}")
    for file in sorted(changes["added"]):
        print(f"  + {file.relative_to(project_dir)}")
    
    # Step 3: Load project and update cache
    print_section("3. Build Project and Create Cache")
    project = load_project(project_dir)
    print(f"Loaded: {project.name} v{project.version}")
    print(f"Entities: {len(project.entities)}")
    print(f"Relations: {len(project.relations)}")
    
    cache = update_cache(project_dir, project.name, project.version)
    print(f"\n✓ Cache created with {len(cache.entries)} files")
    
    # Step 4: Check rebuild status again (should be no)
    print_section("4. Check Rebuild Status (With Cache)")
    needs_rebuild, changes = should_rebuild(project_dir)
    print(f"Needs rebuild: {needs_rebuild}")
    if not needs_rebuild:
        print("✓ Build is up to date! No changes detected.")
    
    # Step 5: Show cache info
    print_section("5. Cache Information")
    cache = load_cache(project_dir)
    print(f"Project: {cache.project_name} v{cache.project_version}")
    print(f"Created: {cache.created_at}")
    print(f"Updated: {cache.last_updated}")
    print(f"\nCached files ({len(cache.entries)}):")
    for path, entry in sorted(cache.entries.items()):
        size_kb = entry.size / 1024
        print(f"  - {path:30s} {entry.hash[:12]}... {size_kb:>6.1f} KB")
    
    # Step 6: Simulate file modification
    print_section("6. Simulate File Modification")
    customer_file = project_dir / "entities" / "customer.yml"
    original_content = customer_file.read_text()
    
    # Add a comment
    modified_content = original_content + "\n# Modified for demo\n"
    customer_file.write_text(modified_content)
    print(f"Modified: {customer_file.relative_to(project_dir)}")
    
    # Check for changes
    needs_rebuild, changes = should_rebuild(project_dir)
    print(f"\nNeeds rebuild: {needs_rebuild}")
    print(f"Modified files: {len(changes['modified'])}")
    for file in sorted(changes["modified"]):
        print(f"  ~ {file.relative_to(project_dir)}")
    
    # Step 7: Get detailed change info
    print_section("7. Detailed Change Detection")
    cache = load_cache(project_dir)
    changes = get_changed_files(project_dir, cache)
    
    total = sum(len(files) for files in changes.values())
    print(f"Total changes: {total}")
    print(f"  Added: {len(changes['added'])}")
    print(f"  Modified: {len(changes['modified'])}")
    print(f"  Deleted: {len(changes['deleted'])}")
    
    # Step 8: Restore file
    print_section("8. Restore Original File")
    customer_file.write_text(original_content)
    print(f"Restored: {customer_file.relative_to(project_dir)}")
    
    needs_rebuild, changes = should_rebuild(project_dir)
    print(f"\nNeeds rebuild: {needs_rebuild}")
    if not needs_rebuild:
        print("✓ Build is up to date again after restore")
    
    # Step 9: Show cache file location
    print_section("9. Cache File Location")
    from grai.core.cache import get_cache_path
    cache_path = get_cache_path(project_dir)
    print(f"Cache location: {cache_path}")
    print(f"Cache exists: {cache_path.exists()}")
    if cache_path.exists():
        size_kb = cache_path.stat().st_size / 1024
        print(f"Cache size: {size_kb:.2f} KB")
    
    # Summary
    print_section("Summary")
    print("""
Incremental builds provide several benefits:

1. ⚡ Fast Rebuilds
   - Skip compilation when files haven't changed
   - Only process modified files

2. 📊 Change Detection
   - Track file hashes (SHA256)
   - Detect added, modified, and deleted files
   - Fast size checks before hash computation

3. 🗄️ Persistent Cache
   - Stored in .grai/cache.json
   - Survives program restarts
   - Includes project metadata

4. 🔧 CLI Integration
   - `grai build` - Automatic incremental builds
   - `grai build --full` - Force full rebuild
   - `grai cache` - View cache status
   - `grai cache --clear` - Clear cache

Use incremental builds for faster development cycles!
    """)


if __name__ == "__main__":
    try:
        demo_incremental_builds()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

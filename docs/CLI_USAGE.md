# CLI Usage Guide

Complete reference for the grai.build command-line interface.

---

## Overview

The `grai` CLI provides commands for managing knowledge graph projects:

```bash
grai --help    # Show all commands
grai --version # Show version
```

---

## Commands

### `grai init` - Initialize a New Project

Initialize a new grai.build project **in the current directory** (like `git init` or `npm init`).

```bash
# Create and enter your project directory first
mkdir my-graph-project
cd my-graph-project

# Initialize in current directory
grai init
```

**Options:**

- `--name, -n` - Custom project name (default: directory name)
- `--force, -f` - Overwrite existing files
- `path` - Initialize in specific directory (default: `.`)

**Examples:**

```bash
# Initialize in current directory with default name
cd ~/projects/ecommerce
grai init
# Creates project named "ecommerce" (from directory name)

# Initialize with custom name
cd ~/projects/ecommerce
grai init --name my-custom-name
# Creates project named "my-custom-name"

# Initialize in different directory
grai init /path/to/project
# Creates project in /path/to/project

# Force overwrite existing files
grai init --force
```

**What it creates:**

```
my-graph-project/
├── grai.yml              # Project configuration
├── entities/             # Entity definitions
│   ├── customer.yml
│   └── product.yml
├── relations/            # Relation definitions
│   └── purchased.yml
├── target/               # Compiled output (empty initially)
│   └── neo4j/
└── README.md             # Project documentation
```

---

### `grai validate` - Validate Project

Check entity and relation definitions for errors.

```bash
cd my-graph-project
grai validate
```

**Options:**

- `--strict, -s` - Treat warnings as errors
- `--verbose, -v` - Show detailed validation output
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Validate current project
grai validate

# Strict mode (warnings cause failure)
grai validate --strict

# Validate with details
grai validate --verbose

# Validate different project
grai validate /path/to/project
```

**What it checks:**

- Entity references exist
- Key mappings are valid
- No duplicate properties
- No circular dependencies
- Required fields present
- Valid data types

---

### `grai build` - Compile to Cypher

Compile your project to Neo4j Cypher statements.

```bash
cd my-graph-project
grai build
```

**Options:**

- `--output, -o` - Output directory (default: `target/neo4j`)
- `--filename, -f` - Output filename (default: `compiled.cypher`)
- `--schema-only` - Generate only schema (constraints/indexes)
- `--skip-validation` - Skip validation before compiling
- `--verbose, -v` - Show detailed build output
- `--full` - Force full rebuild (ignore cache)
- `--no-cache` - Don't update cache after build
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Basic build
grai build

# Custom output location
grai build --output ./output --filename schema.cypher

# Schema only (no data loading statements)
grai build --schema-only

# Skip validation (faster, but risky)
grai build --skip-validation

# Detailed output
grai build --verbose

# Force full rebuild (ignore incremental cache)
grai build --full

# Build without updating cache
grai build --no-cache
```

**Output:**

Creates `target/neo4j/compiled.cypher` containing:

- Constraint definitions (UNIQUE keys)
- Index definitions (performance)
- Entity MERGE statements
- Relation MERGE statements

---

### `grai run` - Execute Against Neo4j

Build and execute Cypher against a Neo4j database.

**By default**, only creates the schema (constraints and indexes). Use `--with-data` to include data loading statements (requires CSV files).

```bash
cd my-graph-project
grai run --password mypassword
```

**Options:**

- `--uri, -u` - Neo4j connection URI (default: `bolt://localhost:7687`)
- `--user` - Username (default: `neo4j`)
- `--password, -p` - Password (prompts if not provided)
- `--database, -d` - Database name (default: `neo4j`)
- `--file, -f` - Cypher file to execute (default: `target/neo4j/compiled.cypher`)
- `--schema-only` - Create only schema (default: `True`)
- `--with-data` - Include data loading statements (requires LOAD CSV context)
- `--load-csv` - Load CSV data from data/ directory after creating schema
- `--dry-run` - Show what would be executed without running
- `--skip-build` - Skip building before execution
- `--verbose, -v` - Show detailed execution output
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Create schema only (default, recommended for getting started)
grai run

# Create schema AND load CSV data in one command
grai run --load-csv --password secret

# Create schema with explicit flag
grai run --schema-only

# Include data loading statements (requires CSV files)
grai run --with-data

# Specify connection details
grai run --uri bolt://localhost:7687 --user neo4j --password secret

# Different database
grai run --database mygraph --password secret

# Execute specific Cypher file
grai run --file custom.cypher --password secret

# Dry run (see what would execute)
grai run --dry-run --password secret

# Skip rebuild (use existing compiled.cypher)
grai run --skip-build --password secret

# Verbose output (show database stats)
grai run --verbose --password secret
```

**Remote Neo4j:**

```bash
# Connect to remote Neo4j instance
grai run \
  --uri bolt://my-neo4j-server.com:7687 \
  --user neo4j \
  --password mypassword \
  --database production
```

---

### `grai export` - Export Graph IR

Export project to Graph IR (Intermediate Representation) as JSON.

```bash
cd my-graph-project
grai export
```

**Options:**

- `--output, -o` - Output file path (default: `graph-ir.json`)
- `--format, -f` - Export format (currently only `json`)
- `--pretty/--compact` - Pretty-print JSON (default: pretty)
- `--indent, -i` - Indentation spaces (default: 2)
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Export to default file
grai export

# Custom output file
grai export --output schema.json

# Compact JSON
grai export --compact

# Custom indentation
grai export --indent 4
```

**Output structure:**

```json
{
  "project": {
    "name": "my-graph",
    "version": "1.0.0"
  },
  "entities": [...],
  "relations": [...],
  "statistics": {
    "entity_count": 2,
    "relation_count": 1,
    "total_properties": 9
  }
}
```

---

### `grai info` - Show Project Information

Display project statistics and structure.

```bash
cd my-graph-project
grai info
```

**Options:**

- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Show current project info
grai info

# Show different project info
grai info /path/to/project
```

**Output:**

- Project name and version
- Entity count and details
- Relation count and details
- Property statistics
- Source mappings

---

### `grai cache` - Manage Build Cache

View or clear incremental build cache.

```bash
cd my-graph-project
grai cache --show
```

**Options:**

- `--clear, -c` - Clear the build cache
- `--show, -s` - Show cache contents
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Show cache info
grai cache --show

# Clear cache
grai cache --clear

# Both (show then clear)
grai cache --show --clear
```

**What it shows:**

- Cached file hashes
- Last build timestamp
- Changed files since last build
- Cache size

---

### `grai lineage` - Analyze Lineage

Track entity relationships and calculate impact analysis.

```bash
cd my-graph-project
grai lineage
```

**Options:**

- `--entity, -e` - Show lineage for specific entity
- `--relation, -r` - Show lineage for specific relation
- `--impact, -i` - Calculate impact analysis for entity
- `--visualize, -v` - Generate visualization (`mermaid` or `graphviz`)
- `--output, -o` - Output file for visualization
- `--focus, -f` - Focus visualization on specific entity
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Show general lineage statistics
grai lineage

# Show entity lineage
grai lineage --entity customer

# Show relation lineage
grai lineage --relation PURCHASED

# Calculate impact of changing an entity
grai lineage --impact customer

# Generate Mermaid diagram
grai lineage --visualize mermaid --output lineage.mmd

# Generate Graphviz diagram
grai lineage --visualize graphviz --output lineage.dot

# Focus on specific entity
grai lineage --visualize mermaid --focus customer
```

**Visualization formats:**

- **Mermaid** - Markdown-compatible diagrams
- **Graphviz** - DOT format for Graphviz tools

---

### `grai visualize` - Generate Interactive Visualization

Create interactive HTML visualization of the knowledge graph.

```bash
cd my-graph-project
grai visualize --open
```

**Options:**

- `--output, -o` - Output HTML file (default: `graph.html`)
- `--format, -f` - Visualization format: `d3` or `cytoscape` (default: `d3`)
- `--title, -t` - Custom title (default: project name)
- `--width, -w` - Canvas width in pixels (default: 1200)
- `--height, -h` - Canvas height in pixels (default: 800)
- `--open` - Open in browser after generation
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# D3.js force-directed graph
grai visualize --format d3 --open

# Cytoscape.js network
grai visualize --format cytoscape --open

# Custom dimensions
grai visualize --width 1600 --height 1000 --open

# Custom title
grai visualize --title "My Knowledge Graph" --open

# Save to specific file
grai visualize --output my-graph.html --open
```

**Visualization features:**

- **D3.js**: Force-directed physics simulation, drag-and-drop nodes
- **Cytoscape.js**: Hierarchical layout, professional network view
- **Interactive**: Click nodes for details, zoom, pan
- **Self-contained**: Single HTML file, no external dependencies

---

### `grai docs` - Generate Documentation

Generate interactive HTML documentation for your project.

```bash
cd my-graph-project
grai docs --serve
```

**Options:**

- `--serve` - Start local server and open in browser
- `--output, -o` - Output directory (default: `target/docs`)
- `project_dir` - Path to project directory (default: `.`)

**Examples:**

```bash
# Generate and serve documentation
grai docs --serve

# Generate to custom directory
grai docs --output ./documentation
```

---

### `grai migrate-*` - Schema Migrations

Manage schema changes over time with version-controlled migrations.

**Generate a migration:**

```bash
grai migrate-generate --message "Add email to customer"
```

**Check migration status:**

```bash
grai migrate-status --uri bolt://localhost:7687 --password secret
```

**Apply pending migrations:**

```bash
grai migrate-apply --uri bolt://localhost:7687 --password secret
```

**Rollback last migration:**

```bash
grai migrate-rollback --uri bolt://localhost:7687 --password secret
```

See [Schema Migrations](MIGRATIONS.md) for complete documentation.

---

## Common Workflows

### Create New Project

```bash
# 1. Create directory
mkdir ~/projects/my-graph && cd ~/projects/my-graph

# 2. Initialize
grai init

# 3. Verify structure
ls -la
```

### Develop Schema

```bash
# 1. Edit YAML files
vim entities/customer.yml

# 2. Validate
grai validate

# 3. Build
grai build

# 4. Review output
cat target/neo4j/compiled.cypher

# 5. Execute
grai run --password secret
```

### Work from Any Directory

```bash
# Option 1: Navigate to project
cd ~/projects/my-graph
grai validate

# Option 2: Specify project path
grai validate ~/projects/my-graph
grai build ~/projects/my-graph
```

### Incremental Builds

```bash
# First build (full)
grai build

# Edit a file
vim entities/customer.yml

# Next build (incremental - only changed files)
grai build

# Force full rebuild
grai build --full
```

### Generate Documentation

```bash
# Export schema as JSON
grai export --output schema.json

# Generate lineage diagrams
grai lineage --visualize mermaid --output lineage.mmd
grai lineage --visualize graphviz --output lineage.dot

# Generate interactive visualization
grai visualize --format d3 --output graph-d3.html
grai visualize --format cytoscape --output graph-cytoscape.html
```

---

## Tips

### 1. Always initialize in an empty directory

```bash
# Recommended
mkdir my-graph && cd my-graph && grai init

# Not recommended (could overwrite files - use --force if intentional)
cd existing-project-with-files && grai init
```

### 2. Use --dry-run for testing

```bash
# See what would be executed without actually running
grai run --dry-run --password secret
```

### 3. Use cache for faster builds

```bash
# Check what changed
grai cache --show

# Clear cache if needed
grai cache --clear
```

### 4. Validate before building

```bash
# Validation is automatic in build, but you can run it separately
grai validate && grai build
```

### 5. Use environment variables

```bash
# Set default Neo4j connection
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=secret

# Now you can omit these options
grai run
```

---

## Getting Help

```bash
# General help
grai --help

# Command-specific help
grai init --help
grai validate --help
grai build --help
grai run --help
grai export --help
grai info --help
grai cache --help
grai lineage --help
grai visualize --help
```

---

## Related Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) - Complete beginner's guide
- [NEO4J_SETUP.md](NEO4J_SETUP.md) - Neo4j installation and setup
- [PARSER.md](PARSER.md) - YAML schema reference
- [VALIDATOR.md](VALIDATOR.md) - Validation rules
- [COMPILER.md](COMPILER.md) - Cypher generation details
- [VISUALIZER.md](VISUALIZER.md) - Visualization options
- [LINEAGE.md](LINEAGE.md) - Lineage tracking guide
- [CACHE.md](CACHE.md) - Incremental build system

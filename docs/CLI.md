# CLI - Command-Line Interface

The grai.build CLI provides a Typer-based command-line interface for working with knowledge graph projects.

## Overview

The CLI exposes five main commands:

- `grai init` - Initialize a new project
- `grai validate` - Validate entity and relation definitions
- `grai build` - Build project by compiling to Cypher
- `grai compile` - Compile without validation
- `grai info` - Show project information and statistics

## Installation

```bash
pip install grai-build
```

Or install from source:

```bash
git clone https://github.com/grai-build/grai.build
cd grai.build
pip install -e .
```

## Commands

### `grai init`

Initialize a new grai.build project with example entities and relations.

**Usage:**

```bash
grai init [PATH] [OPTIONS]
```

**Arguments:**

- `PATH` - Directory to initialize project in (default: `.`)

**Options:**

- `--name`, `-n` TEXT - Project name (default: `my-knowledge-graph`)
- `--force`, `-f` - Overwrite existing files
- `--help` - Show help message

**Examples:**

```bash
# Initialize in current directory
grai init

# Initialize in specific directory with custom name
grai init my-project --name my-graph

# Overwrite existing project
grai init my-project --force
```

**Created Structure:**

```
my-project/
├── grai.yml              # Project configuration
├── README.md             # Project documentation
├── entities/             # Entity definitions
│   ├── customer.yml
│   └── product.yml
├── relations/            # Relation definitions
│   └── purchased.yml
└── target/               # Compiled output
    └── neo4j/
        └── compiled.cypher
```

---

### `grai validate`

Validate entity and relation definitions for correctness and consistency.

**Usage:**

```bash
grai validate [PROJECT_DIR] [OPTIONS]
```

**Arguments:**

- `PROJECT_DIR` - Path to grai.build project directory (default: `.`)

**Options:**

- `--strict`, `-s` - Treat warnings as errors
- `--verbose`, `-v` - Show detailed validation output
- `--help` - Show help message

**Examples:**

```bash
# Validate current directory
grai validate

# Validate specific project
grai validate my-project

# Strict mode (warnings as errors)
grai validate --strict

# Verbose output
grai validate --verbose
```

**Validation Checks:**

- ✅ Entity references exist
- ✅ Key mappings are valid
- ✅ No duplicate property names
- ✅ No duplicate entity/relation names
- ✅ No circular dependencies
- ✅ Required fields are present

**Output:**

```
🔍 Validating project...

✓ Loaded project: my-graph (v1.0.0)
  - 2 entities
  - 1 relations

✓ Validation passed!
```

---

### `grai build`

Build the project by validating and compiling to Neo4j Cypher.

**Usage:**

```bash
grai build [PROJECT_DIR] [OPTIONS]
```

**Arguments:**

- `PROJECT_DIR` - Path to grai.build project directory (default: `.`)

**Options:**

- `--output`, `-o` PATH - Output directory (default: `target/neo4j`)
- `--filename`, `-f` TEXT - Output filename (default: `compiled.cypher`)
- `--schema-only` - Generate only schema (constraints and indexes)
- `--skip-validation` - Skip validation before compiling
- `--verbose`, `-v` - Show detailed build output
- `--help` - Show help message

**Examples:**

```bash
# Build current directory
grai build

# Build with custom output
grai build --output dist/cypher --filename my-graph.cypher

# Build schema only
grai build --schema-only

# Build without validation
grai build --skip-validation

# Verbose output with build summary
grai build --verbose
```

**Output:**

```
🔨 Building project...

✓ Loaded project: my-graph (v1.0.0)
→ Validating...
✓ Validation passed
→ Compiling to Cypher...
✓ Compiled successfully
✓ Wrote output to: target/neo4j/compiled.cypher

✓ Build complete!

     Build Summary
┏━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric      ┃ Count ┃
┡━━━━━━━━━━━━━╇━━━━━━━┩
│ Entities    │ 2     │
│ Relations   │ 1     │
│ Constraints │ 2     │
│ Indexes     │ 8     │
│ Statements  │ 3     │
└─────────────┴───────┘
```

---

### `grai compile`

Compile project to Cypher without validation. This is an alias for `grai build --skip-validation`.

**Usage:**

```bash
grai compile [PROJECT_DIR] [OPTIONS]
```

**Arguments:**

- `PROJECT_DIR` - Path to grai.build project directory (default: `.`)

**Options:**

- `--output`, `-o` PATH - Output directory (default: `target/neo4j`)
- `--help` - Show help message

**Examples:**

```bash
# Compile without validation
grai compile

# Compile to custom directory
grai compile --output dist/cypher
```

**Use Case:**

Use `compile` when you've already validated and just want to regenerate the Cypher output. Use `build` for the full validation + compilation workflow.

---

### `grai info`

Show project information and statistics.

**Usage:**

```bash
grai info [PROJECT_DIR]
```

**Arguments:**

- `PROJECT_DIR` - Path to grai.build project directory (default: `.`)

**Options:**

- `--help` - Show help message

**Examples:**

```bash
# Show info for current directory
grai info

# Show info for specific project
grai info my-project
```

**Output:**

```
📊 Project Information

         Project: my-graph
┌──────────────────────┬───────┐
│ Name                 │ my-graph │
│ Version              │ 1.0.0 │
│ Entities             │ 2     │
│ Relations            │ 1     │
│ Entity Properties    │ 10    │
│ Relation Properties  │ 4     │
└──────────────────────┴───────┘

                  Entities
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Entity   ┃ Source              ┃ Keys    ┃ Properties ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ customer │ analytics.customers │ cust_id │ 5          │
│ product  │ analytics.products  │ prod_id │ 5          │
└──────────┴─────────────────────┴─────────┴────────────┘

                   Relations
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Relation  ┃ From → To          ┃ Source           ┃ Properties ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ PURCHASED │ customer → product │ analytics.orders │ 4          │
└───────────┴────────────────────┴──────────────────┴────────────┘
```

---

## Global Options

All commands support these global options:

- `--version`, `-v` - Show version and exit
- `--help` - Show help message and exit

**Examples:**

```bash
# Show version
grai --version

# Show general help
grai --help

# Show help for specific command
grai build --help
```

## Complete Workflows

### Basic Workflow

```bash
# 1. Initialize project
grai init my-graph-project --name my-graph

# 2. Edit definitions
cd my-graph-project
vim entities/customer.yml
vim relations/purchased.yml

# 3. Validate
grai validate

# 4. Build
grai build

# 5. View output
cat target/neo4j/compiled.cypher
```

### Development Workflow

```bash
# Initialize
grai init

# Iterate: edit, validate, build
vim entities/new-entity.yml
grai validate
grai build --verbose

# Check project stats
grai info
```

### Production Workflow

```bash
# Validate in CI/CD
grai validate --strict

# Build for deployment
grai build --output dist/cypher --filename production.cypher

# Schema-only for database initialization
grai build --schema-only --filename schema.cypher
```

## Error Handling

The CLI provides clear error messages with exit codes:

- `0` - Success
- `1` - Error (validation failure, file not found, etc.)

**Example Errors:**

```bash
$ grai validate

✗ Validation failed!

Errors:
  ✗  Relation 'PURCHASED' references unknown entity 'order'
  ✗  Entity 'customer' has duplicate property 'email'
```

```bash
$ grai build

✗ Error: grai.yml not found
Hint: Run 'grai init' to create a new project
```

## Rich Output

The CLI uses Rich for beautiful, colored terminal output:

- ✓ Green checkmarks for success
- ✗ Red X marks for errors
- ⚠ Yellow warnings
- → Cyan arrows for progress
- 📊 Tables for structured data
- 🚀 Emoji for visual context

## Environment Variables

Currently, grai.build doesn't use environment variables, but future versions may support:

- `GRAI_HOME` - Default project directory
- `GRAI_OUTPUT_DIR` - Default output directory
- `GRAI_NEO4J_URI` - Default Neo4j connection URI

## Shell Completion

Shell completion is currently disabled but may be added in future versions.

## API

The CLI can also be used programmatically:

```python
from typer.testing import CliRunner
from grai.cli.main import app

runner = CliRunner()
result = runner.invoke(app, ["validate", "my-project"])

if result.exit_code == 0:
    print("Validation passed!")
else:
    print(f"Error: {result.stdout}")
```

## See Also

- [Parser Documentation](PARSER.md) - YAML parsing details
- [Validator Documentation](VALIDATOR.md) - Validation rules
- [Compiler Documentation](COMPILER.md) - Cypher generation
- [Project Progress](PROGRESS.md) - Development status

## Contributing

To add new CLI commands:

1. Add command function to `grai/cli/main.py`
2. Decorate with `@app.command()`
3. Add tests to `tests/test_cli.py`
4. Update this documentation

Example:

```python
@app.command()
def my_command(
    arg: str = typer.Argument(..., help="My argument"),
    option: bool = typer.Option(False, "--option", "-o", help="My option"),
):
    """My command description."""
    console.print(f"Running my command with {arg}")
    # Implementation here
```

## Troubleshooting

### Command not found

If `grai` command is not found after installation:

```bash
# Reinstall in editable mode
pip install -e .

# Or use full path
python -m grai.cli.main --help
```

### Import errors

If you see import errors:

```bash
# Install dependencies
pip install pydantic pyyaml typer rich neo4j

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Permission errors

If you get permission errors when writing files:

```bash
# Check directory permissions
ls -la

# Use sudo (not recommended for user projects)
sudo grai build

# Or change output directory
grai build --output ~/my-graphs
```

---

**Version**: 0.1.0  
**Last Updated**: January 2025

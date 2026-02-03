# Getting Started

This guide walks through creating your first grai.build project.

## Prerequisites

- Python 3.11+
- Neo4j running locally or accessible remotely (see [Neo4j Setup](NEO4J_SETUP.md))

## Installation

```bash
pip install grai-build
```

Verify installation:

```bash
grai --version
grai --help
```

## Create a Project

### Initialize

Create a new project directory and initialize:

```bash
mkdir my-graph-project
cd my-graph-project
grai init
```

This creates:

```
my-graph-project/
├── grai.yml              # Project configuration
├── entities/
│   ├── customer.yml      # Sample entity
│   └── product.yml
├── relations/
│   └── purchased.yml     # Sample relation
├── data/                 # Sample CSV data
│   ├── customers.csv
│   ├── products.csv
│   └── purchased.csv
└── target/               # Compiled output
```

### Project Configuration

The `grai.yml` file configures your project:

```yaml
name: my-graph-project
version: 1.0.0

config:
  neo4j:
    uri: bolt://localhost:7687
    database: neo4j
    user: neo4j

  compiler:
    backend: neo4j
    output_dir: target/neo4j

  validator:
    strict_mode: true
```

## Define Your Schema

### Entities

Entities represent nodes in your graph. Create YAML files in the `entities/` directory:

```yaml
# entities/customer.yml
entity: customer
source: analytics.customers
keys: [customer_id]
properties:
  - name: customer_id
    type: string
  - name: name
    type: string
  - name: email
    type: string
  - name: created_at
    type: datetime
```

### Relations

Relations represent edges between entities. Create YAML files in the `relations/` directory:

```yaml
# relations/purchased.yml
relation: PURCHASED
from: customer
to: product
source: analytics.orders
mappings:
  from_key: customer_id
  to_key: product_id
properties:
  - name: order_id
    type: string
  - name: order_date
    type: datetime
  - name: quantity
    type: integer
```

### Property Types

Supported property types:

| Type | Description |
|------|-------------|
| `string` | Text values |
| `integer` | Whole numbers |
| `float` | Decimal numbers |
| `boolean` | True/false |
| `date` | Date without time |
| `datetime` | Date with time |
| `json` | JSON objects |

## Build and Deploy

### Validate

Check your schema for errors:

```bash
grai validate
```

### Build

Compile to Cypher:

```bash
grai build
```

View the output:

```bash
cat target/neo4j/compiled.cypher
```

### Deploy to Neo4j

Execute against your database:

```bash
grai run \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password your-password
```

Options:

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview without executing |
| `--schema-only` | Create constraints/indexes only |
| `--load-csv` | Load sample data from CSV files |
| `--verbose` | Show detailed output |

### Load Sample Data

If you want to load the sample CSV data:

```bash
grai run --load-csv --password your-password
```

Or use Neo4j Browser to run the generated `load_data.cypher` script.

## Generate Documentation

Create interactive HTML documentation:

```bash
grai docs --serve
```

This opens a browser with:

- Project overview
- Entity catalog
- Relation catalog
- Interactive graph visualization
- Lineage diagrams

## Visualization

Generate standalone visualizations:

```bash
# D3.js force-directed graph
grai visualize

# Cytoscape.js network
grai visualize --format cytoscape

# Open in browser
grai visualize --open
```

## Lineage Analysis

Analyze dependencies:

```bash
# View statistics
grai lineage

# Analyze specific entity
grai lineage --entity customer

# Impact analysis
grai lineage --impact customer

# Generate Mermaid diagram
grai lineage --visualize mermaid --output lineage.mmd
```

## Schema Migrations

Manage schema changes over time:

```bash
# Generate migration from changes
grai migrate-generate --description "Add email to customer"

# Check pending migrations
grai migrate-status

# Apply migrations
grai migrate-apply --uri bolt://localhost:7687 --password secret

# Rollback if needed
grai migrate-rollback --uri bolt://localhost:7687 --password secret
```

See [Schema Migrations](MIGRATIONS.md) for details.

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy Schema

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install grai-build
        run: pip install grai-build

      - name: Validate
        run: grai validate

      - name: Deploy
        run: |
          grai run --schema-only \
            --uri ${{ secrets.NEO4J_URI }} \
            --user ${{ secrets.NEO4J_USER }} \
            --password ${{ secrets.NEO4J_PASSWORD }}
```

## Command Reference

| Command | Description |
|---------|-------------|
| `grai init` | Initialize new project |
| `grai validate` | Validate schema |
| `grai build` | Compile to Cypher |
| `grai run` | Deploy to Neo4j |
| `grai docs` | Generate documentation |
| `grai visualize` | Generate graph visualization |
| `grai lineage` | Analyze dependencies |
| `grai export` | Export as JSON |
| `grai cache` | Manage build cache |
| `grai migrate-*` | Schema migrations |
| `grai info` | Show project info |

See [CLI Reference](CLI.md) for complete documentation.

## Next Steps

- [CLI Reference](CLI.md) - Full command documentation
- [Schema Migrations](MIGRATIONS.md) - Version control for schemas
- [Lineage Tracking](LINEAGE.md) - Dependency analysis
- [Philosophy](PHILOSOPHY.md) - Design principles

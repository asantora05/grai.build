# grai.build

**Schema-as-code for graph databases** — Define schemas in YAML, generate docs like dbt, manage migrations like Alembic.

[![CI](https://github.com/asantora05/grai.build/workflows/CI/badge.svg)](https://github.com/asantora05/grai.build/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/asantora05/grai.build/graph/badge.svg?token=FIV3O0YYVR)](https://codecov.io/gh/asantora05/grai.build)
[![PyPI](https://img.shields.io/pypi/v/grai-build)](https://pypi.org/project/grai-build/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is grai.build?

grai.build manages your graph **schema**, not your data. Define entities and relations in YAML, and grai.build:

- **Validates** schema for consistency before deployment
- **Compiles** to Cypher constraints and indexes
- **Generates** interactive documentation (like `dbt docs`)
- **Tracks lineage** with visualizations
- **Manages migrations** with version control

**What it's not:** An ETL tool. Use Airflow, Prefect, or dbt for data loading — grai.build handles the schema layer.

## Quick Start

```bash
pip install grai-build

# Initialize a project
grai init my-graph-project
cd my-graph-project

# Validate and build
grai build

# Generate documentation
grai docs --serve

# Deploy to Neo4j
grai run --uri bolt://localhost:7687 --user neo4j --password secret
```

## Project Structure

```
my-graph-project/
├── grai.yml              # Project configuration
├── entities/
│   ├── customer.yml      # Node definitions
│   └── product.yml
├── relations/
│   └── purchased.yml     # Relationship definitions
└── target/
    └── neo4j/
        └── compiled.cypher
```

## Schema Definition

**Entity** (`entities/customer.yml`):
```yaml
entity: customer
source: analytics.customers
keys: [customer_id]
properties:
  - name: customer_id
    type: string
  - name: name
    type: string
  - name: region
    type: string
```

**Relation** (`relations/purchased.yml`):
```yaml
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
```

**Compiled output** (`target/neo4j/compiled.cypher`):
```cypher
MERGE (n:customer {customer_id: row.customer_id})
SET n.name = row.name, n.region = row.region;

MATCH (from:customer {customer_id: row.customer_id})
MATCH (to:product {product_id: row.product_id})
MERGE (from)-[r:PURCHASED]->(to)
SET r.order_id = row.order_id, r.order_date = row.order_date;
```

## Features

| Feature | Description |
|---------|-------------|
| Schema validation | Catch reference errors and type mismatches before deployment |
| Cypher compilation | Generate constraints, indexes, and merge statements |
| Documentation | Interactive HTML docs with entity catalog and graph visualization |
| Lineage tracking | Dependency graphs and impact analysis |
| Migrations | Version-controlled schema changes with up/down scripts |
| Build caching | Incremental builds for faster iteration |

## CLI Commands

```bash
grai init <name>       # Create new project
grai validate          # Validate schema
grai build             # Compile project
grai run               # Deploy to Neo4j
grai docs              # Generate documentation
grai lineage           # Show dependency graph
grai migrate-generate  # Create migration from changes
grai migrate-apply     # Apply pending migrations
```

## CI/CD Integration

```yaml
# .github/workflows/deploy-schema.yml
name: Deploy Graph Schema

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate Schema
        run: grai validate

      - name: Deploy to Production
        run: |
          grai run --schema-only \
            --uri ${{ secrets.NEO4J_URI }} \
            --user ${{ secrets.NEO4J_USER }} \
            --password ${{ secrets.NEO4J_PASSWORD }}
```

## Development

```bash
git clone https://github.com/asantora05/grai.build.git
cd grai.build
pip install -e ".[dev]"
pytest
```

## Roadmap

- [x] YAML schema definition and validation
- [x] Cypher compilation for Neo4j
- [x] Documentation generation
- [x] Lineage tracking and visualization
- [x] Schema migrations
- [ ] Gremlin backend support
- [ ] Incremental sync

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.

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

grai init my-graph-project
cd my-graph-project

grai build
grai docs --serve
grai run --uri bolt://localhost:7687 --user neo4j --password secret
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
  - name: order_date
    type: datetime
```

## Documentation

| Section | Description |
|---------|-------------|
| [Getting Started](GETTING_STARTED.md) | Installation and first project |
| [CLI Reference](CLI.md) | Complete command reference |
| [Schema Migrations](MIGRATIONS.md) | Version-controlled schema changes |
| [Neo4j Setup](NEO4J_SETUP.md) | Database configuration |
| [Philosophy](PHILOSOPHY.md) | Design principles |

## Features

| Feature | Description |
|---------|-------------|
| Schema validation | Catch reference errors and type mismatches |
| Cypher compilation | Generate constraints, indexes, and merge statements |
| Documentation | Interactive HTML docs with graph visualization |
| Lineage tracking | Dependency graphs and impact analysis |
| Migrations | Version-controlled schema changes with up/down scripts |
| Build caching | Incremental builds for faster iteration |

## Contributing

Contributions welcome. See the [GitHub repository](https://github.com/asantora05/grai.build) for details.

## License

MIT License

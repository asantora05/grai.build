# grai.build

> **Schema-as-code for graph databases** - Documentation like dbt, migrations for Neo4j

[![CI](https://github.com/asantora05/grai.build/workflows/CI/badge.svg)](https://github.com/asantora05/grai.build/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/asantora05/grai.build/graph/badge.svg?token=FIV3O0YYVR)](https://codecov.io/gh/asantora05/grai.build)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📘 What is grai.build?

**grai.build brings dbt's documentation experience to graph databases** - define your schema in YAML, generate beautiful docs, and manage migrations.

It manages your graph **schema**, not your data. You define entities and relations in YAML, and grai.build:

- ✅ **Validates** your schema for consistency
- ✅ **Generates** Cypher constraints and indexes
- ✅ **Documents** your graph structure automatically (like `dbt docs`)
- ✅ **Tracks lineage** with interactive visualizations
- ✅ **Integrates** with your CI/CD pipeline

**What it's NOT:**

- ❌ Not an ETL tool (use Airflow, Prefect, or dbt for data loading)
- ❌ Not a data transformation framework (dbt does this for SQL)
- ❌ Not a replacement for your existing data infrastructure

**Think of it as:**

- **Like dbt:** Declarative YAML definitions, beautiful documentation, lineage tracking
- **Like Alembic/Flyway:** Database migrations and schema management
- **For graphs:** Manages Neo4j schema while your pipelines handle data

## 🚀 Quick Start

### Installation

```bash
pip install grai-build
```

### Create Your First Project

```bash
# Initialize a new project
grai init my-graph-project
cd my-graph-project

# Validate and build
grai build

# Generate documentation (like dbt docs)
grai docs --serve

# Deploy schema to Neo4j
grai run --uri bolt://localhost:7687 --user neo4j --password secret
```

## 📂 Project Structure

```
my-graph-project/
├── grai.yml              # Project manifest
├── entities/
│   ├── customer.yml      # Entity definitions
│   └── product.yml
├── relations/
│   └── purchased.yml     # Relation definitions
└── target/               # Compiled output
    └── neo4j/
        └── compiled.cypher
```

## 📝 Example

### Entity: `entities/customer.yml`

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

### Relation: `relations/purchased.yml`

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

## 🎯 Key Features

- **Declarative modeling** - Define your graph schema in YAML (like dbt models)
- **Schema validation** - Catch errors before deployment
- **Documentation generation** - Beautiful HTML docs with `grai docs` (like `dbt docs generate/serve`)
- **Lineage visualization** - Interactive graph and Mermaid diagrams showing data flow
- **Multi-backend support** - Start with Neo4j, expand to Gremlin later
- **CLI-first** - Integrates into your CI/CD pipeline
- **Type-safe** - Built with Pydantic for robust validation

## 📚 Documentation

Explore the full documentation:

- [Getting Started](GETTING_STARTED.md) - Quick start guide and basic concepts
- [CLI Reference](CLI.md) - Complete command reference
- [Philosophy](PHILOSOPHY.md) - Design principles and architecture
- [Neo4j Setup](NEO4J_SETUP.md) - Setting up Neo4j for grai.build

## 🤝 Contributing

Contributions are welcome! This is an early-stage project with room for improvement.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for the graph database community**

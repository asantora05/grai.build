# grai.build

> **Schema-as-code for graph databases** - Documentation like dbt, migrations for Neo4j

[![CI](https://github.com/asantora05/grai.build/workflows/CI/badge.svg)](https://github.com/asantora05/grai.build/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/asantora05/grai.build/graph/badge.svg?token=FIV3O0YYVR)](https://codecov.io/gh/asantora05/grai.build)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📘 What is grai.build?

**grai.build brings dbt's workflow to graph databases** - define your schema in YAML, load data from common sources, generate beautiful docs, and track lineage.

You define entities and relations in YAML, and grai.build:

- ✅ **Validates** your schema for consistency
- ✅ **Generates** Cypher constraints and indexes
- ✅ **Loads data** from BigQuery, PostgreSQL, and other sources
- ✅ **Documents** your graph structure automatically (like `dbt docs`)
- ✅ **Tracks lineage** with interactive visualizations
- ✅ **Integrates** with your CI/CD pipeline

**What it DOES:**

- ✅ Schema management (constraints, indexes, validation)
- ✅ Data loading from common sources (BigQuery, PostgreSQL, Snowflake coming soon)
- ✅ Declarative YAML-based definitions
- ✅ Documentation and lineage tracking

**What it's NOT:**

- ❌ Not a workflow orchestrator (use Airflow/Prefect for scheduling and complex pipelines)
- ❌ Not a data transformation framework (use dbt for SQL transformations, then load to graph)
- ❌ Not a replacement for your existing data infrastructure

**Think of it as:**

- **Like dbt:** Declarative YAML definitions, data loading, documentation, lineage tracking
- **Like Alembic/Flyway:** Database migrations and schema management
- **For graphs:** Manages Neo4j schema AND loads data from your warehouse

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

# Load sample data for local testing
grai run --load-csv --password secret
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

### Compile to Cypher

```bash
grai build
```

**Output (`target/neo4j/compiled.cypher`):**

```cypher
// Create Customer nodes
MERGE (n:customer {customer_id: row.customer_id})
SET n.name = row.name,
    n.region = row.region;

// Create Product nodes
MERGE (n:product {product_id: row.product_id})
SET n.name = row.name;

// Create PURCHASED relations
MATCH (from:customer {customer_id: row.customer_id})
MATCH (to:product {product_id: row.product_id})
MERGE (from)-[r:PURCHASED]->(to)
SET r.order_id = row.order_id,
    r.order_date = row.order_date;
```

## 🎯 Features

- **Declarative modeling** - Define your graph schema in YAML (like dbt models)
- **Schema validation** - Catch errors before deployment
- **Documentation generation** - Beautiful HTML docs with `grai docs` (like `dbt docs generate/serve`)
- **Lineage visualization** - Interactive graph and Mermaid diagrams showing data flow
- **Multi-backend support** - Start with Neo4j, expand to Gremlin later
- **CLI-first** - Integrates into your CI/CD pipeline
- **Type-safe** - Built with Pydantic for robust validation
- **Extensible** - Easy to add custom backends and transformations

## 🏗️ Real-World Usage

### Local Development

```bash
# 1. Define schema
vim entities/customer.yml

# 2. Validate
grai validate

# 3. Generate documentation
grai docs --serve  # Opens browser with interactive docs

# 4. Deploy schema
grai run --schema-only

# 5. Test with sample data
grai run --load-csv
```

### Production Deployment

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
      - uses: actions/checkout@v3

      - name: Validate Schema
        run: grai validate

      - name: Deploy to Production
        run: |
          grai run --schema-only \
            --uri ${{ secrets.NEO4J_URI }} \
            --user ${{ secrets.NEO4J_USER }} \
            --password ${{ secrets.NEO4J_PASSWORD }}
```

### With Your ETL Pipeline

```python
# Your Airflow DAG
from airflow import DAG
from airflow.operators.bash import BashOperator
from your_etl import load_customers_to_neo4j

dag = DAG('graph_pipeline')

# 1. grai.build ensures schema is up-to-date
deploy_schema = BashOperator(
    task_id='deploy_schema',
    bash_command='grai run --schema-only',
    dag=dag
)

# 2. Your ETL loads the actual data
load_data = PythonOperator(
    task_id='load_data',
    python_callable=load_customers_to_neo4j,
    dag=dag
)

deploy_schema >> load_data
```

## 📦 Architecture

```
grai/
├── cli/              # Typer-based CLI commands
├── core/
│   ├── models.py     # Pydantic models (Entity, Relation, Property)
│   ├── parser/       # YAML → Python models
│   ├── validator/    # Schema validation
│   ├── compiler/     # Generate Cypher/Gremlin
│   ├── loader/       # Execute against databases
│   └── utils/        # Shared utilities
└── templates/        # Project templates
```

## 🧪 Development

### Setup

```bash
# Clone the repo
git clone https://github.com/asantora05/grai.build.git
cd grai.build

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black grai/
ruff check grai/
```

## 📖 Documentation

Generate beautiful, interactive documentation for your graph:

```bash
# Generate and serve documentation locally
grai docs --serve

# Generate to custom directory
grai docs --output ./my-docs

# Just generate (don't serve)
grai docs
```

The documentation includes:

- 📊 Project overview with stats
- 📦 Entity catalog with properties
- 🔗 Relation catalog with mappings
- 🕸️ Interactive graph visualization (D3.js)
- 🔄 Lineage diagrams (Mermaid.js)

For development guidance, check out the [instructions](.github/instructions/instructions.instructions.md).

## 🗺️ Roadmap

- [x] Core Pydantic models
- [x] YAML parser
- [x] Schema validator
- [x] Cypher compiler
- [x] Neo4j loader
- [x] CLI commands (`init`, `build`, `validate`, `run`, `docs`)
- [x] Graph IR export (JSON)
- [x] Documentation generation (dbt-style)
- [x] Lineage visualization (Mermaid + D3.js)
- [ ] Graph visualization improvements
- [ ] Gremlin backend support
- [ ] Incremental sync
- [ ] Schema versioning and migrations

## 📊 Current Status

**v0.3.0** - Feature-complete MVP with documentation

- ✅ **Core Models** - Pydantic models for Entity, Relation, Property
- ✅ **YAML Parser** - Parse and load entity/relation definitions
- ✅ **Schema Validator** - Validate references and mappings
- ✅ **Cypher Compiler** - Generate Neo4j constraints and indexes
- ✅ **Neo4j Loader** - Execute Cypher against Neo4j instances
- ✅ **Documentation Generator** - Interactive HTML docs (like dbt docs)
- ✅ **Lineage Tracking** - Visualize data flow and dependencies
- ✅ **Graph Visualizer** - D3.js and Cytoscape visualizations
- ✅ **Build Cache** - Incremental builds for faster iteration
- ✅ **CLI Commands** - Full command suite (`init`, `build`, `validate`, `run`, `docs`, etc.)

**257 tests passing | High coverage across all modules**

See it in action:

```bash
# Initialize example project
grai init my-project
cd my-project

# Generate and view documentation
grai docs --serve
```

## 🤝 Contributing

Contributions are welcome! This is an early-stage project, so there's plenty of room for improvement.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 💡 Inspiration

This project is inspired by:

- [dbt](https://www.getdbt.com/) - Analytics engineering workflow
- [SQLMesh](https://sqlmesh.com/) - Data transformation framework
- [Amundsen](https://www.amundsen.io/) - Data discovery and metadata

---

**Built with ❤️ for the graph database community**

# grai.build

> **Declarative knowledge graph modeling** - dbt for graph databases

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📘 What is grai.build?

`grai.build` is an open-source developer tool that brings the declarative, YAML-based modeling approach of [dbt](https://www.getdbt.com/) to knowledge graphs.

Define your entities and relations in simple YAML files, and grai will:

- ✅ Validate your schema for consistency
- ✅ Compile to Cypher (Neo4j) or Gremlin queries
- ✅ Execute against your graph database
- ✅ Track changes and provide lineage

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

# Build and validate
grai build

# Execute against Neo4j
grai build --execute --uri bolt://localhost:7687 --user neo4j --password secret
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

- **Declarative modeling** - Define your graph schema in YAML
- **Schema validation** - Catch errors before deployment
- **Multi-backend support** - Start with Neo4j, expand to Gremlin later
- **CLI-first** - Integrates into your CI/CD pipeline
- **Type-safe** - Built with Pydantic for robust validation
- **Extensible** - Easy to add custom backends and transformations

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

Coming soon! For now, check out the [instructions](.github/instructions/instructions.instructions.md) for development guidance.

## 🗺️ Roadmap

- [x] Core Pydantic models
- [x] YAML parser
- [x] Schema validator
- [ ] Cypher compiler
- [ ] Neo4j loader
- [ ] CLI commands (`init`, `build`, `test`, `run`)
- [ ] Graph IR export (JSON)
- [ ] Lineage visualization
- [ ] Gremlin backend support
- [ ] Incremental sync

## 📊 Current Status

**v0.1.0-alpha** - Core foundation complete

- ✅ **Core Models** (95% coverage, 13 tests)

  - Pydantic models for Entity, Relation, Property
  - Full validation and type safety
  - Lookup methods and utilities

- ✅ **YAML Parser** (83% coverage, 20 tests)

  - Parse entity and relation YAML files
  - Batch directory loading
  - Complete project loading
  - Robust error handling

- ✅ **Validator** (91% coverage, 27 tests)
  - Entity reference validation
  - Key mapping verification
  - Circular dependency detection
  - Strict mode support
  - Detailed error messages

**Total: 60 tests passing | 89% coverage**

📝 **Coming Next**: Cypher compiler to generate Neo4j queries

Run demos to see functionality:

```bash
python demo.py            # Core models
python demo_parser.py     # YAML parser
python demo_validator.py  # Validator
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

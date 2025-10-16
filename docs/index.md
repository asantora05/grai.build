# grai.build Documentation

Welcome to the grai.build documentation! This guide will help you understand and use grai.build to manage your graph database schemas.

## 📚 Documentation Structure

### Getting Started

- **[Getting Started](getting-started.md)** - Quick start guide and installation
- **[Philosophy](philosophy.md)** - Design principles and project vision
- **[Neo4j Setup](neo4j-setup.md)** - Setting up Neo4j locally for development

### Core Features

- **[CLI Reference](cli.md)** - Complete command-line interface documentation
- **[Source Configuration](sources.md)** - How to configure data sources (BigQuery, Snowflake, etc.)
- **[Data Loading](data-loading.md)** - Loading data from warehouses into your graph
- **[Build Cache](cache.md)** - Incremental builds for faster iteration
- **[Profiles](profiles.md)** - Multi-environment configuration (dev, staging, prod)

### Advanced Features

- **[Lineage Tracking](lineage.md)** - Track dependencies and impact analysis
- **[Visualization](visualization.md)** - Interactive graph visualizations

## 🚀 Quick Links

### New to grai.build?

Start here:

1. [Getting Started Guide](getting-started.md) - Install and create your first project
2. [Philosophy](philosophy.md) - Understand the "why" behind grai.build
3. [CLI Reference](cli.md) - Learn the command-line tools

### Common Tasks

- **Initialize a project**: `grai init`
- **Validate your schema**: `grai validate`
- **Build Cypher output**: `grai build`
- **Deploy to Neo4j**: `grai run --password <password>`
- **View lineage**: `grai lineage`
- **Create visualization**: `grai visualize`

### Need Help?

- [GitHub Issues](https://github.com/asantora05/grai.build/issues) - Report bugs or request features
- [GitHub Discussions](https://github.com/asantora05/grai.build/discussions) - Ask questions and share ideas
- [Support Guide](../SUPPORT.md) - Where to get help

## 📖 Documentation by Topic

### Schema Definition

Learn how to define your graph schema:

- [Source Configuration](sources.md) - Configure different data source types
- [Getting Started](getting-started.md#defining-entities) - Entity and relation basics

### Development Workflow

- [Build Cache](cache.md) - Speed up development with incremental builds
- [CLI Reference](cli.md) - All available commands and options

### Data Operations

- [Data Loading](data-loading.md) - Load data from various sources
- [Neo4j Setup](neo4j-setup.md) - Configure your Neo4j instance

### Analysis & Visualization

- [Lineage Tracking](lineage.md) - Understand data flow and dependencies
- [Visualization](visualization.md) - Generate interactive graph visualizations

## 🎯 Use Cases

### dbt Users

If you're familiar with dbt, you'll feel at home with grai.build:

- **YAML-based definitions** - Like dbt models
- **Build command** - Similar to `dbt build`
- **Data loading** - Like `dbt run` but for graphs
- **Documentation generation** - Like `dbt docs generate`
- **Incremental builds** - Skip unchanged files
- **Profiles** - Multi-environment configs like dbt

See: [Philosophy](philosophy.md#comparison-to-dbt)

### Data Engineers

Managing graph schemas and loading data in production:

- **CI/CD integration** - Validate schemas and load data in your pipeline
- **Version control** - Track schema changes in git
- **Multiple environments** - Dev, staging, production configs
- **Data source connectors** - BigQuery, Snowflake, PostgreSQL (future)
- **Orchestration-ready** - Integrates with Airflow, Prefect, etc.

See: [Data Loading](data-loading.md), [Profiles](profiles.md)

### Data Analysts

Exploring and documenting graph structures:

- **Lineage visualization** - See upstream/downstream dependencies
- **Impact analysis** - Understand change implications
- **Interactive docs** - Browse your graph schema

See: [Lineage Tracking](lineage.md), [Visualization](visualization.md)

## 🏗️ Architecture

grai.build follows a clear pipeline:

```
YAML Definitions → Parser → Validator → Compiler → Cypher Scripts → Neo4j
                                                   ↓
                                            Lineage Tracker
                                                   ↓
                                            Visualizations

Data Sources (BigQuery, etc.) → Data Loader → Batching → Neo4j
                                     ↓
                                Verbose Logging
```

Each component is independent and testable, making the tool reliable and extensible.

## 🤝 Contributing

Want to contribute to grai.build?

- 🐛 [Report bugs](https://github.com/asantora05/grai.build/issues)
- 💡 [Suggest features](https://github.com/asantora05/grai.build/discussions)
- 📖 Improve documentation
- 🧪 Write tests
- 🔧 Submit pull requests

See our [Contributing Guide](https://github.com/asantora05/grai.build/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://github.com/asantora05/grai.build/blob/main/CODE_OF_CONDUCT.md).

## 📄 License

grai.build is open source under the [MIT License](../LICENSE).

---

**Ready to get started?** Head to the [Getting Started Guide](getting-started.md)!

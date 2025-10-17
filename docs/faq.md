# Frequently Asked Questions

Common questions about grai.build.

---

## General Questions

### What is grai.build?

grai.build is a declarative schema management tool for graph databases, inspired by dbt. It lets you define your graph schema in YAML files, validates consistency, generates Cypher scripts, and manages your Neo4j schema.

**Think of it as "dbt for graph databases"** - but focused on schema, not data transformation.

### Is grai.build an ETL tool?

**No.** grai.build is a **schema management** tool, not an ETL tool.

- ✅ **What it does:** Define schema, validate structure, generate Cypher constraints/indexes
- ❌ **What it doesn't do:** Transform data, schedule jobs, orchestrate pipelines

For data loading, use tools like:

- Airflow / Prefect (orchestration)
- dbt (SQL transformations)
- Custom Python scripts
- Apache Spark / Kafka

Then use grai.build to ensure your graph schema is consistent and documented.

### How is grai.build different from dbt?

| Feature           | dbt                                     | grai.build                         |
| ----------------- | --------------------------------------- | ---------------------------------- |
| **Database**      | SQL (PostgreSQL, Snowflake, etc.)       | Graph (Neo4j, future: Gremlin)     |
| **Focus**         | Data transformation (SELECT statements) | Schema management + data loading   |
| **Models**        | SQL files with Jinja                    | YAML files with entities/relations |
| **Output**        | Tables/views                            | Graph nodes/edges                  |
| **Data Loading**  | Via materialization                     | From BigQuery, PostgreSQL, etc.    |
| **Documentation** | Yes (HTML docs)                         | Yes (HTML docs + visualizations)   |
| **Lineage**       | Yes (SQL-based)                         | Yes (graph-based)                  |
| **Testing**       | Yes (data quality tests)                | Yes (schema validation)            |
| **Orchestration** | No (use Airflow)                        | No (use Airflow)                   |

**Use both together:**

- Use **dbt** to transform data in your warehouse (SQL → clean tables)
- Use **grai.build** to load transformed data into Neo4j (warehouse → graph)
- Use **Airflow/Prefect** to orchestrate both (dbt run → grai load)

### What databases are supported?

**Currently:**

- ✅ Neo4j (full support)

**Planned:**

- 🚧 Apache TinkerPop / Gremlin
- 🚧 Amazon Neptune
- 🚧 Azure Cosmos DB (Gremlin API)

### Do I need to learn Cypher?

**Not really.** grai.build generates Cypher for you based on your YAML definitions.

However, basic Cypher knowledge is helpful for:

- Querying your graph after it's built
- Understanding the generated output
- Debugging issues

**Resources:**

- [Neo4j Cypher Basics](https://neo4j.com/docs/getting-started/cypher-intro/)
- [Cypher Reference Card](https://neo4j.com/docs/cypher-refcard/current/)

---

## Installation & Setup

### How do I install grai.build?

```bash
# From PyPI (when published)
pip install grai-build

# Or from source (development)
git clone https://github.com/asantora05/grai.build.git
cd grai.build
pip install -e .
```

### What Python version do I need?

Python 3.11 or higher.

Check your version:

```bash
python --version
```

### Do I need Neo4j running locally?

Yes, if you want to execute the generated Cypher against a database.

**For local development:**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  neo4j:latest
```

**For schema-only work:**
You can use `grai build` to generate Cypher without connecting to Neo4j.

---

## Project Structure

### Where should I create my project?

Create your project **anywhere outside the grai.build source code**.

```bash
# Good: Create in your projects directory
mkdir ~/projects/my-graph
cd ~/projects/my-graph
grai init

# Bad: Don't create inside grai.build repo
cd /path/to/grai.build/repo
grai init  # ❌ This will pollute the source code
```

### What files does `grai init` create?

```
my-project/
├── grai.yml              # Project configuration
├── entities/
│   ├── customer.yml      # Example entity
│   └── product.yml       # Example entity
├── relations/
│   └── purchased.yml     # Example relation
├── data/                 # Sample CSV files
│   ├── customers.csv
│   ├── products.csv
│   └── purchased.csv
├── load_data.cypher      # Sample data loading script
├── README.md             # Project documentation
└── target/               # Build output (generated)
```

### Can I organize entities into subdirectories?

**Not currently.** All entity files must be directly in `entities/` and all relation files in `relations/`.

```bash
# ✅ Supported
entities/customer.yml
entities/product.yml

# ❌ Not supported (yet)
entities/retail/customer.yml
entities/retail/product.yml
```

This is a planned feature for v1.0.

---

## Defining Entities and Relations

### What's the difference between an entity and a relation?

**Entity** = Node in your graph

- Represents a thing (customer, product, user, etc.)
- Has properties (name, email, created_at, etc.)
- Has unique keys for identification

**Relation** = Edge in your graph

- Connects two entities
- Has a direction (from → to)
- Can have properties (order_date, quantity, etc.)
- Represents relationships (PURCHASED, FOLLOWS, WORKS_FOR, etc.)

### Can an entity have multiple keys?

Yes! Composite keys are supported:

```yaml
entity: order_item
source: analytics.order_items
keys: [order_id, product_id] # Composite key
properties:
  - name: order_id
    type: string
  - name: product_id
    type: string
  - name: quantity
    type: integer
```

This creates a unique constraint on the combination of both fields.

### Can a relation connect the same entity to itself?

Yes! Self-referencing relations are supported:

```yaml
relation: FOLLOWS
from: user
to: user # Same entity
source: social.follows
mappings:
  from_key: follower_id
  to_key: followee_id
```

Example: User A follows User B.

### What property types are supported?

```yaml
properties:
  - name: id
    type: string
  - name: age
    type: integer
  - name: price
    type: float
  - name: active
    type: boolean
  - name: created_at
    type: datetime
  - name: tags
    type: list
  - name: metadata
    type: map
```

These map to Neo4j's native types.

---

## Commands and Workflow

### What's the difference between `grai build` and `grai run`?

**`grai build`:**

- Compiles YAML → Cypher
- Writes output to `target/neo4j/compiled.cypher`
- Does **not** connect to Neo4j
- Safe to run anytime

**`grai run`:**

- Runs `grai build` first
- **Then** connects to Neo4j
- Executes the generated Cypher
- Modifies your database

```bash
# Just compile (safe)
grai build

# Compile and execute (modifies database)
grai run --password yourpassword
```

### How do I load data into Neo4j?

grai.build has **built-in data loading** for common sources. Here are your options:

**1. Use `grai load` (recommended for BigQuery, PostgreSQL):**

```bash
# Configure source in entity YAML
entity: customer
source: my_dataset.customers

# Load data
grai load customers --verbose
```

**2. Manual Cypher scripts:**

```cypher
CREATE (c:customer {customer_id: 'C001', name: 'Alice'});
```

**3. Python with grai.core:**

```python
from grai.core.loader.bigquery_loader import load_entity_from_bigquery

result = load_entity_from_bigquery(
    entity=entity,
    bigquery_connection=extractor,
    neo4j_connection=driver,
    batch_size=1000,
    verbose=True
)
```

**4. LOAD CSV in Cypher:**

```cypher
LOAD CSV WITH HEADERS FROM 'file:///customers.csv' AS row
MERGE (c:customer {customer_id: row.customer_id})
SET c.name = row.name, c.email = row.email;
```

**5. Use ETL tools for complex workflows:**

- Airflow/Prefect for orchestration
- dbt for transformations, then grai.build for loading
- Apache Hop, Talend, etc.

### Can I use grai.build in CI/CD?

**Yes!** grai.build is designed for CI/CD workflows.

Example GitHub Actions:

```yaml
name: Deploy Graph Schema

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install grai
        run: pip install grai-build

      - name: Validate schema
        run: grai validate

      - name: Deploy to production
        run: |
          grai run \
            --uri ${{ secrets.NEO4J_URI }} \
            --user ${{ secrets.NEO4J_USER }} \
            --password ${{ secrets.NEO4J_PASSWORD }}
```

---

## Data Sources

### What data sources are supported?

Currently:

- ✅ **BigQuery** (load data from BigQuery tables)
- ✅ **PostgreSQL** (load data from PostgreSQL databases)
- ✅ **Manual Cypher** (write your own data loading scripts)

Planned:

- 🚧 Snowflake
- 🚧 CSV files
- 🚧 Parquet files

### Do I need a data source to use grai.build?

**No.** You can create schema-only projects:

```yaml
entity: customer
source: null # No data source
keys: [customer_id]
properties:
  - name: customer_id
    type: string
```

This generates constraints and indexes without attempting data loading.

### How do I load data from BigQuery?

1. **Configure in grai.yml:**

```yaml
config:
  bigquery:
    project_id: my-project
    credentials_path: /path/to/service-account.json
```

2. **Set source in entity:**

```yaml
entity: customer
source: my_dataset.customers
keys: [customer_id]
```

3. **Load data:**

```bash
grai load customers --verbose
```

### How do I load data from PostgreSQL?

1. **Configure profile in `~/.grai/profiles.yml`:**

```yaml
default:
  target: dev
  outputs:
    dev:
      warehouse:
        type: postgres
        host: localhost
        port: 5432
        database: analytics
        user: postgres
        password: mypassword
        schema: public
        sslmode: prefer
      graph:
        type: neo4j
        uri: bolt://localhost:7687
        user: neo4j
        password: neopass
```

2. **Set source in entity:**

```yaml
entity: customer
source: customers # Table name
keys: [customer_id]
properties:
  - name: customer_id
    type: string
  - name: name
    type: string
```

3. **Load data:**

```bash
grai load entity customer --profile default --verbose
```

See [Profiles](profiles.md) and [Data Loading](data-loading.md) for details.

---

## Troubleshooting

### Why isn't my data loading into Neo4j?

Common causes:

1. **NULL values in key fields**

   - Neo4j cannot MERGE on NULL
   - Use `--verbose` to see sample rows
   - Filter NULLs in your source query

2. **Wrong credentials**

   - Test connection: `cypher-shell -a bolt://localhost:7687 -u neo4j -p password`

3. **Source query returns no data**

   - Test query directly in your data warehouse

4. **Batch size too large**
   - Reduce batch size in grai.yml

**Debug with:**

```bash
grai load --verbose --limit 10
```

### How do I reset my Neo4j database?

```cypher
-- In Neo4j Browser
MATCH (n) DETACH DELETE n;
```

Or recreate the Docker container:

```bash
docker stop neo4j
docker rm neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/pass neo4j:latest
```

### Why is validation failing?

Common issues:

1. **Entity not found:**

   - Check entity name matches filename
   - Ensure entity file exists

2. **Invalid YAML:**

   - Check indentation (use spaces, not tabs)
   - Validate syntax: `python -c "import yaml; yaml.safe_load(open('entities/customer.yml'))"`

3. **Missing required fields:**
   - Every entity needs: `entity`, `source`, `keys`, `properties`
   - Every relation needs: `relation`, `from`, `to`, `source`, `mappings`

See [Troubleshooting](troubleshooting.md) for more.

---

## Advanced Topics

### Can I use profiles like dbt?

**Yes!** grai.build supports profiles for managing multiple environments:

```yaml
# profiles.yml
default:
  target: dev
  outputs:
    dev:
      type: neo4j
      uri: bolt://localhost:7687
      user: neo4j
      password: devpassword
      database: neo4j

    prod:
      type: neo4j
      uri: bolt://prod-server:7687
      user: neo4j
      password: "{{ env_var('NEO4J_PASSWORD') }}"
      database: neo4j
```

See [Profiles](profiles.md) for details.

### Does grai.build track schema versions?

**Not yet.** Schema versioning/migrations are planned for v1.0.

Current workflow:

- Track schema changes in git
- Use `grai validate` before deploying
- Neo4j will preserve existing data when adding constraints

### Can I extend grai.build with custom backends?

**Yes!** The architecture is designed to be extensible.

To add a new backend (e.g., Gremlin):

1. Create a new compiler in `grai/core/compiler/`
2. Implement the same interface as `CypherCompiler`
3. Add loader in `grai/core/loader/`

See the codebase for examples.

### How does caching work?

grai.build caches compiled output to speed up incremental builds:

```bash
# Use cache (default)
grai build --use-cache

# Clear cache
grai build --clear-cache

# Force rebuild
grai build --no-cache
```

Cache is stored in `target/.cache/` and invalidated when source files change.

See [Build Cache](cache.md) for details.

---

## Contributing

### How can I contribute?

- 🐛 [Report bugs](https://github.com/asantora05/grai.build/issues)
- 💡 [Suggest features](https://github.com/asantora05/grai.build/discussions)
- 📖 Improve documentation
- 🧪 Write tests
- 🔧 Submit pull requests

See [Contributing Guide](contributing.md).

### Where can I get help?

- 📖 [Documentation](https://asantora05.github.io/grai.build/)
- 🐛 [GitHub Issues](https://github.com/asantora05/grai.build/issues)
- 💬 [GitHub Discussions](https://github.com/asantora05/grai.build/discussions)
- 📧 Email: support@grai.build

---

## More Questions?

Can't find your answer? [Ask on GitHub Discussions](https://github.com/asantora05/grai.build/discussions) or [open an issue](https://github.com/asantora05/grai.build/issues/new).

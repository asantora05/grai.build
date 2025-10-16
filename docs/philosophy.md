# 🎯 Philosophy & Design Principles

## What is grai.build?

**grai.build is "dbt for knowledge graphs"** - a declarative tool for managing graph database schemas and loading data from common sources.

---

## 🎯 Core Philosophy

### 1. **Declarative Schema-as-Code**

Like dbt transformed SQL analytics with declarative modeling, grai.build brings the same approach to graph databases.

---

## 🤔 The Problem We Solve

### Traditional Graph Development Problems

1. **Schema Drift**: Graph schemas evolve organically, becoming inconsistent
2. **No Version Control**: Hard to track what entities/relations exist
3. **Manual Cypher**: Writing constraints and indexes by hand
4. **No Documentation**: Graph structure lives only in developers' heads
5. **No CI/CD**: Can't validate schema changes before deployment

### What We're NOT Solving

We are **not** an ETL tool. We don't:

- Extract data from source systems (use Airbyte, Fivetran, custom APIs)
- Load data in real-time (use Kafka, CDC, application code)
- Replace your data pipelines (use Airflow, Prefect, dbt)
- Manage data transformations (use dbt for that)

---

## 🎯 Core Philosophy

### 1. **Schema, Not Data**

```yaml
# grai.build defines WHAT your graph looks like
entity: customer
keys: [customer_id]
properties:
  - name: customer_id
  - name: email
# Your ETL pipeline handles HOW data gets loaded
```

**Think of it like database migrations:**

- Alembic/Flyway manage schema changes
- Your application manages data
- grai.build is the Alembic for graphs

### 2. **Declarative, Not Imperative**

```yaml
# Declarative (grai.build)
entity: customer
source: analytics.customers
keys: [customer_id]
# Not imperative
# (no "run this script to create customers")
```

You declare what you want, we generate the Cypher to make it happen.

### 3. **Version Control Everything**

```bash
git diff entities/customer.yml
# See exactly what changed in your schema

git blame relations/purchased.yml
# Know when and why relations were added
```

Your graph schema lives in version control, just like your application code.

### 4. **Separation of Concerns**

```
┌─────────────────────────────────────────────────────────┐
│  grai.build (Schema Layer)                              │
│  • Define entities/relations                            │
│  • Generate constraints/indexes                         │
│  • Validate consistency                                 │
│  • Generate documentation                               │
└─────────────────────────────────────────────────────────┘
                         ↓ (generates Cypher)
┌─────────────────────────────────────────────────────────┐
│  Your ETL Pipeline (Data Layer)                         │
│  • Extract from sources (Postgres, APIs, files)         │
│  • Transform data                                       │
│  • Load into Neo4j (using generated schema)             │
│  • Scheduled via Airflow/Prefect/dbt                    │
└─────────────────────────────────────────────────────────┘
```

### 5. **CI/CD First**

```yaml
# .github/workflows/graph-schema.yml
- name: Validate Graph Schema
  run: grai validate

- name: Check for Breaking Changes
  run: grai diff --fail-on-breaking

- name: Deploy Schema
  run: grai run --schema-only
```

Schema changes go through code review and CI, just like application code.

---

## 🏗️ Architecture Principles

### Inspired by Modern Data Tools

#### **dbt (SQL Transformations)**

```sql
-- models/customers.sql
{{ config(materialized='table') }}
select * from raw.customers
```

**grai.build (Graph Schema)**

```yaml
# entities/customer.yml
entity: customer
source: analytics.customers
keys: [customer_id]
```

#### **Terraform (Infrastructure as Code)**

```hcl
resource "aws_instance" "web" {
  ami = "ami-123456"
}
```

**grai.build (Schema as Code)**

```yaml
entity: customer
keys: [customer_id]
```

#### **Alembic (Database Migrations)**

```python
def upgrade():
    op.add_column('users', sa.Column('email'))
```

**grai.build (Graph Migrations)**

```yaml
# Version controlled schema changes
entity: customer
properties:
  - name: email # New property
```

---

## 📊 Comparison to Other Tools

### vs. Neo4j Desktop / Browser

- **Neo4j**: Manual Cypher in a GUI
- **grai.build**: Declarative schema in version control

### vs. neo4j-admin import

- **neo4j-admin**: Bulk CSV loading tool
- **grai.build**: Schema management + data loading for graphs (use both together)

### vs. Apache AGE / TigerGraph

- **Other Graphs**: Different graph databases
- **grai.build**: Could support multiple backends (Neo4j first)

### vs. dbt

- **dbt**: SQL transformations in data warehouses
- **grai.build**: Schema definitions for graph databases
- **Use together**: dbt transforms relational data → grai.build defines graph schema

---

## 🎯 When to Use grai.build

### ✅ Perfect Use Cases

1. **Microservices with Shared Graph**

   ```
   Multiple services write to Neo4j
   → Need consistent schema across services
   → grai.build enforces schema contract
   ```

2. **Analytics Graphs**

   ```
   dbt → Data Warehouse → ETL → Neo4j
   → grai.build defines graph schema
   → ETL loads transformed data
   ```

3. **Knowledge Graphs**

   ```
   Multiple data sources → Graph
   → grai.build defines ontology
   → Pipelines populate entities
   ```

4. **CI/CD Pipelines**
   ```
   PR → grai validate → Review → Deploy
   → Catch schema errors before production
   ```

### ❌ Not Ideal Use Cases

1. **Simple Application CRUD**

   ```
   Just use Neo4j driver directly in your app
   grai.build adds unnecessary complexity
   ```

2. **One-off Data Imports**

   ```
   Use neo4j-admin import or LOAD CSV
   Don't need schema management overhead
   ```

3. **Exploratory Analysis**
   ```
   Just write Cypher in Neo4j Browser
   Too early to formalize schema
   ```

---

## 🔄 Recommended Workflows

### Development Workflow

```bash
# 1. Define schema locally
vim entities/customer.yml

# 2. Validate
grai validate

# 3. See generated Cypher
grai build
cat target/neo4j/compiled.cypher

# 4. Test locally with sample data
grai run --schema-only
grai run --load-csv  # Quick test with CSV samples

# 5. Commit
git add entities/customer.yml
git commit -m "Add customer entity"
```

### Production Workflow

```bash
# CI Pipeline (GitHub Actions, GitLab CI, etc.)
steps:
  - grai validate
  - grai build
  - grai run --schema-only --uri $PROD_URI

# Data Pipeline (Airflow, Prefect, etc.)
# Your DAG:
extract_from_postgres()
transform_data()
load_to_neo4j()  # Uses schema from grai.build
```

### Team Workflow

```
Developer A              Developer B
     │                        │
     ├─ Add entity            ├─ Add relation
     ├─ grai validate         ├─ grai validate
     ├─ PR → Review           ├─ PR → Review
     │                        │
     └────────┬───────────────┘
              │
         Merge to main
              │
         CI validates
              │
      Deploy schema to prod
              │
    ETL pipeline loads data
```

---

## 🚀 Future Vision

### Phase 1: Schema Management + Data Loading (Current)

**Goal:** Manage graph schemas and load data like dbt manages SQL models

**Features:**

- ✅ Define entities/relations in YAML
- ✅ Generate Cypher constraints/indexes
- ✅ Validate schema consistency
- ✅ Load data from BigQuery
- ✅ Batch processing with progress tracking
- ✅ Verbose logging for debugging
- ✅ Basic visualization

### Phase 2: Integration Templates (Next)

- 🔄 Generate ETL boilerplate code
- 🔄 dbt integration (graph models)
- 🔄 Airflow operators for graph loading
- 🔄 FastAPI endpoints for graph CRUD

### Phase 3: Multi-Backend (Future)

- ⏳ Apache AGE support
- ⏳ TigerGraph support
- ⏳ Gremlin-compatible databases
- ⏳ Cross-platform schema abstraction

### Phase 4: Advanced Features (Future)

- ⏳ Schema migrations (like Alembic)
- ⏳ Breaking change detection
- ⏳ Auto-generated GraphQL APIs
- ⏳ Graph testing framework

---

## 💡 Key Insights

### 1. **CSV Loading is for Development Only**

The `--load-csv` flag exists for:

- Quick local testing
- Demos and tutorials
- Validating schema with sample data

**In production**, you need proper ETL pipelines.

### 2. **grai.build Generates, You Execute**

```bash
# grai.build generates Cypher
grai build → target/neo4j/compiled.cypher

# You decide when/how to execute it
# Option 1: CLI
grai run --schema-only

# Option 2: In your pipeline
cat compiled.cypher | cypher-shell

# Option 3: Application code
driver.execute_cypher(read_file('compiled.cypher'))
```

### 3. **Schema Evolution > Data Migration**

Unlike relational databases where migrations are complex:

- Graphs are schema-flexible
- New properties/labels can be added easily
- Focus on evolution, not migration

### 4. **Documentation is a First-Class Output**

```bash
grai export → schema.json
grai lineage → lineage.mmd
grai visualize → interactive-graph.html
```

Documentation stays in sync with code automatically.

---

## 🎓 Learning from dbt's Success

### What dbt Got Right

1. **Separation of Concerns**: Analysts own transformations, engineers own pipelines
2. **Version Control**: SQL lives in git, not in tools
3. **Testing Built-in**: Data tests run in CI/CD
4. **Documentation**: Auto-generated from code
5. **Community**: Open-source, extensible

### What We're Applying

1. **Separation**: Graph architects define schema, engineers load data
2. **Version Control**: YAML in git, not in Neo4j Browser
3. **Testing**: Schema validation in CI/CD
4. **Documentation**: Auto-generated visualizations
5. **Community**: Open-source, extensible to other graph DBs

---

## 🎯 Success Metrics

We know we're successful when:

1. **Teams can onboard faster**

   - New devs understand graph structure from YAML
   - Documentation is always up-to-date

2. **Schema stays consistent**

   - No more "wait, does this node have this property?"
   - CI catches schema violations

3. **Deployment is automated**

   - Schema changes deploy through CI/CD
   - No manual Cypher in production

4. **Knowledge is shared**
   - Graph structure is documented
   - Lineage is tracked
   - Changes are reviewable

---

## 📚 Further Reading

- [Getting Started](GETTING_STARTED.md) - Quick start guide
- [CLI Usage](CLI_USAGE.md) - Complete command reference
- [Data Loading](DATA_LOADING.md) - ETL integration patterns
- [Neo4j Setup](NEO4J_SETUP.md) - Local development setup

---

## 💬 Questions?

**"Should I use grai.build if I'm just building a simple app?"**

Probably not. If your app is the only thing writing to Neo4j, just use the driver directly. grai.build adds value when you have:

- Multiple services/teams sharing a graph
- Need for schema governance
- CI/CD pipelines
- Complex ETL processes

**"Can grai.build replace my ETL pipeline?"**

No. grai.build manages your graph **schema**. Your ETL pipeline manages your **data**. Use them together.

**"How does this relate to dbt?"**

Use dbt to transform data in your warehouse, then use grai.build to define the schema when loading that data into a graph. They complement each other.

**"Why not just write Cypher directly?"**

Same reason you use dbt instead of raw SQL:

- Version control
- Validation
- Documentation
- Consistency
- Team collaboration

---

**Remember:** grai.build handles both **schema management** and **data loading** from common sources. For complex transformations, use dbt. For orchestration, use Airflow/Prefect. Focus on defining your graph structure in YAML, and let grai.build handle the implementation.

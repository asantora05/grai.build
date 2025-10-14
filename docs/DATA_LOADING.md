# 📊 Data Loading Guide

Complete guide to understanding data loading in grai.build.

---

## 🎯 Overview

grai.build separates **schema creation** from **data loading**:

1. **Schema**: Constraints and indexes that define your graph structure
2. **Data**: Actual nodes and relationships loaded into the graph

This separation follows best practices and allows for flexible data loading strategies.

---

## 🏗️ Schema-Only Mode (Default)

### What it does

Creates only the database schema:

- Unique constraints on entity keys
- Indexes on entity properties
- **No actual data nodes or relationships**

### When to use

- Getting started with a new project
- Setting up a new database
- Testing schema definitions
- CI/CD pipelines (schema validation)

### How to use

```bash
# Schema only (default)
grai run --uri bolt://localhost:7687 --user neo4j --password secret

# Explicit flag
grai run --schema-only --uri bolt://localhost:7687 --user neo4j --password secret
```

### What gets created

```cypher
// Constraints for unique keys
CREATE CONSTRAINT constraint_customer_customer_id IF NOT EXISTS 
FOR (n:customer) REQUIRE n.customer_id IS UNIQUE;

// Indexes for properties
CREATE INDEX index_customer_name IF NOT EXISTS 
FOR (n:customer) ON (n.name);

CREATE INDEX index_customer_email IF NOT EXISTS 
FOR (n:customer) ON (n.email);
```

---

## 📦 With Data Mode

### What it does

Generates MERGE statements with `row.property` placeholders designed for use with `LOAD CSV` or parameterized queries.

### When to use

- You have CSV files prepared
- You're using custom data loading scripts
- You need to generate templates for ETL pipelines

### How to use

```bash
# Generate data loading statements
grai run --with-data --uri bolt://localhost:7687 --user neo4j --password secret
```

### ⚠️ Important Note

The `--with-data` flag generates Cypher like this:

```cypher
MERGE (n:customer {customer_id: row.customer_id})
SET n.name = row.name,
    n.email = row.email;
```

This **will fail** if executed directly because `row` is undefined. You need to either:

1. Wrap it in a `LOAD CSV` statement
2. Use it as a template for parameterized queries
3. Use Python/application code to supply parameters

---

## 🎁 Quick Start with Sample Data

When you run `grai init`, sample CSV files are automatically created for you:

```
your-project/
├── data/
│   ├── customers.csv      # 5 sample customers
│   ├── products.csv       # 6 sample products
│   └── purchased.csv      # 10 sample orders
└── load_data.py           # Ready-to-use loading script
```

**To load the sample data immediately:**

1. Create the schema:
   ```bash
   grai run --uri bolt://localhost:7687 --user neo4j --password yourpassword
   ```

2. Load the CSV data:
   ```bash
   python load_data.py
   ```

That's it! Your graph is now populated with sample data.

---

## 🔄 Data Loading Strategies

### Strategy 1: Python Scripts (Recommended)

Use Python to load data directly:

```python
from grai.core.loader.neo4j_loader import connect_neo4j, execute_cypher, close_connection

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "graipassword"

DATA = """
CREATE (c1:customer {
    customer_id: 'C001',
    name: 'Alice Johnson',
    email: 'alice@example.com',
    created_at: datetime('2024-01-15')
});

CREATE (c2:customer {
    customer_id: 'C002',
    name: 'Bob Smith',
    email: 'bob@example.com',
    created_at: datetime('2024-02-01')
});
"""

driver = connect_neo4j(uri=URI, user=USER, password=PASSWORD)
result = execute_cypher(driver, DATA)

if result.success:
    print(f"✅ Loaded {result.records_affected} records")

close_connection(driver)
```

### Strategy 2: LOAD CSV

Prepare CSV files and use Neo4j's LOAD CSV:

**customers.csv:**
```csv
customer_id,name,email,created_at
C001,Alice Johnson,alice@example.com,2024-01-15T00:00:00Z
C002,Bob Smith,bob@example.com,2024-02-01T00:00:00Z
```

**Load script:**
```cypher
LOAD CSV WITH HEADERS FROM 'file:///data/customers.csv' AS row
MERGE (n:customer {customer_id: row.customer_id})
SET n.name = row.name,
    n.email = row.email,
    n.created_at = datetime(row.created_at);
```

### Strategy 3: Application Integration

Use the neo4j driver in your application:

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

def create_customer(tx, customer_id, name, email):
    query = """
    MERGE (c:customer {customer_id: $customer_id})
    SET c.name = $name,
        c.email = $email
    """
    tx.run(query, customer_id=customer_id, name=name, email=email)

with driver.session() as session:
    session.write_transaction(
        create_customer,
        "C001",
        "Alice Johnson",
        "alice@example.com"
    )

driver.close()
```

---

## 🚀 Recommended Workflow

### 1. Create Schema

```bash
# First, create the schema
grai run --uri bolt://localhost:7687 --user neo4j --password secret
```

### 2. Verify Schema

```cypher
-- In Neo4j Browser
SHOW CONSTRAINTS;
SHOW INDEXES;
```

### 3. Load Data

Choose your strategy:

- **Small datasets**: Python scripts (Strategy 1)
- **Large datasets**: LOAD CSV (Strategy 2)
- **Production apps**: Application integration (Strategy 3)

### 4. Verify Data

```cypher
-- Check what was loaded
MATCH (n)
RETURN labels(n) AS type, count(n) AS count;

-- View sample data
MATCH (n:customer)
RETURN n
LIMIT 5;
```

---

## 🔧 Troubleshooting

### Error: "Variable `row` not defined"

**Cause**: Trying to execute data loading Cypher without LOAD CSV context.

**Solution**: Use `--schema-only` (default) instead of `--with-data`:

```bash
# This works (default)
grai run

# This will fail without CSV files
grai run --with-data
```

### No data appears after `grai run`

**Expected behavior**: By default, `grai run` only creates the schema, not data.

**Solution**: Load data using Python scripts (see Strategy 1 above).

### CSV loading fails

**Common issues**:

1. **File path**: Make sure CSV is in Neo4j import directory
2. **Headers**: CSV must have headers matching property names
3. **Encoding**: Use UTF-8 encoding
4. **Line endings**: Unix (LF) line endings preferred

---

## 📚 Examples

### Complete Example: Schema + Data

```bash
# Step 1: Create schema
grai run --uri bolt://localhost:7687 --user neo4j --password secret

# Step 2: Load data
cat > load_data.py << 'EOF'
from grai.core.loader.neo4j_loader import connect_neo4j, execute_cypher, close_connection

driver = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="secret"
)

data = """
CREATE (c:customer {customer_id: 'C001', name: 'Alice', email: 'alice@example.com'});
CREATE (p:product {product_id: 'P001', name: 'Laptop', price: 999.99});
MATCH (c:customer {customer_id: 'C001'})
MATCH (p:product {product_id: 'P001'})
CREATE (c)-[:PURCHASED {order_id: 'O001', order_date: date()}]->(p);
"""

result = execute_cypher(driver, data)
print(f"✅ Created {result.records_affected} records")
close_connection(driver)
EOF

python load_data.py

# Step 3: Verify
# Open Neo4j Browser and run:
# MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25;
```

---

## 🎯 Best Practices

1. **Always create schema first** before loading data
2. **Use schema-only mode by default** (it's the default for a reason)
3. **Load data separately** using Python scripts or LOAD CSV
4. **Test with small datasets** before loading production data
5. **Use transactions** for bulk loading
6. **Add error handling** in data loading scripts
7. **Validate data** before loading (check for nulls, duplicates, etc.)

---

## 📖 Related Documentation

- [Getting Started Guide](GETTING_STARTED.md) - Complete beginner tutorial
- [Neo4j Setup Guide](NEO4J_SETUP.md) - Local Neo4j installation
- [CLI Usage](CLI_USAGE.md) - Complete CLI reference
- [Compiler Documentation](COMPILER.md) - Cypher generation details

---

**Questions? Issues?**

File an issue on GitHub: https://github.com/grai-build/grai.build/issues

# 🚀 Getting Started with grai.build

Complete guide for using grai.build from any directory as a real user.

---

## 📋 Prerequisites

- Python 3.11+ installed
- grai-build package installed
- Neo4j running (see [NEO4J_SETUP.md](NEO4J_SETUP.md) for details)

---

## ✅ Step 1: Verify Installation

First, make sure grai is installed and working:

```bash
# Check if grai is installed
which grai

# Check version
grai --version

# Should output: grai.build version 0.1.0
```

If not installed, install it:

```bash
# For development (editable install)
cd /path/to/grai.build/repo
pip install -e .

# Or for production use (from PyPI when published)
pip install grai-build
```

---

## 📂 Step 2: Create Your Project Directory

Create a new project directory **outside the grai.build source repo**:

```bash
# Create and navigate to your project directory (can be anywhere)
mkdir -p ~/my-projects/ecommerce-graph
cd ~/my-projects/ecommerce-graph
```

**Important:** Always create the directory first and then `cd` into it. This matches the workflow of tools like `npm init`, `git init`, and `cargo init`.

---

## 🎬 Step 3: Initialize Project

### Option A: Use `grai init` (Recommended)

Initialize the project **in the current directory**:

```bash
# Make sure you're in your project directory
cd ~/my-projects/ecommerce-graph

# Initialize here (creates files in current directory)
grai init
```

This creates files in the current directory:

```
~/my-projects/ecommerce-graph/  (your current directory)
├── grai.yml
├── entities/
│   ├── customer.yml
│   └── product.yml
├── relations/
│   └── purchased.yml
├── data/                  # NEW: Sample CSV files!
│   ├── customers.csv     # 5 sample customers
│   ├── products.csv      # 6 sample products
│   └── purchased.csv     # 10 sample orders
├── load_data.cypher      # NEW: Data loading Cypher script
├── README.md
└── target/
```

**What's included:**

- ✅ Entity and relation YAML definitions
- ✅ Sample CSV files with realistic data
- ✅ Ready-to-use Cypher script for loading data (just copy/paste into Neo4j Browser)
- ✅ Documentation and examples

**Alternative usage:**

```bash
# Initialize with a custom project name
grai init --name my-custom-name

# Initialize in a different directory
grai init /path/to/project

# Force overwrite existing files
grai init --force
```

### Option B: Manual Setup

If you prefer manual setup, create the structure manually:

```bash
# Create directories
mkdir -p entities relations target/neo4j

# Create grai.yml
cat > grai.yml << 'EOF'
name: ecommerce-graph
version: 1.0.0

config:
  neo4j:
    uri: bolt://localhost:7687
    database: neo4j
    user: neo4j
    password: graipassword

  compiler:
    backend: neo4j
    output_dir: target/neo4j

  validator:
    strict_mode: true
EOF

# Create an example entity
cat > entities/customer.yml << 'EOF'
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
  - name: region
    type: string
  - name: created_at
    type: datetime
EOF

# Create another entity
cat > entities/product.yml << 'EOF'
entity: product
source: catalog.products
keys: [product_id]
properties:
  - name: product_id
    type: string
  - name: name
    type: string
  - name: category
    type: string
  - name: price
    type: float
EOF

# Create a relation
cat > relations/purchased.yml << 'EOF'
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
  - name: total_amount
    type: float
EOF
```

---

## 🔍 Step 4: Validate Your Project

```bash
# Make sure you're in your project directory
cd ~/my-projects/ecommerce-graph

# Validate the project
grai validate
```

**Expected output:**

```
✅ Project validated successfully
   Entities: 2
   Relations: 1
   Properties: 9
```

---

## 🔨 Step 5: Build (Compile to Cypher)

```bash
# Compile to Cypher without executing
grai build
```

**Expected output:**

```
✅ Project validated successfully
📦 Compiling project...
✅ Compiled 2 entities and 1 relation
📁 Output written to: target/neo4j/compiled.cypher
```

**View the compiled Cypher:**

```bash
cat target/neo4j/compiled.cypher
```

You should see Cypher statements like:

```cypher
// Create customer nodes
MERGE (n:customer {customer_id: row.customer_id})
SET n.name = row.name,
    n.email = row.email,
    n.region = row.region,
    n.created_at = row.created_at;

// Create product nodes
MERGE (n:product {product_id: row.product_id})
SET n.name = row.name,
    n.category = row.category,
    n.price = row.price;

// Create PURCHASED relations
MATCH (from:customer {customer_id: row.customer_id})
MATCH (to:product {product_id: row.product_id})
MERGE (from)-[r:PURCHASED]->(to)
SET r.order_id = row.order_id,
    r.order_date = row.order_date,
    r.quantity = row.quantity,
    r.total_amount = row.total_amount;
```

---

## 🚀 Step 6: Create the Schema in Neo4j

**Prerequisites:**

- Neo4j must be running (see [NEO4J_SETUP.md](NEO4J_SETUP.md))
- You have connection credentials

```bash
# Create schema (constraints and indexes only)
grai run \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password graipassword
```

**What this does:**

By default, `grai run` creates only the **schema** (constraints and indexes) without attempting to load data. This is perfect for getting started, as it doesn't require CSV files or data sources.

**Expected output:**

```
✅ Project validated successfully
📦 Compiling project...
✅ Compiled 2 entities and 1 relation
📁 Output written to: target/neo4j/compiled.cypher
🔌 Connecting to Neo4j at bolt://localhost:7687...
✅ Connected successfully
⚡ Executing Cypher statements...
✅ Executed 10 statements successfully
📊 Records affected: 0
⏱️  Execution time: 0.13s
```

The generated Cypher looks like this:

```cypher
// Create constraints for unique keys
CREATE CONSTRAINT constraint_customer_customer_id IF NOT EXISTS
FOR (n:customer) REQUIRE n.customer_id IS UNIQUE;

CREATE CONSTRAINT constraint_product_product_id IF NOT EXISTS
FOR (n:product) REQUIRE n.product_id IS UNIQUE;

// Create indexes for faster lookups
CREATE INDEX index_customer_name IF NOT EXISTS
FOR (n:customer) ON (n.name);

CREATE INDEX index_customer_email IF NOT EXISTS
FOR (n:customer) ON (n.email);
// ... and so on
```

---

## 🌐 Step 7: Verify Schema in Neo4j Browser

Open Neo4j Browser: http://localhost:7474

Login with:

- Username: `neo4j`
- Password: `graipassword`

Check the constraints:

```cypher
SHOW CONSTRAINTS
```

Check the indexes:

```cypher
SHOW INDEXES
```

You should see all the constraints and indexes defined in your project. The schema is ready, but no data has been loaded yet.

---

## � Understanding Data Loading

The `grai run` command has two modes:

### Mode 1: Schema Only (Default)

```bash
grai run --uri bolt://localhost:7687 --user neo4j --password graipassword
```

Creates only constraints and indexes. This is the **recommended starting point** as it doesn't require any data files.

### Mode 2: With Data (Requires CSV Files)

```bash
grai run --with-data --uri bolt://localhost:7687 --user neo4j --password graipassword
```

Generates MERGE statements with `row.property` placeholders, which are designed to be used with `LOAD CSV` statements. This mode will fail unless you've prepared CSV files and modified the Cypher to include LOAD CSV context.

**For now, stick with the default schema-only mode.** To load actual data, use Python scripts (see next section).

---

## �📊 Step 8: Load Sample Data

Create a script to load test data:

```bash
cat > load_data.py << 'EOF'
"""Load sample data into the graph."""
from grai.core.loader.neo4j_loader import (
    connect_neo4j,
    execute_cypher,
    close_connection,
)

# Connection details
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "graipassword"

# Sample data
DATA = """
// Create customers
CREATE (c1:customer {
    customer_id: 'C001',
    name: 'Alice Johnson',
    email: 'alice@example.com',
    region: 'US-West',
    created_at: datetime('2024-01-15')
});
CREATE (c2:customer {
    customer_id: 'C002',
    name: 'Bob Smith',
    email: 'bob@example.com',
    region: 'US-East',
    created_at: datetime('2024-02-01')
});
CREATE (c3:customer {
    customer_id: 'C003',
    name: 'Carol Williams',
    email: 'carol@example.com',
    region: 'EU',
    created_at: datetime('2024-02-15')
});

// Create products
CREATE (p1:product {
    product_id: 'P001',
    name: 'Laptop Pro 15',
    category: 'Electronics',
    price: 1299.99
});
CREATE (p2:product {
    product_id: 'P002',
    name: 'Wireless Mouse',
    category: 'Accessories',
    price: 29.99
});
CREATE (p3:product {
    product_id: 'P003',
    name: 'USB-C Hub',
    category: 'Accessories',
    price: 49.99
});
CREATE (p4:product {
    product_id: 'P004',
    name: 'Monitor 27"',
    category: 'Electronics',
    price: 399.99
});

// Create purchases
MATCH (c:customer {customer_id: 'C001'})
MATCH (p:product {product_id: 'P001'})
CREATE (c)-[:PURCHASED {
    order_id: 'O001',
    order_date: datetime('2024-03-01'),
    quantity: 1,
    total_amount: 1299.99
}]->(p);

MATCH (c:customer {customer_id: 'C001'})
MATCH (p:product {product_id: 'P002'})
CREATE (c)-[:PURCHASED {
    order_id: 'O002',
    order_date: datetime('2024-03-01'),
    quantity: 2,
    total_amount: 59.98
}]->(p);

MATCH (c:customer {customer_id: 'C002'})
MATCH (p:product {product_id: 'P003'})
CREATE (c)-[:PURCHASED {
    order_id: 'O003',
    order_date: datetime('2024-03-15'),
    quantity: 1,
    total_amount: 49.99
}]->(p);

MATCH (c:customer {customer_id: 'C003'})
MATCH (p:product {product_id: 'P001'})
CREATE (c)-[:PURCHASED {
    order_id: 'O004',
    order_date: datetime('2024-03-20'),
    quantity: 1,
    total_amount: 1299.99
}]->(p);

MATCH (c:customer {customer_id: 'C003'})
MATCH (p:product {product_id: 'P004'})
CREATE (c)-[:PURCHASED {
    order_id: 'O005',
    order_date: datetime('2024-03-20'),
    quantity: 1,
    total_amount: 399.99
}]->(p);
"""

def main():
    print("📦 Loading sample data...")

    driver = connect_neo4j(uri=URI, user=USER, password=PASSWORD)
    result = execute_cypher(driver, DATA)

    if result.success:
        print(f"✅ Data loaded successfully!")
        print(f"   Statements: {result.statements_executed}")
        print(f"   Records: {result.records_affected}")
        print(f"   Time: {result.execution_time:.2f}s")
    else:
        print(f"❌ Failed to load data:")
        for error in result.errors:
            print(f"   {error}")

    close_connection(driver)

if __name__ == "__main__":
    main()
EOF

# Run it
python load_data.py
```

**Expected output:**

```
📦 Loading sample data...
✅ Data loaded successfully!
   Statements: 12
   Records: 22
   Time: 0.34s
```

---

## 🔎 Step 9: Query Your Data

In Neo4j Browser (http://localhost:7474):

### View the entire graph

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50
```

### Find high-value customers

```cypher
MATCH (c:customer)-[p:PURCHASED]->()
WITH c, sum(p.total_amount) AS total_spent
WHERE total_spent > 1000
RETURN c.name, c.email, total_spent
ORDER BY total_spent DESC
```

### Popular products

```cypher
MATCH ()-[p:PURCHASED]->(prod:product)
RETURN prod.name, prod.category, count(p) AS purchases, sum(p.quantity) AS units_sold
ORDER BY purchases DESC
```

### Customer purchase history

```cypher
MATCH (c:customer {customer_id: 'C001'})-[p:PURCHASED]->(prod:product)
RETURN c.name, prod.name, p.order_date, p.quantity, p.total_amount
ORDER BY p.order_date
```

---

## 🎨 Step 10: Visualize Your Schema

Generate an interactive visualization:

```bash
# D3.js force-directed graph
grai visualize --format d3 --open

# Or Cytoscape.js network
grai visualize --format cytoscape --open
```

This opens an interactive HTML file showing your entities and relations.

---

## 🔄 Common Workflows

### Workflow 1: Make Schema Changes

```bash
# 1. Edit your YAML files
vim entities/customer.yml

# 2. Validate changes
grai validate

# 3. Build to see generated Cypher
grai build

# 4. Review the output
cat target/neo4j/compiled.cypher

# 5. Execute when satisfied
grai run --uri bolt://localhost:7687 --user neo4j --password graipassword
```

### Workflow 2: Add New Entity

```bash
# Create new entity file
cat > entities/order.yml << 'EOF'
entity: order
source: analytics.orders
keys: [order_id]
properties:
  - name: order_id
    type: string
  - name: status
    type: string
  - name: created_at
    type: datetime
  - name: total_amount
    type: float
EOF

# Validate and build
grai validate
grai run --uri bolt://localhost:7687 --user neo4j --password graipassword
```

### Workflow 3: Generate Documentation

```bash
# Export schema as JSON
grai export --format json --output schema.json

# Generate lineage diagram (Mermaid)
grai lineage --format mermaid --output lineage.mmd

# Generate lineage diagram (Graphviz)
grai lineage --format dot --output lineage.dot
```

### Workflow 4: Work from Any Directory

**Important:** You can run `grai` commands from anywhere as long as:

1. You're in a directory with a `grai.yml` file, OR
2. You specify the project directory with `--project-dir`

```bash
# Option 1: Navigate to project directory
cd ~/my-projects/ecommerce-graph
grai validate

# Option 2: Run from anywhere
grai validate --project-dir ~/my-projects/ecommerce-graph
grai build --project-dir ~/my-projects/ecommerce-graph

# Option 3: Use environment variable
export GRAI_PROJECT_DIR=~/my-projects/ecommerce-graph
grai validate  # Works from any directory
```

---

## 📁 Directory Structure Best Practices

### Recommended structure:

```
~/my-projects/
├── ecommerce-graph/           # One project
│   ├── grai.yml
│   ├── entities/
│   ├── relations/
│   └── target/
├── social-network-graph/      # Another project
│   ├── grai.yml
│   ├── entities/
│   ├── relations/
│   └── target/
└── finance-graph/             # Another project
    ├── grai.yml
    ├── entities/
    ├── relations/
    └── target/
```

### Each project is independent:

- Has its own `grai.yml` configuration
- Can point to different Neo4j databases
- Can have different validation rules
- Generates its own compiled output

---

## 🎯 Quick Reference

### Essential Commands (run from project directory)

```bash
# Initialize new project
grai init

# Validate schema
grai validate

# Build (compile only)
grai build

# Build and execute
grai run --uri bolt://localhost:7687 --user neo4j --password graipassword

# Visualize
grai visualize --format d3 --open

# Export schema
grai export --format json --output schema.json

# Generate lineage
grai lineage --format mermaid

# Get help
grai --help
grai build --help
```

### Connection Details (default Docker setup)

```bash
URI:      bolt://localhost:7687
User:     neo4j
Password: graipassword
Browser:  http://localhost:7474
Database: neo4j
```

---

## ✅ Checklist for New Projects

- [ ] Created project directory outside grai.build repo
- [ ] Initialized project with `grai init` or manually
- [ ] Created `grai.yml` with Neo4j connection details
- [ ] Defined at least one entity in `entities/`
- [ ] (Optional) Defined relations in `relations/`
- [ ] Ran `grai validate` successfully
- [ ] Ran `grai build` to see compiled Cypher
- [ ] Neo4j is running and accessible
- [ ] Ran `grai run` to load schema
- [ ] Verified in Neo4j Browser
- [ ] (Optional) Loaded sample data
- [ ] (Optional) Generated visualization

---

## 🆘 Troubleshooting

### "No grai.yml found"

Make sure you're in the right directory:

```bash
pwd
ls -la grai.yml
```

Or specify the project directory:

```bash
grai validate --project-dir /path/to/project
```

### "Cannot connect to Neo4j"

Check Neo4j is running:

```bash
# Docker
docker ps | grep neo4j

# Test connection
curl http://localhost:7474
```

### "Command 'grai' not found"

Install grai-build:

```bash
pip install -e /path/to/grai.build/repo
# Or when published: pip install grai-build
```

### "Module not found" errors

Make sure all dependencies are installed:

```bash
pip install pydantic pyyaml typer rich neo4j
```

---

## 🚀 Next Steps

1. **Create your own entities** - Define your domain model
2. **Load real data** - Connect to your data sources
3. **Build queries** - Leverage the graph structure
4. **Integrate with CI/CD** - Automate schema deployment
5. **Share with team** - Version control your YAML files

---

## 📚 Additional Resources

- [NEO4J_SETUP.md](NEO4J_SETUP.md) - Detailed Neo4j installation guide
- [PARSER.md](PARSER.md) - YAML schema reference
- [VALIDATOR.md](VALIDATOR.md) - Validation rules
- [COMPILER.md](COMPILER.md) - Cypher generation details
- [VISUALIZER.md](VISUALIZER.md) - Visualization options

---

**🎉 Happy graph modeling with grai.build!**

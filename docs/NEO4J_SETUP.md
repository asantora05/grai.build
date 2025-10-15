# 🚀 Neo4j Local Setup Guide

Complete guide to using grai.build with a local Neo4j instance.

---

## 📋 Prerequisites

- Python 3.11+ installed
- Docker Desktop (recommended) OR Neo4j Desktop
- Terminal/Command line access
- grai.build project already installed

---

## 🐳 Option 1: Neo4j with Docker (Recommended)

### Step 1: Install Docker Desktop

Download and install Docker Desktop:

- **macOS**: https://www.docker.com/products/docker-desktop/
- Follow installation instructions and start Docker Desktop

### Step 2: Run Neo4j Container

Open your terminal and run:

```bash
docker run \
  --name neo4j-grai \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graipassword \
  -v $HOME/neo4j/data:/data \
  -v $HOME/neo4j/logs:/logs \
  -d \
  neo4j:latest
```

**What this does:**

- Creates a container named `neo4j-grai`
- Exposes port `7474` for browser interface
- Exposes port `7687` for Bolt protocol (what grai uses)
- Sets password to `graipassword` (change this if needed)
- Persists data to `~/neo4j/data` on your Mac
- Runs in detached mode (background)

### Step 3: Verify Neo4j is Running

```bash
# Check container status
docker ps | grep neo4j-grai

# Check logs
docker logs neo4j-grai
```

You should see logs indicating Neo4j started successfully.

### Step 4: Access Neo4j Browser

Open your browser and go to:

```
http://localhost:7474
```

**Login credentials:**

- Username: `neo4j`
- Password: `graipassword`

You should see the Neo4j Browser interface. Try running:

```cypher
RETURN "Hello, Neo4j!" AS message
```

### Step 5: Useful Docker Commands

```bash
# Stop Neo4j
docker stop neo4j-grai

# Start Neo4j (after stopping)
docker start neo4j-grai

# Restart Neo4j
docker restart neo4j-grai

# View logs
docker logs -f neo4j-grai

# Remove container (keeps data)
docker rm neo4j-grai

# Remove container AND data
docker rm -v neo4j-grai
rm -rf ~/neo4j
```

---

## 🖥️ Option 2: Neo4j Desktop

### Step 1: Download Neo4j Desktop

Download from: https://neo4j.com/download/

### Step 2: Install and Launch

1. Install Neo4j Desktop
2. Launch the application
3. Create a new Project (e.g., "grai-project")
4. Create a new Database (e.g., "grai-db")

### Step 3: Configure Database

1. Click on your database
2. Go to Settings
3. Note the connection details:
   - **Bolt URL**: `bolt://localhost:7687`
   - **Username**: `neo4j`
   - **Password**: Set during database creation

### Step 4: Start Database

Click the "Start" button on your database.

---

## 🔧 Configure grai.build

### Step 1: Install Neo4j Python Driver

The `neo4j` driver should already be installed if you have grai-build installed. Verify:

```bash
pip show neo4j
```

If not installed:

```bash
pip install neo4j
```

### Step 2: Create Your Project Directory

**Important:** For real-world use, create your project in a separate directory (not in the grai.build source repo).

```bash
# Create a new project directory anywhere you want
mkdir -p ~/my-projects/my-graph-project
cd ~/my-projects/my-graph-project

# Initialize a new grai project
grai init

# Or copy the example template (replace with your actual path)
cp -r /path/to/grai.build/templates/* .
```

Your project structure should look like:

```
~/my-projects/my-graph-project/
├── grai.yml              # Project manifest
├── entities/
│   ├── customer.yml
│   └── product.yml
├── relations/
│   └── purchased.yml
└── target/               # Will be created by grai build
```

### Step 3: Update Project Configuration

Edit your `grai.yml` file:

```yaml
# grai.yml
name: my-graph-project
version: 1.0.0

config:
  neo4j:
    uri: bolt://localhost:7687
    database: neo4j
    user: neo4j
    password: graipassword # Change to your password

  compiler:
    backend: neo4j
    output_dir: target/neo4j

  validator:
    strict_mode: true
```

### Step 3: Test Connection

Create a test script to verify connection:

```bash
cat > test_connection.py << 'EOF'
"""Test Neo4j connection."""
from grai.core.loader.neo4j_loader import (
    connect_neo4j,
    verify_connection,
    get_database_info,
    close_connection,
)

# Connection details
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "graipassword"  # Change to your password
DATABASE = "neo4j"

def main():
    print("🔌 Testing Neo4j connection...")

    try:
        # Connect
        print(f"Connecting to {URI}...")
        driver = connect_neo4j(
            uri=URI,
            user=USER,
            password=PASSWORD,
        )
        print("✅ Connected successfully!")

        # Verify
        print(f"\n🔍 Verifying connection to database '{DATABASE}'...")
        if verify_connection(driver, database=DATABASE):
            print("✅ Connection verified!")
        else:
            print("❌ Connection verification failed")
            return

        # Get database info
        print(f"\n📊 Database information:")
        info = get_database_info(driver, database=DATABASE)
        print(f"  - Nodes: {info['node_count']}")
        print(f"  - Relationships: {info['relationship_count']}")
        print(f"  - Labels: {info['labels']}")
        print(f"  - Relationship types: {info['relationship_types']}")

        # Close
        close_connection(driver)
        print("\n✅ Connection test complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
EOF

python test_connection.py
```

**Expected output:**

```
🔌 Testing Neo4j connection...
Connecting to bolt://localhost:7687...
✅ Connected successfully!

🔍 Verifying connection to database 'neo4j'...
✅ Connection verified!

📊 Database information:
  - Nodes: 0
  - Relationships: 0
  - Labels: []
  - Relationship types: []

✅ Connection test complete!
```

---

## 📝 Use grai.build with Neo4j

### Step 1: Navigate to Your Project

```bash
# Go to your project directory (wherever you created it)
cd ~/my-projects/my-graph-project

# Or if you want to test with the templates first:
cd /path/to/grai.build/templates
```

### Step 2: Build and Validate

```bash
# Validate the project
grai validate

# Build (compile to Cypher without executing)
grai build

# View the compiled Cypher
cat target/neo4j/compiled.cypher
```

### Step 3: Execute Against Neo4j

```bash
# Execute with explicit connection details
grai run \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password graipassword
```

**Expected output:**

```
✅ Project validated successfully
📦 Compiling project...
✅ Compiled 2 entities and 1 relation
📁 Output written to: target/neo4j/compiled.cypher
🔌 Connecting to Neo4j at bolt://localhost:7687...
✅ Connected successfully
⚡ Executing Cypher statements...
✅ Executed 3 statements successfully
📊 Records affected: 0 (no data loaded yet)
⏱️  Execution time: 0.42s
```

### Step 4: Verify in Neo4j Browser

Open http://localhost:7474 and run:

```cypher
// Check what nodes were created
MATCH (n) RETURN labels(n), count(n)
```

You should see:

```
labels(n)     | count(n)
--------------|---------
["customer"]  | 0
["product"]   | 0
```

The schema is loaded, but no data yet (since we're using MERGE without actual data).

### Step 5: Load Sample Data

Create a test data file:

```bash
cat > load_sample_data.py << 'EOF'
"""Load sample data into Neo4j."""
from grai.core.loader.neo4j_loader import connect_neo4j, execute_cypher, close_connection

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "graipassword"

SAMPLE_DATA = """
// Create sample customers
CREATE (c1:customer {customer_id: 'C001', name: 'Alice Smith', region: 'US-West'});
CREATE (c2:customer {customer_id: 'C002', name: 'Bob Jones', region: 'US-East'});
CREATE (c3:customer {customer_id: 'C003', name: 'Charlie Brown', region: 'EU'});

// Create sample products
CREATE (p1:product {product_id: 'P001', name: 'Laptop', price: 999.99});
CREATE (p2:product {product_id: 'P002', name: 'Mouse', price: 29.99});
CREATE (p3:product {product_id: 'P003', name: 'Keyboard', price: 79.99});

// Create purchases
MATCH (c:customer {customer_id: 'C001'})
MATCH (p:product {product_id: 'P001'})
CREATE (c)-[:PURCHASED {order_id: 'O001', order_date: datetime('2024-01-15')}]->(p);

MATCH (c:customer {customer_id: 'C001'})
MATCH (p:product {product_id: 'P002'})
CREATE (c)-[:PURCHASED {order_id: 'O002', order_date: datetime('2024-01-15')}]->(p);

MATCH (c:customer {customer_id: 'C002'})
MATCH (p:product {product_id: 'P003'})
CREATE (c)-[:PURCHASED {order_id: 'O003', order_date: datetime('2024-01-20')}]->(p);

MATCH (c:customer {customer_id: 'C003'})
MATCH (p:product {product_id: 'P001'})
CREATE (c)-[:PURCHASED {order_id: 'O004', order_date: datetime('2024-02-01')}]->(p);
"""

def main():
    print("📦 Loading sample data into Neo4j...")

    driver = connect_neo4j(uri=URI, user=USER, password=PASSWORD)

    result = execute_cypher(driver, SAMPLE_DATA)

    if result.success:
        print(f"✅ Loaded successfully!")
        print(f"   Statements executed: {result.statements_executed}")
        print(f"   Records affected: {result.records_affected}")
        print(f"   Execution time: {result.execution_time:.2f}s")
    else:
        print(f"❌ Failed to load data")
        for error in result.errors:
            print(f"   {error}")

    close_connection(driver)

if __name__ == "__main__":
    main()
EOF

python load_sample_data.py
```

### Step 6: Query Your Data

In Neo4j Browser (http://localhost:7474):

```cypher
// See all nodes and relationships
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25

// Find customers who bought laptops
MATCH (c:customer)-[p:PURCHASED]->(prod:product {name: 'Laptop'})
RETURN c.name, c.region, p.order_date, prod.name, prod.price

// Count purchases per customer
MATCH (c:customer)-[p:PURCHASED]->()
RETURN c.name, count(p) AS purchase_count
ORDER BY purchase_count DESC
```

---

## 🎨 Visualize Your Graph

Use grai's built-in visualization:

```bash
# Generate interactive visualization
grai visualize --format d3 --open

# Or Cytoscape format
grai visualize --format cytoscape --open
```

This will open an interactive HTML visualization in your browser showing your graph schema.

---

## 🔄 Common Workflows

### Workflow 1: Iterative Development

```bash
# 1. Edit YAML files
vim entities/customer.yml

# 2. Validate changes
grai validate

# 3. Build and review compiled Cypher
grai build
cat target/neo4j/compiled.cypher

# 4. Execute when ready
grai run --uri bolt://localhost:7687 --user neo4j --password graipassword

# 5. Verify in browser
open http://localhost:7474
```

### Workflow 2: Fresh Start

```bash
# Clear the database and reload
python << 'EOF'
from grai.core.loader.neo4j_loader import connect_neo4j, clear_database, close_connection

driver = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="graipassword"
)

# WARNING: This deletes ALL data!
result = clear_database(driver, confirm=True)
print(f"✅ Cleared {result.records_affected} records")

close_connection(driver)
EOF

# Rebuild from scratch
grai run --uri bolt://localhost:7687 --user neo4j --password graipassword
python load_sample_data.py
```

### Workflow 3: Check Database State

```bash
# Get detailed info
python << 'EOF'
from grai.core.loader.neo4j_loader import connect_neo4j, get_database_info, close_connection

driver = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="graipassword"
)

info = get_database_info(driver)

print(f"📊 Database Statistics:")
print(f"   Nodes: {info['node_count']}")
print(f"   Relationships: {info['relationship_count']}")
print(f"   Labels: {', '.join(info['labels']) or 'None'}")
print(f"   Relationship types: {', '.join(info['relationship_types']) or 'None'}")

close_connection(driver)
EOF
```

---

## 🔍 Troubleshooting

### Issue: "Cannot connect to Neo4j"

**Check if Neo4j is running:**

```bash
# For Docker
docker ps | grep neo4j-grai

# Should show a running container
```

**Check logs:**

```bash
docker logs neo4j-grai
```

**Test connection manually:**

```bash
curl http://localhost:7474
# Should return HTTP 200
```

### Issue: "Authentication failed"

Make sure your password matches:

```bash
# Docker: password set with NEO4J_AUTH
docker run -e NEO4J_AUTH=neo4j/YOUR_PASSWORD ...

# In grai commands
grai run --password YOUR_PASSWORD
```

### Issue: "neo4j driver not installed"

Install the Python driver:

```bash
pip install neo4j
```

### Issue: Port already in use

Check what's using the ports:

```bash
lsof -i :7474
lsof -i :7687
```

Stop conflicting services or change Neo4j ports:

```bash
docker run -p 7475:7474 -p 7688:7687 ...
```

### Issue: Permission denied on data directory

Fix directory permissions:

```bash
mkdir -p ~/neo4j/data ~/neo4j/logs
chmod -R 755 ~/neo4j
```

---

## 📚 Next Steps

1. **Explore the CLI:**

   ```bash
   grai --help
   grai build --help
   ```

2. **Try other commands:**

   ```bash
   grai lineage --format mermaid
   grai export --format json
   grai visualize --format cytoscape
   ```

3. **Create your own entities:**

   - Copy `templates/entities/customer.yml` as a starting point
   - Define your own properties and relationships
   - Run `grai validate` and `grai build`

4. **Read the documentation:**
   - `docs/PARSER.md` - YAML structure
   - `docs/VALIDATOR.md` - Validation rules
   - `docs/COMPILER.md` - Cypher generation
   - `docs/VISUALIZER.md` - Visualization options

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Validate project
grai validate

# Build (compile only)
grai build

# Build and execute
grai run --uri bolt://localhost:7687 --user neo4j --password graipassword

# Visualize schema
grai visualize --format d3 --open

# View lineage
grai lineage --format mermaid

# Export IR
grai export --format json --output schema.json
```

### Connection Details (Docker)

```
URI:      bolt://localhost:7687
User:     neo4j
Password: graipassword (or what you set)
Browser:  http://localhost:7474
Database: neo4j
```

### Docker Commands

```bash
# Start
docker start neo4j-grai

# Stop
docker stop neo4j-grai

# Logs
docker logs -f neo4j-grai

# Remove
docker rm neo4j-grai
```

---

## ✅ Success Checklist

- [ ] Neo4j running (Docker or Desktop)
- [ ] Can access http://localhost:7474
- [ ] Can login with credentials
- [ ] Python neo4j driver installed (`pip install neo4j`)
- [ ] `test_connection.py` runs successfully
- [ ] `grai validate` passes
- [ ] `grai build` generates Cypher
- [ ] `grai run` loads schema
- [ ] Can query data in Neo4j Browser
- [ ] `grai visualize --open` shows graph

---

**🎉 You're ready to build knowledge graphs with grai.build and Neo4j!**

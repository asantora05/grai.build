# Troubleshooting

Common issues and solutions when using grai.build.

---

## Installation Issues

### "Command 'grai' not found"

**Problem:** After installing grai-build, the `grai` command is not available.

**Solutions:**

1. **Check if installed:**

   ```bash
   pip list | grep grai-build
   ```

2. **Install in development mode:**

   ```bash
   cd /path/to/grai.build
   pip install -e .
   ```

3. **Check PATH:**

   ```bash
   which grai
   echo $PATH
   ```

4. **Reinstall:**
   ```bash
   pip uninstall grai-build
   pip install grai-build
   ```

### "Module not found" errors

**Problem:** Import errors when running grai commands.

**Solution:** Install all required dependencies:

```bash
pip install pydantic pyyaml typer rich neo4j
```

Or install with dev dependencies:

```bash
pip install -e ".[dev]"
```

---

## Project Configuration Issues

### "No grai.yml found"

**Problem:** `grai` commands fail with "No grai.yml found in current directory or parents".

**Solutions:**

1. **Check current directory:**

   ```bash
   pwd
   ls -la grai.yml
   ```

2. **Navigate to project directory:**

   ```bash
   cd ~/my-projects/my-graph-project
   grai validate
   ```

3. **Specify project directory:**

   ```bash
   grai validate --project-dir /path/to/project
   ```

4. **Initialize a new project:**
   ```bash
   mkdir my-project
   cd my-project
   grai init
   ```

### "Invalid YAML syntax"

**Problem:** YAML parsing errors in entity or relation files.

**Common issues:**

1. **Incorrect indentation (must use spaces, not tabs):**

   ```yaml
   # ❌ Wrong
   entity: customer
   	properties:
   		- name: id

   # ✅ Correct
   entity: customer
   properties:
     - name: id
   ```

2. **Missing colons:**

   ```yaml
   # ❌ Wrong
   entity customer

   # ✅ Correct
   entity: customer
   ```

3. **Unquoted special characters:**

   ```yaml
   # ❌ Wrong
   name: Customer: Premium

   # ✅ Correct
   name: "Customer: Premium"
   ```

**Debug YAML syntax:**

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('entities/customer.yml'))"
```

---

## Validation Issues

### "Entity not found" in relation

**Problem:** Relation references an entity that doesn't exist.

**Solution:** Ensure the entity file exists and has the correct name:

```yaml
# relations/purchased.yml
relation: PURCHASED
from: customer # Must match entity: customer in entities/customer.yml
to: product # Must match entity: product in entities/product.yml
```

**Check entity names:**

```bash
# List all entity files
ls -1 entities/

# Grep for entity names
grep "^entity:" entities/*.yml
```

### "Missing required field"

**Problem:** Validation fails due to missing required fields.

**Required fields for entities:**

```yaml
entity: customer # Required
source: db.customers # Required (can be null for schema-only)
keys: [id] # Required
properties: # Required (can be empty list)
  - name: id # Required
    type: string # Required
```

**Required fields for relations:**

```yaml
relation: PURCHASED # Required
from: customer # Required
to: product # Required
source: db.orders # Required (can be null for schema-only)
mappings: # Required
  from_key: customer_id # Required
  to_key: product_id # Required
```

---

## Neo4j Connection Issues

### "Cannot connect to Neo4j"

**Problem:** `grai run` fails to connect to Neo4j.

**Solutions:**

1. **Check Neo4j is running:**

   ```bash
   # For Docker
   docker ps | grep neo4j

   # For local install
   neo4j status
   ```

2. **Test connection:**

   ```bash
   curl http://localhost:7474
   ```

3. **Verify credentials:**

   ```bash
   # Try connecting with cypher-shell
   cypher-shell -a bolt://localhost:7687 -u neo4j -p yourpassword
   ```

4. **Check firewall:**
   ```bash
   # Test ports are accessible
   nc -zv localhost 7474  # HTTP
   nc -zv localhost 7687  # Bolt
   ```

### "Authentication failed"

**Problem:** Invalid credentials for Neo4j.

**Solutions:**

1. **Check default password:**
   For fresh Neo4j install, default password is usually `neo4j`. You'll be prompted to change it on first login.

2. **Reset password:**

   ```bash
   # For Docker
   docker exec -it neo4j neo4j-admin set-initial-password newpassword

   # For local install
   neo4j-admin set-initial-password newpassword
   ```

3. **Use environment variables:**
   ```bash
   export NEO4J_PASSWORD=yourpassword
   grai run --uri bolt://localhost:7687 --user neo4j --password $NEO4J_PASSWORD
   ```

### "Database not found"

**Problem:** Specified database doesn't exist in Neo4j.

**Solution:** Create the database or use default `neo4j` database:

```cypher
-- In Neo4j Browser
CREATE DATABASE mydb;
```

Or update your `grai.yml`:

```yaml
config:
  neo4j:
    uri: bolt://localhost:7687
    database: neo4j # Use default database
```

---

## Data Loading Issues

### "NULL values in key fields"

**Problem:** Data loading succeeds but no nodes appear in Neo4j. Verbose mode shows NULL values in key fields.

**Cause:** Neo4j MERGE cannot use NULL values in pattern matching.

**Solutions:**

1. **Filter NULLs in source query:**

   ```yaml
   entity: customer
   source: |
     SELECT * FROM customers
     WHERE customer_id IS NOT NULL
   ```

2. **Use different key:**

   ```yaml
   entity: customer
   keys: [email] # Use a field that's always non-null
   ```

3. **Generate IDs for NULLs:**
   ```yaml
   entity: customer
   source: |
     SELECT
       COALESCE(customer_id, GENERATE_UUID()) as customer_id,
       name,
       email
     FROM customers
   ```

**Debug with verbose mode:**

```bash
grai load --verbose --limit 10
```

Look for output like:

```
Sample row: {'customer_id': None, 'name': 'John'}
```

### "No data loaded" but no errors

**Problem:** `grai load` reports success but no data appears in database.

**Solutions:**

1. **Use verbose mode to see what's happening:**

   ```bash
   grai load --verbose
   ```

2. **Check data source connection:**

   ```bash
   # For BigQuery
   gcloud auth application-default login
   ```

3. **Verify source query:**

   ```bash
   # Test your source query directly
   bq query --use_legacy_sql=false "SELECT * FROM your_dataset.your_table LIMIT 10"
   ```

4. **Check batch size:**
   ```yaml
   # In grai.yml, try smaller batches
   config:
     loader:
       batch_size: 100 # Default is 1000
   ```

---

## Build and Compilation Issues

### "Cypher compilation failed"

**Problem:** `grai build` fails to generate valid Cypher.

**Solutions:**

1. **Validate first:**

   ```bash
   grai validate
   ```

2. **Check generated Cypher:**

   ```bash
   grai build
   cat target/neo4j/compiled.cypher
   ```

3. **Test Cypher manually:**
   Copy generated Cypher into Neo4j Browser and run it to see the actual error.

### "Output directory not found"

**Problem:** Build fails because target directory doesn't exist.

**Solution:** grai should create it automatically, but you can create it manually:

```bash
mkdir -p target/neo4j
grai build
```

---

## Visualization Issues

### "Visualization won't open"

**Problem:** `grai visualize --open` doesn't open browser.

**Solutions:**

1. **Open manually:**

   ```bash
   grai visualize --format d3
   # Then open the file shown in output
   open target/visualizations/graph-d3.html
   ```

2. **Check default browser:**

   ```bash
   # On macOS
   export BROWSER=chrome
   grai visualize --open
   ```

3. **Check file was created:**
   ```bash
   ls -la target/visualizations/
   ```

---

## Performance Issues

### "Slow validation"

**Problem:** `grai validate` takes a long time on large projects.

**Solutions:**

1. **Use build cache:**

   ```bash
   grai build --use-cache
   ```

2. **Validate specific files:**

   ```bash
   grai validate entities/customer.yml
   ```

3. **Disable strict mode:**
   ```yaml
   # In grai.yml
   config:
     validator:
       strict_mode: false
   ```

### "Slow data loading"

**Problem:** `grai load` is very slow.

**Solutions:**

1. **Increase batch size:**

   ```yaml
   # In grai.yml
   config:
     loader:
       batch_size: 5000 # Increase from default 1000
   ```

2. **Use limit for testing:**

   ```bash
   grai load --limit 1000
   ```

3. **Load entities in parallel:**
   ```bash
   # Load entities separately
   grai load customers &
   grai load products &
   wait
   ```

---

## Common Errors and Solutions

### Pydantic ValidationError

**Error:**

```
pydantic.error_wrappers.ValidationError: 1 validation error for Entity
```

**Solution:** Check your YAML matches the required schema:

```yaml
entity: customer
source: analytics.customers
keys: [customer_id] # Must be a list
properties: # Must be a list of objects
  - name: customer_id
    type: string
```

### FileNotFoundError

**Error:**

```
FileNotFoundError: [Errno 2] No such file or directory: 'entities/customer.yml'
```

**Solution:** Check file path and current directory:

```bash
pwd
ls -la entities/
```

### YAML ParsingError

**Error:**

```
yaml.parser.ParserError: while parsing a block mapping
```

**Solution:** Check YAML indentation and syntax:

```bash
# Use a YAML validator
python -c "import yaml; yaml.safe_load(open('entities/customer.yml'))"
```

---

## Getting Help

If you're still stuck:

1. **Check existing issues:**
   [GitHub Issues](https://github.com/asantora05/grai.build/issues)

2. **Create a new issue:**
   Include:

   - grai.build version (`grai --version`)
   - Python version (`python --version`)
   - Operating system
   - Full error message
   - Relevant YAML files
   - Steps to reproduce

3. **Enable debug mode:**

   ```bash
   grai --debug validate
   grai --verbose load
   ```

4. **Check logs:**
   ```bash
   # If using Docker for Neo4j
   docker logs neo4j
   ```

---

## Useful Debug Commands

```bash
# Check grai installation
which grai
grai --version

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('entities/customer.yml'))"

# List all entities and relations
grep "^entity:" entities/*.yml
grep "^relation:" relations/*.yml

# Test Neo4j connection
cypher-shell -a bolt://localhost:7687 -u neo4j -p password "RETURN 1 as test"

# Check compiled Cypher
cat target/neo4j/compiled.cypher | head -50

# Run with verbose output
grai build --verbose
grai load --verbose --limit 10

# Export current schema
grai export --format json --output debug-schema.json
```

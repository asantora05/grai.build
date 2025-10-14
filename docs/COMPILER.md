# Cypher Compiler

The Cypher Compiler module generates Neo4j Cypher statements from validated entity and relation models.

## Overview

The compiler transforms declarative YAML definitions into executable Cypher scripts that create:

- Node constraints (unique keys)
- Node indexes (for faster lookups)
- MERGE statements for nodes (entities)
- MATCH...MERGE statements for relationships (relations)

## Quick Start

```python
from pathlib import Path
from grai.core.parser import load_project
from grai.core.compiler import compile_and_write

# Load project
project = load_project(Path("templates"))

# Compile and write to file
output_path = compile_and_write(project, output_dir=Path("target/neo4j"))
print(f"Compiled to: {output_path}")
```

## API Reference

### `compile_entity(entity: Entity) -> str`

Compiles a single entity into Cypher MERGE statements.

**Parameters:**

- `entity`: Entity model to compile

**Returns:** Cypher string with:

- Constraint creation (for keys)
- Index creation (for other properties)
- MERGE statement with property SET clauses

**Example:**

```python
from grai.core.models import Entity, Property
from grai.core.compiler import compile_entity

entity = Entity(
    name="customer",
    source="analytics.customers",
    keys=["customer_id"],
    properties=[
        Property(name="customer_id", type="string"),
        Property(name="name", type="string"),
        Property(name="region", type="string"),
    ],
)

cypher = compile_entity(entity)
print(cypher)
```

**Output:**

```cypher
// --- Entity: customer ---
// Source: analytics.customers
CREATE CONSTRAINT customer_customer_id_unique IF NOT EXISTS
FOR (n:customer) REQUIRE n.customer_id IS UNIQUE;

CREATE INDEX customer_name_index IF NOT EXISTS
FOR (n:customer) ON (n.name);

CREATE INDEX customer_region_index IF NOT EXISTS
FOR (n:customer) ON (n.region);

MERGE (n:customer {customer_id: row.customer_id})
SET n.name = row.name,
    n.region = row.region;
```

---

### `compile_relation(relation: Relation, project: Project) -> str`

Compiles a single relation into Cypher MATCH...MERGE statements.

**Parameters:**

- `relation`: Relation model to compile
- `project`: Project context (used to look up entity labels)

**Returns:** Cypher string with MATCH statements for nodes and MERGE for relationship

**Example:**

```python
from grai.core.models import Relation, RelationMapping, Property
from grai.core.compiler import compile_relation

relation = Relation(
    name="PURCHASED",
    from_entity="customer",
    to_entity="product",
    source="analytics.orders",
    mappings=RelationMapping(
        from_key="customer_id",
        to_key="product_id",
    ),
    properties=[
        Property(name="order_id", type="string"),
        Property(name="order_date", type="date"),
    ],
)

cypher = compile_relation(relation, project)
print(cypher)
```

**Output:**

```cypher
// --- Relation: PURCHASED ---
// From: customer → To: product
// Source: analytics.orders
MATCH (from:customer {customer_id: row.customer_id})
MATCH (to:product {product_id: row.product_id})
MERGE (from)-[r:PURCHASED]->(to)
SET r.order_id = row.order_id,
    r.order_date = row.order_date;
```

---

### `compile_project(project: Project, include_header: bool = True, include_constraints: bool = True) -> str`

Compiles an entire project into a single Cypher script.

**Parameters:**

- `project`: Project model containing all entities and relations
- `include_header`: Whether to include project metadata header (default: `True`)
- `include_constraints`: Whether to include constraint/index statements (default: `True`)

**Returns:** Complete Cypher script with all entities and relations

**Example:**

```python
from pathlib import Path
from grai.core.parser import load_project
from grai.core.compiler import compile_project

project = load_project(Path("templates"))
cypher = compile_project(project)
print(cypher)
```

**Output:**

```cypher
// ============================================
// Project: My Knowledge Graph
// Version: 1.0.0
// Description: Demo project for grai.build
// ============================================

// --- Entity: customer ---
// Source: analytics.customers
...

// --- Relation: PURCHASED ---
...
```

---

### `write_cypher_file(cypher: str, output_path: Path) -> Path`

Writes compiled Cypher to a file, creating directories as needed.

**Parameters:**

- `cypher`: Cypher script string
- `output_path`: Target file path

**Returns:** Path to the written file

**Raises:**

- `IOError`: If file cannot be written

**Example:**

```python
from pathlib import Path
from grai.core.compiler import compile_project, write_cypher_file

cypher = compile_project(project)
output_path = Path("target/neo4j/compiled.cypher")
write_cypher_file(cypher, output_path)
```

---

### `compile_and_write(project: Project, output_dir: Path, filename: str = "compiled.cypher") -> Path`

Convenience function that compiles a project and writes to file in one step.

**Parameters:**

- `project`: Project to compile
- `output_dir`: Directory for output file
- `filename`: Name of output file (default: `"compiled.cypher"`)

**Returns:** Path to written file

**Example:**

```python
from pathlib import Path
from grai.core.parser import load_project
from grai.core.compiler import compile_and_write

project = load_project(Path("templates"))
output_path = compile_and_write(
    project,
    output_dir=Path("target/neo4j"),
    filename="my_graph.cypher"
)
```

---

### `generate_load_csv_statements(project: Project, csv_dir: str = "file:///data") -> str`

Generates LOAD CSV statements for bulk data loading.

**Parameters:**

- `project`: Project model
- `csv_dir`: Base directory URL for CSV files (default: `"file:///data"`)

**Returns:** Cypher script with LOAD CSV statements

**Example:**

```python
from grai.core.compiler import generate_load_csv_statements

csv_cypher = generate_load_csv_statements(
    project,
    csv_dir="file:///var/lib/neo4j/import"
)
print(csv_cypher)
```

**Output:**

```cypher
// Load customer entities
LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/customer.csv' AS row
MERGE (n:customer {customer_id: row.customer_id})
SET n.name = row.name,
    n.region = row.region;

// Load PURCHASED relations
LOAD CSV WITH HEADERS FROM 'file:///var/lib/neo4j/import/PURCHASED.csv' AS row
MATCH (from:customer {customer_id: row.customer_id})
MATCH (to:product {product_id: row.product_id})
MERGE (from)-[r:PURCHASED]->(to)
SET r.order_id = row.order_id,
    r.order_date = row.order_date;
```

---

### `compile_schema_only(project: Project) -> str`

Generates only the schema (constraints and indexes), without any data loading statements.

**Parameters:**

- `project`: Project model

**Returns:** Cypher script with only CREATE CONSTRAINT and CREATE INDEX statements

**Example:**

```python
from grai.core.compiler import compile_schema_only

schema_cypher = compile_schema_only(project)
print(schema_cypher)
```

**Output:**

```cypher
// ============================================
// Schema for: My Knowledge Graph
// Version: 1.0.0
// ============================================

// --- Entity: customer ---
CREATE CONSTRAINT customer_customer_id_unique IF NOT EXISTS
FOR (n:customer) REQUIRE n.customer_id IS UNIQUE;

CREATE INDEX customer_name_index IF NOT EXISTS
FOR (n:customer) ON (n.name);
```

---

### `escape_cypher_string(value: str) -> str`

Escapes special characters in strings for Cypher.

**Parameters:**

- `value`: String to escape

**Returns:** Escaped string safe for Cypher

**Example:**

```python
from grai.core.compiler import escape_cypher_string

escaped = escape_cypher_string("O'Reilly's \"Book\"")
print(escaped)  # O\'Reilly\'s \"Book\"
```

## Cypher Output Format

### Node Constraints

For each key property in an entity:

```cypher
CREATE CONSTRAINT {entity_name}_{key_name}_unique IF NOT EXISTS
FOR (n:{entity_name}) REQUIRE n.{key_name} IS UNIQUE;
```

### Node Indexes

For each non-key property:

```cypher
CREATE INDEX {entity_name}_{property_name}_index IF NOT EXISTS
FOR (n:{entity_name}) ON (n.{property_name});
```

### Node MERGE Statements

```cypher
MERGE (n:{entity_name} {key1: row.key1, key2: row.key2})
SET n.prop1 = row.prop1,
    n.prop2 = row.prop2;
```

### Relationship MERGE Statements

```cypher
MATCH (from:{from_entity} {from_key: row.from_key})
MATCH (to:{to_entity} {to_key: row.to_key})
MERGE (from)-[r:{relation_name}]->(to)
SET r.prop1 = row.prop1,
    r.prop2 = row.prop2;
```

## Design Decisions

### Why MERGE instead of CREATE?

`MERGE` is idempotent — running the same script multiple times won't create duplicates. This makes the compiled Cypher safe for repeated execution during development.

### Why separate constraints and data loading?

Separating schema creation from data loading allows:

1. Creating the schema once, then loading data incrementally
2. Generating schema-only scripts for database initialization
3. Better error messages (constraint violations vs. data errors)

### Property Assignment Pattern

Properties are assigned using `row.property_name`, which assumes:

- Data is being loaded from CSV files (`LOAD CSV`)
- Or passed via parameters in application code
- The row variable is consistently used throughout

### Relationship Variable Naming

- Node variables: `n`, `from`, `to`
- Relationship variables: `r`
- Row data: `row`

This follows Neo4j conventions and keeps scripts readable.

## Integration with Other Modules

The compiler integrates with:

1. **Parser**: Loads `Project` models from YAML
2. **Validator**: Should validate projects before compiling
3. **CLI** (future): Will call compiler in `grai build` command
4. **Loader** (future): Will execute compiled Cypher against Neo4j

## Usage in CLI (Planned)

```bash
# Compile project to Cypher
grai build

# Compile and execute
grai build --execute --uri bolt://localhost:7687

# Compile schema only
grai build --schema-only

# Generate LOAD CSV statements
grai build --load-csv --csv-dir file:///data
```

## Testing

The compiler has 20 comprehensive tests covering:

- Entity compilation with various property types
- Relation compilation with properties and key mappings
- Project compilation with multiple entities and relations
- File writing and directory creation
- CSV statement generation
- Schema-only compilation
- Edge cases and error handling

Run tests with:

```bash
pytest tests/test_compiler.py -v
```

## Coverage

Current coverage: **98%** (141 statements, 3 missed)

Missed lines are unreachable error paths in string escaping logic.

## Future Enhancements

- [ ] Support for relationship properties with constraints
- [ ] Generate Gremlin bytecode (in addition to Cypher)
- [ ] Add `IF NOT EXISTS` checks for data loading
- [ ] Support for composite unique constraints
- [ ] Generate migration scripts for schema changes
- [ ] Add `ON CREATE` and `ON MATCH` clauses for conditional properties
- [ ] Support for parameterized queries
- [ ] Add batching hints for large datasets

## See Also

- [Parser Documentation](PARSER.md)
- [Validator Documentation](VALIDATOR.md)
- [Project Progress](PROGRESS.md)

# API Reference

Python API reference for grai.build.

---

## Core Models

::: grai.core.models

### Entity

```python
from grai.core.models import Entity, Property

entity = Entity(
    entity="customer",
    source="analytics.customers",
    keys=["customer_id"],
    properties=[
        Property(name="customer_id", type="string"),
        Property(name="email", type="string"),
    ]
)
```

### Relation

```python
from grai.core.models import Relation, RelationMappings

relation = Relation(
    relation="PURCHASED",
    from_entity="customer",
    to_entity="product",
    source="analytics.orders",
    mappings=RelationMappings(
        from_key="customer_id",
        to_key="product_id"
    )
)
```

---

## Parser

::: grai.core.parser

### YAML Parser

```python
from grai.core.parser.yaml_parser import YAMLParser

parser = YAMLParser()

# Parse entity file
entity = parser.parse_entity_file("entities/customer.yml")

# Parse relation file
relation = parser.parse_relation_file("relations/purchased.yml")

# Parse entire project
project = parser.parse_project(".")
```

---

## Validator

::: grai.core.validator

### Schema Validator

```python
from grai.core.validator.validator import Validator
from grai.core.models import Project

validator = Validator()
project = Project(...)

# Validate project
result = validator.validate(project)

if result.is_valid:
    print("✅ Validation passed")
else:
    for error in result.errors:
        print(f"❌ {error}")
```

---

## Compiler

::: grai.core.compiler

### Cypher Compiler

```python
from grai.core.compiler.cypher_compiler import CypherCompiler
from grai.core.models import Entity, Relation

compiler = CypherCompiler()

# Compile entity
entity_cypher = compiler.compile_entity(entity)

# Compile relation
relation_cypher = compiler.compile_relation(relation)

# Compile entire project
project_cypher = compiler.compile_project(project)
```

---

## Loader

::: grai.core.loader

### Neo4j Loader

```python
from grai.core.loader.neo4j_loader import (
    connect_neo4j,
    execute_cypher,
    close_connection,
)

# Connect
driver = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="neo4j"
)

# Execute Cypher
cypher = "CREATE CONSTRAINT ..."
result = execute_cypher(driver, cypher)

if result.success:
    print(f"✅ Executed {result.statements_executed} statements")
    print(f"   Nodes created: {result.nodes_created}")
    print(f"   Properties set: {result.properties_set}")
else:
    for error in result.errors:
        print(f"❌ {error}")

# Close
close_connection(driver)
```

### BigQuery Loader

```python
from grai.core.loader.bigquery_loader import (
    BigQueryExtractor,
    load_entity_from_bigquery,
)

# Extract data
extractor = BigQueryExtractor(
    project_id="my-project",
    credentials_path="service-account.json"
)

# Load entity
result = load_entity_from_bigquery(
    entity=entity,
    bigquery_connection=extractor,
    neo4j_connection=driver,
    batch_size=1000,
    limit=None,
    verbose=True
)

print(f"✅ Loaded {result.rows_processed} rows")
print(f"   Duration: {result.duration_seconds}s")
```

---

## Profiles

::: grai.core.profiles

### Profile Configuration

```python
from grai.core.profiles import (
    BigQueryProfile,
    Neo4jProfile,
    TargetConfig,
)

# BigQuery profile
bq_profile = BigQueryProfile(
    project_id="my-project",
    dataset="my_dataset",
    credentials_path="/path/to/credentials.json"
)

# Neo4j profile
neo4j_profile = Neo4jProfile(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="neo4j"
)

# Target config
target = TargetConfig(
    bigquery=bq_profile,
    neo4j=neo4j_profile
)
```

---

## Lineage

::: grai.core.lineage

### Lineage Tracker

```python
from grai.core.lineage.lineage_tracker import LineageTracker

tracker = LineageTracker()

# Build lineage graph
lineage = tracker.build_lineage(project)

# Export as Mermaid
mermaid = tracker.export_mermaid(lineage)

# Export as DOT
dot = tracker.export_dot(lineage)

# Export as JSON
json_data = tracker.export_json(lineage)
```

---

## Visualizer

::: grai.core.visualizer

### Graph Visualizer

```python
from grai.core.visualizer.visualizer import Visualizer

visualizer = Visualizer()

# Generate D3.js visualization
html = visualizer.generate_d3(project, output="graph.html")

# Generate Cytoscape.js visualization
html = visualizer.generate_cytoscape(project, output="graph.html")

# Generate custom visualization
html = visualizer.generate_custom(
    project,
    template="custom_template.html",
    output="graph.html"
)
```

---

## CLI

### Main CLI

```python
from grai.cli.main import main_cli

# Programmatically invoke CLI
if __name__ == "__main__":
    main_cli()
```

---

## Type Definitions

### Common Types

```python
from typing import Optional, List, Dict, Any

# Entity types
EntityName = str
PropertyName = str
PropertyType = str

# Source types
SourceReference = Optional[str]

# Cypher types
CypherStatement = str
CypherStatements = List[CypherStatement]

# Result types
ValidationResult = Dict[str, Any]
CompilationResult = Dict[str, Any]
ExecutionResult = Dict[str, Any]
```

---

## Exceptions

### Custom Exceptions

```python
from grai.core.exceptions import (
    GraiError,
    ValidationError,
    CompilationError,
    ConnectionError,
    ExecutionError,
)

try:
    result = validator.validate(project)
except ValidationError as e:
    print(f"Validation failed: {e}")
except GraiError as e:
    print(f"General error: {e}")
```

---

## Utilities

### Common Utilities

```python
from grai.core.utils import (
    load_yaml,
    write_yaml,
    ensure_dir,
    hash_file,
)

# Load YAML
data = load_yaml("grai.yml")

# Write YAML
write_yaml(data, "output.yml")

# Ensure directory exists
ensure_dir("target/neo4j")

# Hash file for caching
hash_value = hash_file("entities/customer.yml")
```

---

## Usage Examples

### Complete Workflow

```python
from pathlib import Path
from grai.core.parser.yaml_parser import YAMLParser
from grai.core.validator.validator import Validator
from grai.core.compiler.cypher_compiler import CypherCompiler
from grai.core.loader.neo4j_loader import connect_neo4j, execute_cypher

# 1. Parse project
parser = YAMLParser()
project = parser.parse_project(Path.cwd())

# 2. Validate
validator = Validator()
result = validator.validate(project)

if not result.is_valid:
    for error in result.errors:
        print(f"❌ {error}")
    exit(1)

# 3. Compile
compiler = CypherCompiler()
cypher = compiler.compile_project(project)

# 4. Execute
driver = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

result = execute_cypher(driver, cypher)
print(f"✅ Executed successfully")
print(f"   Nodes created: {result.nodes_created}")
print(f"   Relationships created: {result.relationships_created}")
```

### Data Loading Workflow

```python
from grai.core.loader.bigquery_loader import (
    BigQueryExtractor,
    load_entity_from_bigquery,
)

# Setup connections
extractor = BigQueryExtractor(
    project_id="my-project",
    credentials_path="credentials.json"
)

driver = connect_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Load each entity
for entity in project.entities:
    print(f"Loading {entity.entity}...")

    result = load_entity_from_bigquery(
        entity=entity,
        bigquery_connection=extractor,
        neo4j_connection=driver,
        batch_size=1000,
        verbose=True
    )

    if result.success:
        print(f"✅ Loaded {result.rows_processed} rows")
    else:
        print(f"❌ Failed: {result.errors}")
```

---

## See Also

- [Getting Started](../getting-started.md) - Tutorial and examples
- [Command Reference](commands.md) - CLI commands
- [YAML Schema](yaml-schema.md) - Configuration reference

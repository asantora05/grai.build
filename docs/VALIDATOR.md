# Validator Implementation

## Overview

The validator module (`grai/core/validator/`) provides comprehensive validation for entity and relation definitions, ensuring project consistency and correctness before compilation.

## Features

### ✅ Validation Functions

1. **Project-Level Validation**

   - `validate_project()` - Complete project validation
   - `validate_unique_names()` - Check for duplicate entity/relation names
   - `validate_sources()` - Verify sources are defined

2. **Entity Validation**

   - `validate_entity()` - Validate individual entity
   - `validate_entity_references()` - Check entity references exist

3. **Relation Validation**

   - `validate_relation()` - Validate individual relation
   - `validate_key_mappings()` - Verify key mappings are valid

4. **Advanced Checks**
   - `validate_property_definitions()` - Check property consistency
   - `check_circular_dependencies()` - Detect circular relations

### ✅ Error Handling

- `ValidationError` - Base exception for validation errors
- `EntityReferenceError` - Invalid entity reference
- `KeyMappingError` - Invalid key mapping
- `CircularDependencyError` - Circular dependency detected
- `ValidationResult` - Rich result object with errors and warnings

## Usage Examples

### Validate Complete Project

```python
from grai.core.parser import load_project
from grai.core.validator import validate_project

# Load and validate project
project = load_project("my-project/")
result = validate_project(project)

if result:
    print("✅ Project is valid!")
else:
    print("❌ Validation failed:")
    for error in result.errors:
        print(f"  • {error}")
```

### Validate Individual Entity

```python
from grai.core.models import Entity, Property, PropertyType
from grai.core.validator import validate_entity

entity = Entity(
    entity="customer",
    source="analytics.customers",
    keys=["customer_id"],
    properties=[
        Property(name="customer_id", type=PropertyType.STRING),
    ],
)

result = validate_entity(entity)
if result:
    print("✅ Entity is valid!")
```

### Validate Relation with Entity Index

```python
from grai.core.validator import validate_relation

# Build entity index
entity_index = {e.entity: e for e in project.entities}

# Validate relation
result = validate_relation(purchased_relation, entity_index)
if not result:
    for error in result.errors:
        print(f"Error: {error}")
```

### Use Strict Mode

```python
# In strict mode, warnings become errors
result = validate_project(project, strict=True)

# This will fail if there are any warnings
if not result:
    print("Failed strict validation")
```

## Validation Checks

### Entity Checks

| Check             | Type    | Description                           |
| ----------------- | ------- | ------------------------------------- |
| Keys required     | Error   | Entity must have at least one key     |
| Unique properties | Error   | No duplicate property names           |
| Key properties    | Warning | Keys should have property definitions |
| Valid source      | Error   | Source must be non-empty              |

### Relation Checks

| Check             | Type  | Description                            |
| ----------------- | ----- | -------------------------------------- |
| Entity references | Error | from/to entities must exist            |
| Key mappings      | Error | Keys must exist in respective entities |
| Unique properties | Error | No duplicate property names            |
| Valid source      | Error | Source must be non-empty               |

### Project Checks

| Check                 | Type    | Description                   |
| --------------------- | ------- | ----------------------------- |
| Unique entity names   | Error   | No duplicate entity names     |
| Unique relation names | Error   | No duplicate relation names   |
| Circular dependencies | Warning | Circular entity relationships |
| All entity checks     | Various | Run on all entities           |
| All relation checks   | Various | Run on all relations          |

## ValidationResult API

The `ValidationResult` class provides a rich result object:

```python
result = validate_project(project)

# Check if valid
if result.valid:
    print("Valid!")

# Access errors
for error in result.errors:
    print(f"Error: {error}")

# Access warnings
for warning in result.warnings:
    print(f"Warning: {warning}")

# String representation
print(result)  # Pretty-printed summary

# Boolean conversion
if result:  # Same as result.valid
    print("Valid!")
```

## Strict Mode

Strict mode treats warnings as errors:

```python
# Normal mode (warnings are OK)
result = validate_project(project, strict=False)
# valid=True, warnings=["Key 'id' has no property"]

# Strict mode (warnings fail validation)
result = validate_project(project, strict=True)
# valid=False, errors=["[Strict mode] Key 'id' has no property"]
```

## Circular Dependency Detection

The validator detects circular dependencies in the entity graph:

```python
# Entity A -> Entity B -> Entity A (circular)
result = validate_project(project, check_cycles=True)

if result.warnings:
    # Will show: "Circular dependency detected: a -> b -> a"
    print(result.warnings[0])
```

## Error Messages

All error messages include context:

```
Relation PURCHASED: References non-existent entity 'product'
Entity customer: Duplicate property names: name, email
Relation FOLLOWS: Key 'user_id' not found in entity 'customer' keys: ['customer_id']
```

## Integration with Parser

The validator integrates seamlessly with the parser:

```python
from grai.core.parser import load_project
from grai.core.validator import validate_project

# Load and validate in one go
project = load_project("templates/")
result = validate_project(project)

if result:
    print("✅ Ready to compile!")
else:
    print("❌ Fix these errors:")
    print(result)
```

## Test Coverage

- **27 tests** covering all functionality
- **91% code coverage**
- Tests for:
  - Valid entities and relations
  - Missing entity references
  - Invalid key mappings
  - Duplicate names
  - Circular dependencies
  - Strict mode
  - Error messages with context

## Implementation Details

### Entity Index

The validator builds an entity index for O(1) lookups:

```python
entity_index = {entity.entity: entity for entity in entities}
# Used for fast entity reference checking
```

### Circular Dependency Detection

Uses depth-first search (DFS) with recursion stack:

1. Build adjacency list from relations
2. Track visited nodes and recursion stack
3. Detect cycles when revisiting node in stack
4. Report full cycle path

### Error Context

All errors include context (entity/relation name) for easy debugging:

```python
result.add_error(
    "Key 'id' not found",
    context="Relation PURCHASED"
)
# Output: "Relation PURCHASED: Key 'id' not found"
```

## Performance

- Fast validation using indexed lookups
- Single-pass validation for most checks
- Minimal memory overhead
- Efficient cycle detection with DFS

## API Reference

### Main Functions

| Function                                       | Description              | Returns            |
| ---------------------------------------------- | ------------------------ | ------------------ |
| `validate_project(project)`                    | Validate entire project  | `ValidationResult` |
| `validate_entity(entity)`                      | Validate single entity   | `ValidationResult` |
| `validate_relation(relation, index)`           | Validate single relation | `ValidationResult` |
| `validate_entity_references(relations, index)` | Check entity refs        | `ValidationResult` |
| `validate_key_mappings(relations, index)`      | Check key mappings       | `ValidationResult` |

### ValidationResult Methods

| Method                      | Description         | Returns |
| --------------------------- | ------------------- | ------- |
| `add_error(msg, context)`   | Add error message   | `None`  |
| `add_warning(msg, context)` | Add warning message | `None`  |
| `__bool__()`                | Check if valid      | `bool`  |
| `__str__()`                 | Pretty-print result | `str`   |

## Best Practices

1. **Always validate after parsing**

   ```python
   project = load_project(".")
   result = validate_project(project)
   if not result:
       sys.exit(1)
   ```

2. **Use strict mode in CI/CD**

   ```python
   result = validate_project(project, strict=True)
   # Zero tolerance for warnings
   ```

3. **Check validation before compilation**

   ```python
   if validate_project(project):
       compile_project(project)  # Safe to compile
   ```

4. **Use entity index for multiple validations**
   ```python
   entity_index = build_entity_index(entities)
   for relation in relations:
       validate_relation(relation, entity_index)
   ```

## Example Output

```
Errors (2):
  • Relation PURCHASED: References non-existent entity 'product'
  • Entity customer: Duplicate property names: email

Warnings (1):
  • Entity customer: Key 'customer_id' does not have a corresponding property definition
```

---

**Status**: ✅ Complete and tested
**Coverage**: 91% (190 statements, 17 missed)
**Tests**: 27 passing

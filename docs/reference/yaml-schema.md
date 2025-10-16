# YAML Schema Reference

Complete reference for entity and relation YAML definitions.

---

## Entity Schema

Entities represent nodes in your graph.

### Basic Structure

```yaml
entity: string # Required: Entity name
source: string | null # Required: Data source reference
keys: list[string] # Required: Unique identifier field(s)
properties: list[Property] # Required: List of properties
description: string # Optional: Entity description
tags: list[string] # Optional: Tags for organization
metadata: dict # Optional: Custom metadata
```

### Example

```yaml
entity: customer
source: analytics.customers
keys: [customer_id]
description: Customer entities from the CRM system
tags: [core, customer]
properties:
  - name: customer_id
    type: string
    description: Unique customer identifier
  - name: email
    type: string
  - name: created_at
    type: datetime
```

### Fields

#### `entity` (required)

The name of the entity. This becomes the Neo4j node label.

- **Type:** string
- **Rules:** Alphanumeric + underscore, no spaces
- **Example:** `customer`, `product`, `order_item`

#### `source` (required)

Reference to the data source. Can be `null` for schema-only entities.

- **Type:** string or null
- **Format:** Depends on source type
  - BigQuery: `project.dataset.table` or `dataset.table`
  - SQL: `schema.table`
  - null: Schema-only (no data loading)

```yaml
# BigQuery
source: my_project.analytics.customers

# Schema-only
source: null
```

#### `keys` (required)

List of property names that uniquely identify the entity.

- **Type:** list of strings
- **Rules:** Each key must exist in `properties`
- **Creates:** Unique constraint in Neo4j

```yaml
# Single key
keys: [customer_id]

# Composite key
keys: [order_id, line_item_id]
```

#### `properties` (required)

List of properties for the entity.

- **Type:** list of Property objects
- **Minimum:** 1 property (the key)
- **See:** [Property Schema](#property-schema)

```yaml
properties:
  - name: id
    type: string
  - name: name
    type: string
  - name: age
    type: integer
```

#### `description` (optional)

Human-readable description of the entity.

- **Type:** string
- **Usage:** Displayed in documentation

```yaml
description: |
  Customer entities from our CRM system.
  Includes both active and inactive customers.
```

#### `tags` (optional)

Tags for categorizing entities.

- **Type:** list of strings
- **Usage:** Filtering, organization, documentation

```yaml
tags: [core, customer, pii]
```

#### `metadata` (optional)

Custom metadata for your use.

- **Type:** dictionary
- **Usage:** Store any custom information

```yaml
metadata:
  owner: data-team
  sla: 24h
  pii: true
```

---

## Relation Schema

Relations represent edges in your graph.

### Basic Structure

```yaml
relation: string # Required: Relation type name
from: string # Required: Source entity name
to: string # Required: Target entity name
source: string | null # Required: Data source reference
mappings: Mappings # Required: Key mappings
properties: list[Property] # Optional: Relation properties
description: string # Optional: Relation description
tags: list[string] # Optional: Tags
metadata: dict # Optional: Custom metadata
```

### Example

```yaml
relation: PURCHASED
from: customer
to: product
source: analytics.orders
description: Customer purchase transactions
tags: [transaction, core]
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
```

### Fields

#### `relation` (required)

The type of relationship. This becomes the Neo4j relationship type.

- **Type:** string
- **Convention:** UPPER_CASE with underscores
- **Example:** `PURCHASED`, `FOLLOWS`, `WORKS_FOR`

```yaml
relation: PURCHASED
```

#### `from` (required)

The source entity for the relationship.

- **Type:** string
- **Rules:** Must match an existing entity name
- **Example:** `customer`

```yaml
from: customer
```

#### `to` (required)

The target entity for the relationship.

- **Type:** string
- **Rules:** Must match an existing entity name
- **Can be same as `from`:** For self-referencing relations

```yaml
to: product

# Self-referencing
from: user
to: user
```

#### `source` (required)

Reference to the data source for the relation data.

- **Type:** string or null
- **Format:** Same as entity source

```yaml
source: analytics.orders
source: null  # Schema-only
```

#### `mappings` (required)

Defines how to join entities.

- **Type:** Mappings object
- **Fields:**
  - `from_key`: Property name in `from` entity
  - `to_key`: Property name in `to` entity

```yaml
mappings:
  from_key: customer_id
  to_key: product_id
```

For composite keys:

```yaml
mappings:
  from_key: [order_id, line_id]
  to_key: [product_order_id, product_line_id]
```

#### `properties` (optional)

Properties of the relationship itself.

- **Type:** list of Property objects
- **Example:** order_date, quantity, amount

```yaml
properties:
  - name: order_date
    type: datetime
  - name: quantity
    type: integer
```

---

## Property Schema

Properties define attributes of entities and relations.

### Structure

```yaml
name: string # Required: Property name
type: string # Required: Data type
description: string # Optional: Description
required: boolean # Optional: Is required (default: false)
indexed: boolean # Optional: Create index (default: false)
unique: boolean # Optional: Unique constraint (default: false)
default: any # Optional: Default value
```

### Example

```yaml
properties:
  - name: email
    type: string
    description: Customer email address
    required: true
    indexed: true
    unique: true

  - name: age
    type: integer
    required: false
    default: 0

  - name: created_at
    type: datetime
    required: true
    indexed: true
```

### Fields

#### `name` (required)

Property name.

- **Type:** string
- **Rules:** Valid Neo4j property name
- **Example:** `customer_id`, `email`, `created_at`

#### `type` (required)

Data type of the property.

- **Type:** string
- **Values:**

| Type       | Neo4j Type | Python Type | Example                |
| ---------- | ---------- | ----------- | ---------------------- |
| `string`   | String     | str         | `"Alice"`              |
| `integer`  | Integer    | int         | `42`                   |
| `float`    | Float      | float       | `99.99`                |
| `boolean`  | Boolean    | bool        | `true`                 |
| `datetime` | DateTime   | datetime    | `2024-01-15T10:30:00Z` |
| `date`     | Date       | date        | `2024-01-15`           |
| `time`     | Time       | time        | `10:30:00`             |
| `list`     | List       | list        | `["tag1", "tag2"]`     |
| `map`      | Map        | dict        | `{"key": "value"}`     |

```yaml
- name: id
  type: string

- name: price
  type: float

- name: active
  type: boolean

- name: created_at
  type: datetime

- name: tags
  type: list
```

#### `description` (optional)

Human-readable description.

```yaml
- name: email
  type: string
  description: Primary contact email for the customer
```

#### `required` (optional)

Whether the property is required.

- **Type:** boolean
- **Default:** false
- **Effect:** Validation only (not enforced in Neo4j)

```yaml
- name: email
  type: string
  required: true
```

#### `indexed` (optional)

Whether to create an index on this property.

- **Type:** boolean
- **Default:** false
- **Effect:** Creates Neo4j index for faster lookups

```yaml
- name: email
  type: string
  indexed: true
```

#### `unique` (optional)

Whether the property must be unique.

- **Type:** boolean
- **Default:** false
- **Effect:** Creates unique constraint in Neo4j

```yaml
- name: email
  type: string
  unique: true
```

#### `default` (optional)

Default value if not provided.

- **Type:** any (matching property type)
- **Usage:** Data loading fallback

```yaml
- name: status
  type: string
  default: "active"

- name: quantity
  type: integer
  default: 1
```

---

## Complete Examples

### E-commerce Example

**Customer Entity:**

```yaml
entity: customer
source: analytics.customers
keys: [customer_id]
description: Customer master data
tags: [core, pii]
properties:
  - name: customer_id
    type: string
    required: true
  - name: email
    type: string
    required: true
    indexed: true
    unique: true
  - name: name
    type: string
    required: true
  - name: region
    type: string
    indexed: true
  - name: created_at
    type: datetime
    required: true
  - name: lifetime_value
    type: float
    default: 0.0
```

**Product Entity:**

```yaml
entity: product
source: catalog.products
keys: [product_id]
description: Product catalog
tags: [core, catalog]
properties:
  - name: product_id
    type: string
    required: true
  - name: name
    type: string
    required: true
    indexed: true
  - name: category
    type: string
    indexed: true
  - name: price
    type: float
    required: true
  - name: in_stock
    type: boolean
    default: true
```

**Purchase Relation:**

```yaml
relation: PURCHASED
from: customer
to: product
source: analytics.orders
description: Customer purchase transactions
tags: [transaction, revenue]
mappings:
  from_key: customer_id
  to_key: product_id
properties:
  - name: order_id
    type: string
    required: true
    indexed: true
  - name: order_date
    type: datetime
    required: true
    indexed: true
  - name: quantity
    type: integer
    required: true
    default: 1
  - name: unit_price
    type: float
    required: true
  - name: total_amount
    type: float
    required: true
  - name: status
    type: string
    default: "pending"
```

### Social Network Example

**User Entity:**

```yaml
entity: user
source: social.users
keys: [user_id]
description: Social network users
tags: [core, user]
properties:
  - name: user_id
    type: string
    required: true
  - name: username
    type: string
    required: true
    indexed: true
    unique: true
  - name: email
    type: string
    required: true
    indexed: true
    unique: true
  - name: display_name
    type: string
  - name: bio
    type: string
  - name: joined_at
    type: datetime
    required: true
  - name: verified
    type: boolean
    default: false
```

**Follow Relation (self-referencing):**

```yaml
relation: FOLLOWS
from: user
to: user
source: social.follows
description: User follow relationships
tags: [social, engagement]
mappings:
  from_key: follower_id
  to_key: followee_id
properties:
  - name: followed_at
    type: datetime
    required: true
    indexed: true
  - name: notifications_enabled
    type: boolean
    default: true
```

---

## Validation Rules

grai.build validates your YAML against these rules:

### Entity Validation

- ✅ `entity` name is unique across project
- ✅ All `keys` exist in `properties`
- ✅ Property names are unique within entity
- ✅ Property types are valid
- ✅ If `source` is not null, it matches a configured source

### Relation Validation

- ✅ `from` entity exists
- ✅ `to` entity exists
- ✅ `from_key` exists in `from` entity's properties
- ✅ `to_key` exists in `to` entity's properties
- ✅ Property names are unique within relation
- ✅ Property types are valid

### Property Validation

- ✅ `name` is valid identifier
- ✅ `type` is one of supported types
- ✅ `default` value matches `type`
- ✅ If `unique: true`, then `indexed: true` (implied)

---

## Tips and Best Practices

### Naming Conventions

```yaml
# Entities: lowercase, singular
entity: customer
entity: product
entity: order_item

# Relations: UPPERCASE, descriptive verb/preposition
relation: PURCHASED
relation: BELONGS_TO
relation: WORKS_FOR

# Properties: lowercase, snake_case
properties:
  - name: customer_id
  - name: created_at
  - name: total_amount
```

### Key Selection

```yaml
# ✅ Good: Use stable, immutable keys
keys: [customer_id]
keys: [email]  # If email never changes

# ❌ Bad: Don't use mutable fields as keys
keys: [name]  # Names can change
keys: [status]  # Status is mutable
```

### Indexing Strategy

```yaml
# Index fields you'll query frequently
properties:
  - name: email
    type: string
    indexed: true # For lookups

  - name: created_at
    type: datetime
    indexed: true # For range queries

  - name: internal_id
    type: string
    indexed: false # Rarely queried
```

### Required vs Optional

```yaml
# Mark fields required if they're critical
properties:
  - name: customer_id
    type: string
    required: true # Always needed

  - name: phone
    type: string
    required: false # Optional contact method
    default: null
```

---

## See Also

- [Getting Started](../getting-started.md) - Tutorial with examples
- [Command Reference](commands.md) - CLI commands
- [Data Loading](../data-loading.md) - Loading data from sources

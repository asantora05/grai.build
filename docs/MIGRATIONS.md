# Schema Migrations

## Overview

grai.build's migration system provides version-controlled schema evolution for your knowledge graph, inspired by [Alembic](https://alembic.sqlalchemy.org/) (Python/SQL) and [Flyway](https://flywaydb.org/) (Java/SQL). Track changes to your entities, relations, and properties over time, and safely apply or rollback schema modifications.

## Key Features

- 📝 **Automatic Change Detection** - Compares your current schema against previous versions
- 🔄 **Bidirectional Migrations** - Every migration includes upgrade and downgrade paths
- 🔒 **Version Tracking** - Maintains migration history in Neo4j
- 🧪 **Dry-Run Mode** - Preview changes before applying them
- 📊 **Execution Statistics** - Track what changed and how long it took
- ✅ **Checksum Verification** - Ensures migration integrity

## Quick Start

### 1. Make Schema Changes

Edit your entity or relation YAML files as usual. For example, add a new property to `entities/customer.yml`:

```yaml
entity: customer
source: analytics.customers
keys: [customer_id]
properties:
  - name: customer_id
    type: string
  - name: name
    type: string
  - name: email # NEW PROPERTY
    type: string
```

### 2. Generate a Migration

Create a migration from your schema changes:

```bash
grai migrate-generate --message "Add email to customer entity"
```

**Output:**

```
✓ Migration created: 20251112_143052_add_email_to_customer_entity.yml
Changes: 1 entities modified
Version: 20251112_143052
Up statements: 1
Down statements: 1
```

This creates a migration file in `migrations/20251112_143052_add_email_to_customer_entity.yml`.

### 3. Review the Migration

Inspect the generated migration file:

```bash
cat migrations/20251112_143052_add_email_to_customer_entity.yml
```

```yaml
version: "20251112_143052"
description: Add email to customer entity
author: auto-generated
timestamp: "2025-11-12T14:30:52.123456"
checksum: a1b2c3d4e5f6...
changes:
  entities:
    - name: customer
      change_type: modified
      properties_added:
        - name: email
          type: string
          required: false
          description: null
          default: null
      properties_modified: []
      properties_removed: []
      keys_changed: false
      old_keys: [customer_id]
      new_keys: [customer_id]
  relations: []
up:
  - "MATCH (n:customer) SET n.email = null"
down:
  - "MATCH (n:customer) REMOVE n.email"
```

### 4. Check Migration Status

See which migrations are pending:

```bash
grai migrate-status \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password yourpassword
```

**Output:**

```
Checking migration status...

Pending Migrations: 1
  • 20251112_143052: Add email to customer entity
```

### 5. Apply the Migration

Apply pending migrations to Neo4j:

```bash
# Dry-run first to preview
grai migrate-apply \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password yourpassword \
  --dry-run

# Then apply for real
grai migrate-apply \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password yourpassword
```

**Output:**

```
Migrations applying...

Found 1 pending migration(s):

• 20251112_143052: Add email to customer entity
  Statements: 1
  ✓ Applied in 45ms

✓ All migrations applied successfully
```

### 6. Rollback if Needed

If something goes wrong, rollback the last migration:

```bash
grai migrate-rollback \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password yourpassword
```

**Output:**

```
Rolling back migration...

✓ Rolled back migration 20251112_143052
Time: 32ms
```

## Common Workflows

### Adding a New Entity

**1. Create the entity definition** (`entities/product.yml`):

```yaml
entity: product
source: analytics.products
keys: [product_id]
properties:
  - name: product_id
    type: string
  - name: name
    type: string
  - name: price
    type: float
```

**2. Generate migration:**

```bash
grai migrate-generate --message "Add product entity"
```

**Generated Cypher (up):**

```cypher
CREATE CONSTRAINT product_unique IF NOT EXISTS
FOR (n:product) REQUIRE (n.product_id) IS UNIQUE
```

**Generated Cypher (down):**

```cypher
MATCH (n:product) DETACH DELETE n
DROP CONSTRAINT product_unique IF EXISTS
```

### Adding a Relation

**1. Create the relation definition** (`relations/purchased.yml`):

```yaml
relation: PURCHASED
from: customer
to: product
source: analytics.orders
mappings:
  from_key: customer_id
  to_key: product_id
properties:
  - name: order_date
    type: datetime
  - name: quantity
    type: integer
```

**2. Generate migration:**

```bash
grai migrate-generate --message "Add PURCHASED relation"
```

**Generated Cypher (up):**

```cypher
// Relation PURCHASED added - schema only
```

**Generated Cypher (down):**

```cypher
MATCH ()-[r:PURCHASED]->() DELETE r
```

### Modifying Property Types

**Before** (`entities/customer.yml`):

```yaml
properties:
  - name: age
    type: string # Was storing as string
```

**After:**

```yaml
properties:
  - name: age
    type: integer # Now storing as integer
```

**Generate migration:**

```bash
grai migrate-generate --message "Change customer age to integer"
```

The differ will detect this as a `MODIFIED` property change with type conversion.

### Changing Entity Keys

**Before:**

```yaml
entity: customer
keys: [customer_id]
```

**After:**

```yaml
entity: customer
keys: [customer_id, email] # Composite key
```

**Generated Cypher (up):**

```cypher
DROP CONSTRAINT customer_unique IF EXISTS
CREATE CONSTRAINT customer_unique IF NOT EXISTS
FOR (n:customer) REQUIRE (n.customer_id, n.email) IS UNIQUE
```

## CLI Command Reference

### `grai migrate-generate`

Generate a new migration from schema changes.

**Options:**

- `--message`, `-m` - Description for the migration (optional)
- `path` - Project directory (default: current directory)

**Examples:**

```bash
# With custom message
grai migrate-generate -m "Add loyalty program fields"

# Specify project directory
grai migrate-generate /path/to/project -m "Update schema"

# Auto-generated description (from changes detected)
grai migrate-generate
```

**When to use:**

- After modifying entity or relation YAML files
- Before committing schema changes to git
- When you want to document what changed

### `grai migrate-status`

Show migration status (pending and applied).

**Options:**

- `--uri` - Neo4j connection URI (default: `bolt://localhost:7687`)
- `--user` - Neo4j username (default: `neo4j`)
- `--password` - Neo4j password (required, prompted if not provided)
- `path` - Project directory (default: current directory)

**Examples:**

```bash
# Basic usage (will prompt for password)
grai migrate-status

# With credentials
grai migrate-status --uri bolt://prod-server:7687 --user admin --password secret

# Different project
grai migrate-status /path/to/project
```

**Output includes:**

- Applied migrations with timestamps and status
- Pending migrations list
- Migration versions and descriptions

### `grai migrate-apply`

Apply pending migrations to Neo4j.

**Options:**

- `--uri` - Neo4j connection URI
- `--user` - Neo4j username
- `--password` - Neo4j password
- `--dry-run` - Preview without executing (default: false)
- `path` - Project directory

**Examples:**

```bash
# Dry-run first (recommended)
grai migrate-apply --dry-run

# Apply all pending migrations
grai migrate-apply

# Apply to production (with explicit credentials)
grai migrate-apply \
  --uri bolt://prod.example.com:7687 \
  --user admin \
  --password $PROD_PASSWORD
```

**Safety tips:**

- Always run `--dry-run` first in production
- Review generated Cypher before applying
- Backup your Neo4j database before major migrations
- Test migrations in development first

### `grai migrate-rollback`

Rollback the last applied migration.

**Options:**

- `--uri` - Neo4j connection URI
- `--user` - Neo4j username
- `--password` - Neo4j password
- `--version` - Specific version to rollback (default: last migration)
- `path` - Project directory

**Examples:**

```bash
# Rollback last migration
grai migrate-rollback

# Rollback specific version
grai migrate-rollback --version 20251112_143052

# Rollback on production
grai migrate-rollback \
  --uri bolt://prod.example.com:7687 \
  --user admin \
  --password $PROD_PASSWORD
```

**Important:**

- Rollback executes the "down" Cypher script
- Data may be lost when rolling back (e.g., dropping properties)
- Only rolls back one migration at a time
- Cannot rollback if migration status is "failed"

## Migration File Structure

### Directory Layout

```
your-project/
├── grai.yml
├── entities/
│   ├── customer.yml
│   └── product.yml
├── relations/
│   └── purchased.yml
└── migrations/
    ├── 20251112_143052_add_email_to_customer.yml
    ├── 20251112_150030_add_product_entity.yml
    └── 20251112_151545_add_purchased_relation.yml
```

### Migration File Format

Each migration is stored as a YAML file with the following structure:

```yaml
version: "20251112_143052" # Timestamp-based version
description: "Add email to customer" # Human-readable description
author: "auto-generated" # Who created it
timestamp: "2025-11-12T14:30:52" # When it was created
checksum: "a1b2c3d4e5f6..." # SHA256 for integrity

changes: # Structured change representation
  entities:
    - name: customer
      change_type: modified
      properties_added: [...]
      properties_modified: [...]
      properties_removed: [...]
      keys_changed: false
      old_keys: [...]
      new_keys: [...]
  relations:
    - name: PURCHASED
      change_type: added
      from_entity_changed: false
      to_entity_changed: false
      properties_added: [...]

up: # Cypher to apply migration
  - "MATCH (n:customer) SET n.email = null"
  - "CREATE CONSTRAINT ..."

down: # Cypher to rollback migration
  - "MATCH (n:customer) REMOVE n.email"
  - "DROP CONSTRAINT ..."
```

## Change Types

The migration system detects and categorizes different types of changes:

### Entity Changes

| Change Type | Description               | Example                       |
| ----------- | ------------------------- | ----------------------------- |
| `ADDED`     | New entity added          | Adding `product` entity       |
| `MODIFIED`  | Entity definition changed | Adding property to `customer` |
| `REMOVED`   | Entity removed            | Deleting `legacy_user` entity |

### Property Changes

| Change Type | Description                    | Example                       | Breaking? |
| ----------- | ------------------------------ | ----------------------------- | --------- |
| `ADDED`     | New property added             | `customer.email`              | No        |
| `MODIFIED`  | Property type/required changed | `age: string → integer`       | ⚠️ Yes    |
| `REMOVED`   | Property dropped               | Removing `customer.legacy_id` | ⚠️ Yes    |

### Relation Changes

| Change Type | Description                 | Example                       |
| ----------- | --------------------------- | ----------------------------- |
| `ADDED`     | New relation added          | Adding `PURCHASED`            |
| `MODIFIED`  | Relation definition changed | Adding properties to relation |
| `REMOVED`   | Relation removed            | Deleting `OLD_RELATION`       |

### Key Changes

| Change Type | Description          | Example                        | Breaking? |
| ----------- | -------------------- | ------------------------------ | --------- |
| `ADDED`     | New key property     | Adding `email` to keys         | No        |
| `REMOVED`   | Key property removed | Removing `legacy_id` from keys | ⚠️ Yes    |
| `MODIFIED`  | Keys changed         | `[id]` → `[id, email]`         | ⚠️ Yes    |

## State Tracking in Neo4j

Migrations are tracked in Neo4j using special `__GraiMigration` nodes:

```cypher
// Example migration node
CREATE (:__GraiMigration {
  version: '20251112_143052',
  description: 'Add email to customer entity',
  applied_at: datetime('2025-11-12T14:30:52'),
  status: 'applied',
  checksum: 'a1b2c3d4e5f6...',
  execution_time_ms: 45,
  error_message: null
})
```

### Migration Statuses

- `pending` - Migration file exists but not yet applied
- `applied` - Successfully executed
- `failed` - Execution failed (check `error_message`)
- `rolled_back` - Previously applied but then rolled back

### Querying Migration History

```cypher
// View all migrations
MATCH (m:__GraiMigration)
RETURN m.version, m.description, m.applied_at, m.status
ORDER BY m.applied_at DESC

// Find failed migrations
MATCH (m:__GraiMigration {status: 'failed'})
RETURN m.version, m.error_message

// Check if specific migration applied
MATCH (m:__GraiMigration {version: '20251112_143052'})
RETURN m.status, m.applied_at
```

## Best Practices

### Development Workflow

1. **Make schema changes** in your YAML files
2. **Generate migration** immediately: `grai migrate-generate`
3. **Review the generated Cypher** - ensure it does what you expect
4. **Test locally** - apply to local Neo4j and verify
5. **Commit migration files** to version control
6. **Apply in other environments** using `migrate-apply`

### Team Collaboration

When working with a team:

1. **Pull latest changes** from git before making schema edits
2. **Check migration status** to see what's pending: `grai migrate-status`
3. **Apply pending migrations** before creating new ones
4. **Resolve conflicts** if two people modified the same schema
5. **Never edit applied migrations** - create a new migration instead

### Production Deployment

For production environments:

1. **Test in staging first** with identical data
2. **Backup Neo4j** before applying migrations
3. **Use dry-run** to preview: `grai migrate-apply --dry-run`
4. **Review execution plan** carefully
5. **Apply during maintenance window** if making breaking changes
6. **Monitor execution time** and performance impact
7. **Have rollback plan ready** in case of issues

### Avoiding Breaking Changes

Some changes can break existing queries or lose data:

⚠️ **Breaking Changes:**

- Dropping entities or relations
- Dropping properties
- Changing property types
- Removing key properties
- Changing entity/relation names

✅ **Safe Changes:**

- Adding new entities
- Adding new properties (with null defaults)
- Adding new relations
- Adding properties to relations
- Adding key properties (if data supports it)

### Migration Naming

Use descriptive messages that explain **what** changed and **why**:

✅ **Good:**

```bash
grai migrate-generate -m "Add customer loyalty tier for rewards program"
grai migrate-generate -m "Change order_date to datetime for timezone support"
grai migrate-generate -m "Remove deprecated legacy_id field"
```

❌ **Bad:**

```bash
grai migrate-generate -m "Update"
grai migrate-generate -m "Fix stuff"
grai migrate-generate -m "Changes"
```

### Version Control

**Do:**

- ✅ Commit migration files to git
- ✅ Include migrations in pull requests
- ✅ Review migrations in code review
- ✅ Keep migrations in chronological order

**Don't:**

- ❌ Edit already-applied migrations
- ❌ Delete old migration files
- ❌ Rebase commits that contain migrations (unless not shared)
- ❌ Manually edit checksums

## Troubleshooting

### "No schema changes detected"

**Problem:** Running `migrate-generate` produces no migration.

**Causes:**

- No YAML files were modified
- Changes match the last migration exactly
- Migration directory doesn't exist

**Solution:**

```bash
# Verify you actually made changes
git diff entities/ relations/

# Check last migration state
cat migrations/*.yml | tail -n 50
```

### "Migration checksum mismatch"

**Problem:** Checksum verification fails.

**Causes:**

- Migration file was edited after being applied
- File corruption
- Different line endings (Windows vs Unix)

**Solution:**

1. Don't edit applied migrations - create a new one
2. If corrupted, restore from git: `git checkout migrations/`
3. For line ending issues, configure git properly

### "Constraint already exists"

**Problem:** Migration fails because constraint already exists.

**Causes:**

- Migration applied manually outside grai.build
- Migration was partially applied
- Neo4j state doesn't match migration history

**Solution:**

```cypher
// Check existing constraints
SHOW CONSTRAINTS

// Drop conflicting constraint
DROP CONSTRAINT customer_unique IF EXISTS

// Then rerun migration
```

### "Cannot rollback - data loss warning"

**Problem:** Rollback would delete data.

**Causes:**

- Rolling back property removal would lose data
- Rolling back entity removal would delete nodes

**Solution:**

1. Accept data loss if intentional
2. Export data first if needed
3. Consider creating a "forward fix" migration instead

## Advanced Usage

### Custom Migration Scripts

While migrations are auto-generated, you can manually edit them for complex scenarios:

**Example: Data transformation during type change**

```yaml
up:
  # Convert string age to integer
  - "MATCH (n:customer) WHERE n.age IS NOT NULL
    SET n.age = toInteger(n.age)"

down:
  # Convert back to string
  - "MATCH (n:customer) WHERE n.age IS NOT NULL
    SET n.age = toString(n.age)"
```

### Handling Large Datasets

For migrations affecting millions of nodes:

```yaml
up:
  # Use CALL {} IN TRANSACTIONS for large updates
  - "MATCH (n:customer)
    CALL {
    WITH n
    SET n.email = null
    } IN TRANSACTIONS OF 10000 ROWS"
```

### Idempotent Migrations

Always use Neo4j's conditional clauses:

```cypher
CREATE CONSTRAINT customer_unique IF NOT EXISTS ...
DROP CONSTRAINT customer_unique IF EXISTS
MERGE (n:customer) ... // Instead of CREATE
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Apply Migrations

on:
  push:
    branches: [main]
    paths:
      - "migrations/**"

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install grai.build
        run: pip install grai-build

      - name: Check Migration Status
        run: |
          grai migrate-status \
            --uri ${{ secrets.NEO4J_URI }} \
            --user ${{ secrets.NEO4J_USER }} \
            --password ${{ secrets.NEO4J_PASSWORD }}

      - name: Apply Migrations (Dry Run)
        run: |
          grai migrate-apply --dry-run \
            --uri ${{ secrets.NEO4J_URI }} \
            --user ${{ secrets.NEO4J_USER }} \
            --password ${{ secrets.NEO4J_PASSWORD }}

      - name: Apply Migrations
        run: |
          grai migrate-apply \
            --uri ${{ secrets.NEO4J_URI }} \
            --user ${{ secrets.NEO4J_USER }} \
            --password ${{ secrets.NEO4J_PASSWORD }}
```

## FAQs

**Q: Can I skip a migration?**
A: No, migrations must be applied in order. If you want to skip functionality, create an empty migration or rollback.

**Q: Can I have multiple pending migrations?**
A: Yes, `migrate-apply` will apply all pending migrations in version order.

**Q: What happens if a migration fails halfway?**
A: The migration status is set to "failed" and execution stops. Fix the issue and rerun `migrate-apply`.

**Q: Can I manually edit Cypher in migration files?**
A: Yes, but only before applying. Once applied, create a new migration for changes.

**Q: How do I handle conflicts when two developers create migrations?**
A: The later migration will build on the earlier one. Apply both in version order.

**Q: Can I migrate between different Neo4j instances?**
A: Yes, migration files are portable. Just point `--uri` to different databases.

**Q: Do migrations work with Neo4j Community Edition?**
A: Yes, fully compatible with both Community and Enterprise editions.

**Q: Can I export/import migration history?**
A: Migration history is stored in `__GraiMigration` nodes. Use Cypher to export: `MATCH (m:__GraiMigration) RETURN m`.

## See Also

- [Getting Started Guide](GETTING_STARTED.md)
- [CLI Usage Reference](CLI_USAGE.md)
- [Schema Validation](VALIDATOR.md)
- [Cypher Compiler](COMPILER.md)
- [Neo4j Setup Guide](NEO4J_SETUP.md)

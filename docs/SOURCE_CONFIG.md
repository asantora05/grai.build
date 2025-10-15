# Enhanced Source Configuration

## Overview

As of v0.3.0, grai.build supports both simple string sources (backward compatible) and detailed source configuration for entities and relations.

## Simple Source (Backward Compatible)

The traditional string format still works:

```yaml
entity: customer
source: analytics.customers
keys: [customer_id]
properties:
  - name: customer_id
    type: string
```

grai.build automatically infers the source type:

- `schema.table` → `type: table`
- `*.csv` → `type: csv`
- `*.json` → `type: json`
- `*.parquet` → `type: parquet`
- `http://...` → `type: api`

## Detailed Source Configuration

For more complex scenarios, use the expanded format:

```yaml
entity: customer
source:
  name: customers
  type: table
  connection: prod_analytics
  db_schema: public
  database: analytics_db
  format: delta
  metadata:
    owner: data-team
    refresh_schedule: "0 0 * * *"
keys: [customer_id]
properties:
  - name: customer_id
    type: string
  - name: name
    type: string
```

## Source Types

Supported `type` values:

- `database` - Database connection
- `table` - Database table or view
- `csv` - CSV file
- `json` - JSON file
- `parquet` - Parquet file
- `api` - REST API endpoint
- `stream` - Data stream (Kafka, Kinesis, etc.)
- `other` - Custom source type

## Field Descriptions

| Field        | Type   | Description                    | Example                            |
| ------------ | ------ | ------------------------------ | ---------------------------------- |
| `name`       | string | Source identifier (required)   | `customers`, `analytics.customers` |
| `type`       | enum   | Source type                    | `table`, `csv`, `api`              |
| `connection` | string | Connection or data source name | `prod_db`, `s3_bucket`             |
| `db_schema`  | string | Database schema name           | `public`, `analytics`              |
| `database`   | string | Database name                  | `analytics_db`, `warehouse`        |
| `format`     | string | Data format details            | `delta`, `iceberg`, `parquet`      |
| `metadata`   | dict   | Additional custom metadata     | `{owner: "team", version: "v2"}`   |

## Examples

### CSV File

```yaml
entity: product
source:
  name: products.csv
  type: csv
  format: utf-8
  metadata:
    location: s3://my-bucket/data/
keys: [product_id]
```

### API Endpoint

```yaml
entity: order
source:
  name: /api/v1/orders
  type: api
  connection: rest_api
  metadata:
    base_url: https://api.example.com
    auth: bearer_token
keys: [order_id]
```

### Database Table with Schema

```yaml
entity: transaction
source:
  name: transactions
  type: table
  database: financial_db
  db_schema: public
  connection: prod_postgres
  metadata:
    partitioned_by: date
keys: [transaction_id]
```

### Kafka Stream

```yaml
entity: event
source:
  name: user-events
  type: stream
  connection: kafka_prod
  metadata:
    topic: user.events.v1
    consumer_group: grai-consumer
keys: [event_id]
```

## Benefits

1. **Better Documentation** - Clear indication of source type and location
2. **Multiple Connections** - Support for different environments (dev, staging, prod)
3. **Metadata Tracking** - Store ownership, refresh schedules, and custom info
4. **Type Safety** - Explicit source types prevent confusion
5. **Tooling Integration** - Easier integration with data catalogs and lineage tools

## Migration Guide

Existing YAML files with simple string sources continue to work without changes. To migrate to the enhanced format:

**Before:**

```yaml
source: analytics.customers
```

**After:**

```yaml
source:
  name: customers
  type: table
  db_schema: analytics
  database: warehouse
```

## Usage in Code

The Python API automatically handles both formats:

```python
from grai.core.models import Entity

# Simple string (auto-converted)
entity1 = Entity(
    entity="customer",
    source="analytics.customers",
    keys=["customer_id"],
    properties=[]
)

# Get source name
print(entity1.get_source_name())  # "analytics.customers"

# Get full config
config = entity1.get_source_config()
print(config.type)  # SourceType.TABLE (inferred)

# Detailed config
entity2 = Entity(
    entity="customer",
    source={
        "name": "customers",
        "type": "table",
        "db_schema": "analytics"
    },
    keys=["customer_id"],
    properties=[]
)
```

## Graph IR Export

The enhanced source configuration is fully exported in the Graph IR (JSON):

```json
{
  "entities": [
    {
      "name": "customer",
      "source": {
        "name": "customers",
        "type": "table",
        "connection": "prod_db",
        "schema": "analytics",
        "database": "warehouse",
        "format": null,
        "metadata": {}
      },
      "keys": ["customer_id"]
    }
  ]
}
```

This makes it easy to integrate with data catalogs, lineage tools, and other metadata systems.

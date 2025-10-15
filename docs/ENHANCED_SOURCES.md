# Enhanced Source Configuration

grai.build now supports enhanced source configuration for entities and relations, providing more flexibility and metadata for different data source types.

## Overview

Sources can be defined in two ways:

1. **Simple string format** (backward compatible):

```yaml
source: analytics.customers
```

2. **Enhanced configuration format** (new):

```yaml
source:
  name: analytics.customers
  type: table
  database: postgres_prod
  db_schema: analytics
  connection: primary_db
  format: parquet
  metadata:
    refresh_cadence: hourly
    owner: data-team
```

## Supported Source Types

The `type` field can be one of:

- `database` - General database source
- `table` - Database table (most common)
- `csv` - CSV file
- `json` - JSON file
- `parquet` - Parquet file
- `api` - REST API endpoint
- `stream` - Streaming source (Kafka, Kinesis, etc.)
- `other` - Custom/other source types

## Configuration Fields

### Required Fields

- **`name`** (string): The source identifier (e.g., table name, file path, API endpoint)

### Optional Fields

- **`type`** (SourceType): Type of data source (auto-inferred if not provided)
- **`connection`** (string): Connection identifier or connection string
- **`db_schema`** (string): Database schema name
- **`database`** (string): Database name
- **`format`** (string): Data format details (e.g., "utf-8", "gzip")
- **`metadata`** (dict): Additional custom metadata

## Examples

### Database Table

```yaml
entity: customer
source:
  name: analytics.customers
  type: table
  database: postgres_prod
  db_schema: analytics
  connection: primary_db
keys:
  - customer_id
properties:
  - name: customer_id
    type: string
  - name: name
    type: string
```

### CSV File

```yaml
entity: order
source:
  name: data/orders.csv
  type: csv
  format: utf-8
  metadata:
    delimiter: ","
    has_header: true
    encoding: utf-8
keys:
  - order_id
properties:
  - name: order_id
    type: string
  - name: total
    type: float
```

### API Endpoint

```yaml
entity: external_product
source:
  name: https://api.example.com/products
  type: api
  format: json
  metadata:
    auth_type: bearer
    rate_limit: 1000/hour
    version: v2
keys:
  - product_id
properties:
  - name: product_id
    type: string
  - name: name
    type: string
```

### Parquet Files

```yaml
entity: event
source:
  name: s3://bucket/path/events.parquet
  type: parquet
  connection: s3_warehouse
  metadata:
    compression: snappy
    partition_cols: [date, region]
keys:
  - event_id
properties:
  - name: event_id
    type: string
  - name: event_type
    type: string
```

### Streaming Source

```yaml
entity: clickstream
source:
  name: kafka://events-topic
  type: stream
  connection: kafka_cluster
  metadata:
    consumer_group: grai-consumers
    offset: latest
keys:
  - session_id
properties:
  - name: session_id
    type: string
  - name: timestamp
    type: datetime
```

## Type Auto-Inference

When using the simple string format, grai.build attempts to infer the source type:

- Contains `.` → `table` (e.g., "schema.table")
- Ends with `.csv` → `csv`
- Ends with `.json` → `json`
- Ends with `.parquet` → `parquet`
- Starts with `http://` or `https://` → `api`
- Otherwise → `null` (no inference)

Example:

```yaml
source: analytics.customers  # Inferred as type: table
source: data.csv            # Inferred as type: csv
source: https://api.com     # Inferred as type: api
```

## Backward Compatibility

All existing entity and relation definitions continue to work without changes. The simple string format is fully supported:

```yaml
entity: customer
source: analytics.customers # This still works!
keys:
  - customer_id
```

## Benefits

1. **Better Documentation**: Source types and metadata are explicit
2. **Lineage Tracking**: Enhanced lineage graphs with source type information
3. **Multi-Source Support**: Easily define entities from different source types
4. **Metadata Rich**: Store connection info, refresh cadence, ownership, etc.
5. **Tooling Integration**: Better integration with data catalogs and orchestrators

## Usage in Compiled Output

The enhanced source information is preserved in:

- **Graph IR exports**: Full source config in JSON
- **Lineage visualizations**: Source types displayed in graphs
- **Documentation**: Source details shown in HTML docs

## Migration Guide

To migrate existing definitions:

1. **No changes required** - simple strings still work
2. **Optional enhancement** - gradually add enhanced configs where needed
3. **Mixed usage** - use both formats in the same project

Example migration:

```yaml
# Before (still works)
source: analytics.customers

# After (enhanced)
source:
  name: analytics.customers
  type: table
  database: postgres_prod
  db_schema: analytics
```

## Best Practices

1. **Use simple format for straightforward cases** - less verbose
2. **Use enhanced format when**:
   - Multiple databases/connections
   - Need to document source metadata
   - Different source types (CSV, API, etc.)
   - Building data catalogs/lineage
3. **Document connections** - use descriptive connection names
4. **Add metadata** - include ownership, refresh cadence, SLAs

## Future Enhancements

Planned improvements:

- Connection pooling and credentials management
- Automatic schema inference from sources
- Source validation and testing
- Integration with dbt sources
- Data quality metrics per source

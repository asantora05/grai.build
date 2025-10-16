# dbt Integration Roadmap

## Current Status

### ✅ Completed (Steps 1-2)

1. **dbt Manifest Parser** ✅

   - Import dbt models as grai.build entities
   - 18 tests, 94% coverage
   - CLI: `grai import dbt`

2. **BigQuery Data Loader** ✅

   - Extract from BigQuery, load to Neo4j
   - Batch processing, dry-run mode
   - CLI: `grai load <entity>`

3. **Connection Profiles** ✅
   - dbt-style profiles.yml
   - 21 tests, 95% coverage
   - Environment variable support

### 🔄 In Progress (Step 3)

**Testing & Documentation**

- BigQuery loader tests needed
- dbt integration guide needed
- BigQuery setup guide needed

## Priority Roadmap

### 🎯 Immediate (Next Session)

#### 1. Complete Testing ⚡

**Goal:** Get BigQuery loader to same test quality as dbt parser

Tasks:

- [ ] Create `tests/test_bigquery_loader.py`
  - Mock BigQuery client (avoid real API calls)
  - Test `BigQueryExtractor` methods
  - Test `load_entity_from_bigquery()`
  - Test `load_relation_from_bigquery()`
  - Test Cypher generation functions
  - Test error handling
  - Target: 18-20 tests, 90%+ coverage

#### 2. Documentation 📚

**Goal:** Help users understand the complete workflow

Tasks:

- [ ] Create `docs/dbt-integration.md`
  - Overview of dbt → grai.build workflow
  - Step-by-step guide
  - Example project structure
  - Common patterns
  - Troubleshooting
- [ ] Create `docs/bigquery-setup.md`

  - BigQuery authentication setup
  - Service account creation
  - OAuth configuration
  - Permissions required
  - Cost optimization tips

- [ ] Update `docs/data-loading.md`

  - Add BigQuery examples
  - Profile-based loading examples
  - Batch processing tips

- [ ] Create end-to-end tutorial
  - `docs/tutorials/dbt-to-neo4j.md`
  - Real-world ecommerce example
  - From dbt models to knowledge graph

#### 3. Update CHANGELOG 📝

Add to v0.4.0 (upcoming):

```markdown
## [0.4.0] - 2025-10-XX

### Added

- **dbt Integration**: Import dbt models as entities with `grai import dbt`
- **BigQuery Loader**: Load data from BigQuery to Neo4j
- **Connection Profiles**: dbt-style profiles.yml for managing connections
- Environment variable substitution in profiles
- Support for multiple environments (dev, staging, prod)
- Batch processing for large datasets
- Dry-run mode for data loading

### Changed

- `grai load` command now uses profiles.yml instead of individual flags
- `grai init` creates default profiles.yml

### Deprecated

- Direct connection flags in grai.yml (use profiles.yml instead)
```

### 🚀 Short Term (Next 1-2 Weeks)

#### 4. Enhanced dbt Integration 🔧

**Auto-detect Relations from dbt**

- Parse dbt `ref()` and `source()` calls
- Generate relation YAML files automatically
- Infer foreign key relationships from joins

```python
# grai/core/dbt/relation_inferrer.py
def infer_relations_from_dbt(manifest: dict) -> List[Relation]:
    """
    Analyze dbt models to infer entity relationships.

    - Parse SQL for JOIN statements
    - Extract ref() dependencies
    - Map to grai.build relations
    """
```

**dbt Tests → grai.build Constraints**

- Map dbt tests to Neo4j constraints
- Generate constraint Cypher
- Validate data quality in graph

```yaml
# Generated from dbt unique test
entity: customer
keys:
  - customer_id
constraints:
  - type: unique
    properties: [email]
  - type: not_null
    properties: [name]
```

**dbt Docs Integration**

- Import dbt documentation
- Preserve model descriptions
- Link to dbt lineage

#### 5. Improved CLI Experience 🎨

**`grai load --all`**

```bash
# Load all entities and relations in order
grai load --all

# With dependency resolution
grai load --all --respect-dependencies
```

**Progress Indicators**

```bash
grai load customer
Loading customer from BigQuery...
├─ Extracted: 10,000 rows [████████████████████] 100%
├─ Loading batch 1/10 [██░░░░░░░░░░░░░░░░░░] 10%
└─ ETA: 45 seconds
```

**`grai profile` Command**

```bash
# List available profiles
grai profile list

# Show current profile
grai profile show

# Validate profile
grai profile validate --profile default --target prod

# Set default profile
grai profile set-default myproject
```

#### 6. Data Quality & Validation ✅

**Row Count Validation**

```bash
grai load customer --validate-counts
# Expected: 1000 rows in BigQuery
# Loaded: 1000 nodes in Neo4j
# Status: ✅ Match
```

**Schema Validation**

- Verify property types match
- Check for missing required fields
- Report data quality issues

**Load Summary**

```bash
grai load customer

✓ Load Complete

Summary:
  Entity: customer
  Source: bigquery.analytics.customers
  Extracted: 10,000 rows
  Loaded: 10,000 nodes
  Duration: 32.5s
  Throughput: 307 rows/sec

Validation:
  ✓ Row counts match
  ✓ All required properties present
  ⚠ 12 rows with NULL emails (set to default)
```

### 🔮 Medium Term (1-2 Months)

#### 7. Incremental Loading 🔄

**Track Loaded Records**

```python
# grai/core/cache/load_cache.py
class LoadCache:
    """Track which records have been loaded."""

    def mark_loaded(entity: str, record_id: str, timestamp: datetime)
    def get_last_load(entity: str) -> datetime
    def get_unloaded_records(entity: str) -> List[str]
```

**Incremental Sync**

```bash
# Only load new/updated records
grai load customer --incremental

# Using timestamp column
grai load customer --incremental --updated-at-column modified_at
```

#### 8. Additional Warehouse Support 🗄️

**Snowflake Loader**

```python
# grai/core/loader/snowflake_loader.py
class SnowflakeExtractor:
    """Extract data from Snowflake."""
```

**Redshift Loader**

```python
# grai/core/loader/redshift_loader.py
class RedshiftExtractor:
    """Extract data from Amazon Redshift."""
```

**Databricks Loader**

```python
# grai/core/loader/databricks_loader.py
class DatabricksExtractor:
    """Extract data from Databricks."""
```

#### 9. Performance Optimizations ⚡

**Parallel Loading**

```bash
# Load multiple entities in parallel
grai load customer product order --parallel --workers 4
```

**Compressed Transfer**

```python
# Use Arrow format for faster data transfer
from pyarrow import Table
```

**Connection Pooling**

```python
# Reuse Neo4j connections across batches
```

#### 10. Advanced dbt Features 🚀

**dbt Snapshots → Temporal Graphs**

- Load dbt snapshot tables
- Create temporal nodes in Neo4j
- Query historical states

**dbt Seeds → Reference Data**

```bash
grai import dbt --include-seeds
# Load seed CSVs as reference entities
```

**dbt Exposures → Graph Queries**

- Document downstream graph usage
- Generate sample Cypher queries

### 🌟 Long Term (3-6 Months)

#### 11. Web UI / Dashboard 🖥️

**Load Monitoring Dashboard**

- Real-time load progress
- Historical load metrics
- Data quality trends
- Error logs

**Profile Management UI**

- Visual profile editor
- Connection testing
- Environment switching

#### 12. Advanced Graph Features 🕸️

**Graph Algorithms**

```bash
# Run algorithms on loaded data
grai analyze centrality --entity customer
grai analyze communities --relation PURCHASED
```

**Lineage Tracking**

```bash
# Track data lineage through the pipeline
grai lineage customer
# dbt:customers → BigQuery:analytics.customers → Neo4j:customer
```

#### 13. CI/CD Integration 🔧

**GitHub Actions Workflow**

```yaml
# .github/workflows/sync-dbt-to-neo4j.yml
name: Sync dbt to Neo4j

on:
  workflow_dispatch:
  schedule:
    - cron: "0 2 * * *" # Daily at 2 AM

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Import dbt models
        run: grai import dbt --manifest ${{ env.DBT_MANIFEST }}
      - name: Load to Neo4j
        run: grai load --all --target prod
```

**Airflow DAG**

```python
# dags/grai_sync.py
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG('grai_neo4j_sync') as dag:
    import_dbt = BashOperator(
        task_id='import_dbt_models',
        bash_command='grai import dbt --manifest /path/to/manifest.json'
    )

    load_entities = BashOperator(
        task_id='load_entities',
        bash_command='grai load --all'
    )

    import_dbt >> load_entities
```

#### 14. Multi-Database Support 🗃️

**Support Multiple Graph Databases**

- Neo4j (current)
- TigerGraph
- Neptune (AWS)
- Azure Cosmos DB
- JanusGraph

**Unified Interface**

```yaml
# profiles.yml
default:
  outputs:
    dev:
      graph:
        type: tigergraph # or neptune, cosmosdb
```

## Implementation Priority

### Must Have (v0.4.0)

1. ✅ dbt manifest parser
2. ✅ BigQuery loader
3. ✅ Connection profiles
4. 🔄 BigQuery loader tests
5. 🔄 Documentation (dbt guide, BigQuery setup)
6. 🔄 CHANGELOG update

### Should Have (v0.5.0)

- Auto-detect relations from dbt
- Progress indicators
- `grai load --all`
- `grai profile` command
- Data validation
- Snowflake loader

### Nice to Have (v0.6.0)

- Incremental loading
- Parallel loading
- dbt snapshots support
- Additional warehouses (Redshift, Databricks)

### Future (v1.0+)

- Web UI
- Graph algorithms
- Multi-database support
- Advanced CI/CD templates

## Success Metrics

### Code Quality

- ✅ 90%+ test coverage
- ✅ All tests passing
- ✅ Pre-commit hooks enforced
- ✅ Type hints everywhere

### User Experience

- Complete documentation
- Working examples
- Clear error messages
- Fast load times (<100ms per batch)

### Community

- GitHub stars/forks
- PyPI downloads
- Community contributions
- Issue resolution time

## Getting Started

**Next Coding Session:**

```bash
# 1. Create BigQuery loader tests
touch tests/test_bigquery_loader.py

# 2. Create documentation
touch docs/dbt-integration.md
touch docs/bigquery-setup.md
touch docs/tutorials/dbt-to-neo4j.md

# 3. Update CHANGELOG
vim CHANGELOG.md

# 4. Run tests
pytest tests/test_bigquery_loader.py -v

# 5. Build docs
mkdocs serve  # Preview documentation

# 6. Release
git tag v0.4.0
git push --tags
```

## Questions to Consider

1. **Should we support dbt Cloud API?**

   - Fetch manifest directly from dbt Cloud
   - No need for local manifest.json

2. **How to handle large datasets?**

   - Streaming vs batch loading trade-offs
   - Memory management strategies
   - Resume failed loads

3. **What's the upgrade path?**

   - Breaking changes in profiles.yml format?
   - Migration script for existing users?

4. **Should profiles.yml be per-project?**
   - Currently: `~/.grai/profiles.yml` (global)
   - Alternative: `.grai/profiles.yml` (per-project)
   - Or support both?

## Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [dbt Manifest Schema](https://docs.getdbt.com/reference/artifacts/manifest-json)

## Summary

The dbt integration is **80% complete**:

- ✅ Core functionality working
- ✅ Well tested (39 tests)
- ✅ Great documentation
- 🔄 Need BigQuery loader tests
- 🔄 Need end-to-end guides

**Recommended Next Steps:**

1. Write BigQuery loader tests (1-2 hours)
2. Create dbt integration guide (1 hour)
3. Create BigQuery setup guide (30 min)
4. Update CHANGELOG (15 min)
5. Release v0.4.0 🚀

After that, focus on:

- Auto-detecting relations from dbt
- Progress indicators
- `grai load --all` command

This will make grai.build the **best tool for turning dbt models into knowledge graphs**! 🎉

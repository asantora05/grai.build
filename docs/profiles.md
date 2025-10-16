# Connection Profiles

Similar to dbt's `profiles.yml`, grai.build uses a profiles system to manage connections to data warehouses and graph databases. This makes it easy to switch between development, staging, and production environments.

## Profile File Location

By default, profiles are stored at `~/.grai/profiles.yml`. You can override this location by setting the `GRAI_PROFILES_DIR` environment variable:

```bash
export GRAI_PROFILES_DIR=/path/to/custom/location
```

## Creating Your First Profile

When you run `grai init`, a default `profiles.yml` file is created at `~/.grai/profiles.yml`. You can also create one manually:

```yaml
# ~/.grai/profiles.yml
default:
  target: dev
  outputs:
    dev:
      # Data warehouse configuration
      warehouse:
        type: bigquery
        method: oauth
        project: my-gcp-project
        dataset: analytics
        location: US
        timeout_seconds: 300

      # Graph database configuration
      graph:
        type: neo4j
        uri: bolt://localhost:7687
        user: neo4j
        password: mypassword
        database: neo4j
        encrypted: true

    prod:
      warehouse:
        type: bigquery
        method: service-account
        project: my-prod-project
        dataset: analytics_prod
        location: US
        keyfile: /path/to/service-account.json

      graph:
        type: neo4j
        uri: bolt://prod-neo4j.example.com:7687
        user: neo4j
        password: prodpassword
        database: neo4j
        encrypted: true
```

## Profile Structure

Each profile has:

- **Profile name** (e.g., `default`, `my_project`): Top-level key
- **target**: The default environment to use (e.g., `dev`, `prod`)
- **outputs**: Named configurations for different environments
  - **warehouse**: Data warehouse connection (BigQuery, Snowflake, etc.)
  - **graph**: Graph database connection (Neo4j)

## Using Environment Variables

You can reference environment variables in your profiles using Jinja-style syntax:

```yaml
default:
  target: dev
  outputs:
    dev:
      warehouse:
        type: bigquery
        method: oauth
        project: "{{ env_var('GCP_PROJECT') }}"
        dataset: analytics

      graph:
        type: neo4j
        uri: bolt://localhost:7687
        user: neo4j
        password: "{{ env_var('NEO4J_PASSWORD') }}"
```

Then set the environment variables:

```bash
export GCP_PROJECT=my-dev-project
export NEO4J_PASSWORD=mypassword
```

## BigQuery Configuration

### OAuth Authentication (Development)

```yaml
warehouse:
  type: bigquery
  method: oauth
  project: my-project
  dataset: analytics
  location: US
  timeout_seconds: 300
```

This uses your local gcloud credentials:

```bash
gcloud auth application-default login
```

### Service Account (Production)

```yaml
warehouse:
  type: bigquery
  method: service-account
  project: my-project
  dataset: analytics
  location: US
  keyfile: /path/to/service-account.json
  timeout_seconds: 600
```

### Service Account JSON (Alternative)

```yaml
warehouse:
  type: bigquery
  method: service-account-json
  project: my-project
  dataset: analytics
  location: US
  keyfile_json:
    type: service_account
    project_id: my-project
    private_key_id: "..."
    private_key: "..."
    client_email: "..."
    # ... rest of service account JSON
```

## Snowflake Configuration

```yaml
warehouse:
  type: snowflake
  account: abc12345.us-east-1
  user: "{{ env_var('SNOWFLAKE_USER') }}"
  password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
  role: ANALYST
  database: ANALYTICS
  warehouse: COMPUTE_WH
  schema: PUBLIC
  authenticator: externalbrowser # Optional: for SSO
```

## Neo4j Configuration

```yaml
graph:
  type: neo4j
  uri: bolt://localhost:7687
  user: neo4j
  password: "{{ env_var('NEO4J_PASSWORD') }}"
  database: neo4j # Optional: defaults to 'neo4j'
  encrypted: true # Optional: defaults to true
  trust: TRUST_SYSTEM_CA_SIGNED_CERTIFICATES # Optional
```

### Neo4j Aura (Cloud)

```yaml
graph:
  type: neo4j
  uri: neo4j+s://xxxxx.databases.neo4j.io
  user: neo4j
  password: "{{ env_var('NEO4J_AURA_PASSWORD') }}"
  database: neo4j
  encrypted: true
```

## Using Profiles in Your Project

### In grai.yml

Reference a profile in your project manifest:

```yaml
name: my-project
version: 1.0.0

# Use this profile by default
profile: default
```

### Command Line

Override the profile or target at runtime:

```bash
# Use default profile and target
grai load customer

# Use specific profile
grai load customer --profile my_project

# Use specific target within a profile
grai load customer --target prod

# Use both
grai load customer --profile my_project --target staging
```

### Environment Variables

Set environment variables to override defaults:

```bash
# Override profile
export GRAI_PROFILE=my_project

# Override target
export GRAI_TARGET=prod

# Now these use the prod target
grai load customer
grai load PURCHASED
```

## Multiple Projects

You can define multiple profiles in one file:

```yaml
# Project A
ecommerce:
  target: dev
  outputs:
    dev:
      warehouse:
        type: bigquery
        project: ecommerce-dev
        dataset: analytics
      graph:
        type: neo4j
        uri: bolt://localhost:7687
        user: neo4j
        password: devpass

# Project B
social_network:
  target: dev
  outputs:
    dev:
      warehouse:
        type: snowflake
        account: xyz789.us-west-2
        user: analyst
        database: SOCIAL
      graph:
        type: neo4j
        uri: bolt://localhost:7688
        user: neo4j
        password: devpass2
```

Then specify which profile to use:

```bash
cd ecommerce-project
grai load customer --profile ecommerce

cd ../social-project
grai load user --profile social_network
```

## Best Practices

### 1. Use Environment Variables for Secrets

Never commit passwords or API keys to version control:

```yaml
# ✅ Good
password: "{{ env_var('NEO4J_PASSWORD') }}"

# ❌ Bad
password: supersecretpassword123
```

### 2. Separate Profiles by Environment

Use different targets for dev, staging, and prod:

```yaml
myproject:
  target: dev
  outputs:
    dev:
      # Development settings
    staging:
      # Staging settings
    prod:
      # Production settings
```

### 3. Document Your Profiles

Add comments to explain configuration choices:

```yaml
myproject:
  target: dev
  outputs:
    dev:
      warehouse:
        type: bigquery
        method: oauth # Uses local gcloud credentials
        project: myproject-dev
        dataset: analytics
        # Timeout increased for long-running transformations
        timeout_seconds: 600
```

### 4. Share Profile Template

Create a `profiles.yml.example` in your project repository:

```yaml
# profiles.yml.example
# Copy to ~/.grai/profiles.yml and fill in your credentials

myproject:
  target: dev
  outputs:
    dev:
      warehouse:
        type: bigquery
        method: oauth
        project: "{{ env_var('GCP_PROJECT') }}" # Set this
        dataset: analytics
      graph:
        type: neo4j
        uri: bolt://localhost:7687
        user: neo4j
        password: "{{ env_var('NEO4J_PASSWORD') }}" # Set this
```

## Troubleshooting

### Profile Not Found

```
Error: Profile file not found at ~/.grai/profiles.yml
```

**Solution**: Run `grai init` or create the file manually.

### Profile Name Not Found

```
Error: Profile 'myproject' not found. Available profiles: default
```

**Solution**: Check the profile name in your `profiles.yml` matches what you're using.

### Environment Variable Not Set

```
Error: Environment variable 'NEO4J_PASSWORD' is not set
```

**Solution**: Set the required environment variable:

```bash
export NEO4J_PASSWORD=yourpassword
```

### Target Not Found

```
Error: Target 'prod' not found in profile 'default'
```

**Solution**: Add the target to your profile or check for typos.

## Example Workflows

### Development Workflow

```bash
# Use local development environment
export GRAI_TARGET=dev
export NEO4J_PASSWORD=devpass

grai load customer
grai load product
grai load PURCHASED
```

### Production Deployment

```bash
# Use production environment
export GRAI_TARGET=prod
export NEO4J_PASSWORD=$(vault read -field=password secret/neo4j/prod)
export GCP_KEYFILE_PATH=/etc/gcp/service-account.json

grai load customer --limit 10  # Test with small batch
grai load customer            # Full load
```

### CI/CD Pipeline

```yaml
# .github/workflows/load-data.yml
name: Load Data to Neo4j

on:
  schedule:
    - cron: "0 2 * * *" # Daily at 2 AM

jobs:
  load:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install grai.build
        run: pip install grai-build

      - name: Load data
        env:
          GRAI_TARGET: prod
          NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
          GCP_PROJECT: ${{ secrets.GCP_PROJECT }}
        run: |
          grai load customer
          grai load product
          grai load PURCHASED
```

## See Also

- [Data Loading](data-loading.md) - Loading data from warehouses
- [dbt Integration](dbt-integration.md) - Importing dbt models
- [Neo4j Setup](neo4j-setup.md) - Setting up Neo4j

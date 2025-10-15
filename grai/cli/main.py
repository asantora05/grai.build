"""
Main CLI application for grai.build.

This module provides the Typer-based command-line interface for grai.build,
offering commands for project initialization, validation, compilation, and execution.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from grai import __version__
from grai.core.cache import (
    clear_cache,
    load_cache,
    should_rebuild,
    update_cache,
)
from grai.core.compiler import compile_and_write, compile_schema_only
from grai.core.lineage import (
    build_lineage_graph,
    calculate_impact_analysis,
    get_entity_lineage,
    get_lineage_statistics,
    get_relation_lineage,
    visualize_lineage_graphviz,
    visualize_lineage_mermaid,
)
from grai.core.models import Project
from grai.core.parser import load_project
from grai.core.validator import validate_project
from grai.core.visualizer import (
    generate_cytoscape_visualization,
    generate_d3_visualization,
)

# Initialize Typer app
app = typer.Typer(
    name="grai",
    help="Declarative knowledge graph modeling tool inspired by dbt.",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


def version_callback(value: bool):
    """Show version information."""
    if value:
        console.print(f"grai.build version {__version__}", style="bold green")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    grai.build - Declarative knowledge graph modeling.

    Define entities and relations in YAML, validate schemas,
    compile to Cypher, and load into Neo4j.
    """
    pass


@app.command()
def init(
    path: Path = typer.Argument(
        Path("."),
        help="Directory to initialize project in (default: current directory).",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Project name (default: directory name).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files.",
    ),
):
    """
    Initialize a new grai.build project in the current directory.

    Creates a starter project with example entities and relations.
    Initializes in the current directory by default (like git init, npm init).

    Examples:
        grai init                    # Initialize in current directory
        grai init --name my-graph    # Initialize with custom project name
        grai init /path/to/project   # Initialize in specific directory
    """
    project_dir = path.resolve()

    # Infer project name from directory if not provided
    if name is None:
        name = project_dir.name
        if name == ".":
            name = "my-knowledge-graph"

    console.print(f"\n[bold cyan]🚀 Initializing grai.build project: {name}[/bold cyan]\n")

    # Check if grai.yml already exists (not the directory itself)
    grai_yml_path = project_dir / "grai.yml"
    if grai_yml_path.exists() and not force:
        console.print("[red]✗ Project already initialized (grai.yml exists)[/red]")
        console.print("[yellow]Use --force to overwrite existing files[/yellow]")
        raise typer.Exit(code=1)

    # Create directory structure
    try:
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "entities").mkdir(exist_ok=True)
        (project_dir / "relations").mkdir(exist_ok=True)
        (project_dir / "target" / "neo4j").mkdir(parents=True, exist_ok=True)

        # Create grai.yml
        grai_yml = f"""name: {name}
version: 1.0.0
description: A knowledge graph project built with grai.build

# Optional: Specify custom directories
# entity_dir: entities
# relation_dir: relations
# target_dir: target

# Optional: Neo4j connection settings
# neo4j:
#   uri: bolt://localhost:7687
#   user: neo4j
#   password: password
"""
        (project_dir / "grai.yml").write_text(grai_yml)

        # Create example entity (using enhanced source configuration)
        customer_yml = """entity: customer
# Enhanced source configuration with metadata
source:
  name: customers
  type: table
  db_schema: analytics
  database: warehouse
  connection: prod_db
  metadata:
    owner: data-team
    refresh_schedule: daily
keys:
  - customer_id
properties:
  - name: customer_id
    type: string
    required: true
    description: Unique customer identifier
  - name: name
    type: string
    description: Customer name
  - name: email
    type: string
    description: Customer email address
  - name: created_at
    type: datetime
    description: Account creation timestamp
description: Customer entity from analytics warehouse
"""
        (project_dir / "entities" / "customer.yml").write_text(customer_yml)

        # Create example entity (simple source format for comparison)
        product_yml = """entity: product
# Simple source format (backward compatible - type is auto-inferred as 'table')
source: analytics.products
keys:
  - product_id
properties:
  - name: product_id
    type: string
    required: true
    description: Unique product identifier
  - name: name
    type: string
    description: Product name
  - name: category
    type: string
    description: Product category
  - name: price
    type: float
    description: Product price
description: Product entity using simple source format
"""
        (project_dir / "entities" / "product.yml").write_text(product_yml)

        # Create example relation (enhanced source with CSV type)
        purchased_yml = """relation: PURCHASED
from: customer
to: product
# Enhanced source showing CSV file configuration
source:
  name: orders.csv
  type: csv
  format: utf-8
  metadata:
    location: ./data/
    delimiter: ","
mappings:
  from_key: customer_id
  to_key: product_id
properties:
  - name: order_id
    type: string
    required: true
    description: Unique order identifier
  - name: order_date
    type: date
    description: Date of purchase
  - name: quantity
    type: integer
    description: Quantity purchased
  - name: total_amount
    type: float
    description: Total order amount
description: Purchase relationship with CSV source configuration
"""
        (project_dir / "relations" / "purchased.yml").write_text(purchased_yml)

        # Create data directory for CSV files
        (project_dir / "data").mkdir(exist_ok=True)

        # Create sample CSV for customers
        customer_csv = """customer_id,name,email,created_at
C001,Alice Johnson,alice@example.com,2024-01-15T10:30:00Z
C002,Bob Smith,bob@example.com,2024-01-20T14:15:00Z
C003,Carol Williams,carol@example.com,2024-02-05T09:45:00Z
C004,David Brown,david@example.com,2024-02-10T16:20:00Z
C005,Emma Davis,emma@example.com,2024-02-15T11:00:00Z
"""
        (project_dir / "data" / "customers.csv").write_text(customer_csv)

        # Create sample CSV for products
        product_csv = """product_id,name,category,price
P001,Laptop Pro 15,Electronics,1299.99
P002,Wireless Mouse,Accessories,29.99
P003,USB-C Hub,Accessories,49.99
P004,Monitor 27",Electronics,399.99
P005,Keyboard Mechanical,Accessories,129.99
P006,Webcam HD,Electronics,79.99
"""
        (project_dir / "data" / "products.csv").write_text(product_csv)

        # Create sample CSV for purchases
        purchased_csv = """customer_id,product_id,order_id,order_date,quantity,total_amount
C001,P001,O001,2024-03-01,1,1299.99
C001,P002,O002,2024-03-01,2,59.98
C002,P003,O003,2024-03-05,1,49.99
C002,P005,O004,2024-03-05,1,129.99
C003,P001,O005,2024-03-10,1,1299.99
C003,P004,O006,2024-03-10,1,399.99
C004,P002,O007,2024-03-15,1,29.99
C004,P006,O008,2024-03-15,1,79.99
C005,P005,O009,2024-03-20,1,129.99
C005,P003,O010,2024-03-20,2,99.98
"""
        (project_dir / "data" / "purchased.csv").write_text(purchased_csv)

        # Create Cypher script for loading data
        # Get absolute path to data directory for LOAD CSV
        # Convert to file:// URL properly (file:// + absolute path)
        data_dir_abs = (project_dir / "data").resolve()
        file_url_prefix = f"file://{data_dir_abs}"

        load_cypher = f"""// ============================================
// Load Sample Data from CSV Files
// ============================================
//
// This script loads sample data into Neo4j using LOAD CSV.
// Make sure you've already created the schema with: grai run
//
// To use this script:
// 1. Open Neo4j Browser (http://localhost:7474)
// 2. Copy and paste this entire script
// 3. Run it
//
// Or use cypher-shell:
//   cat load_data.cypher | cypher-shell -u neo4j -p yourpassword
//
// ============================================

// Load Customers
LOAD CSV WITH HEADERS FROM '{file_url_prefix}/customers.csv' AS row
MERGE (c:customer {{customer_id: row.customer_id}})
SET c.name = row.name,
    c.email = row.email,
    c.created_at = datetime(row.created_at);

// Load Products
LOAD CSV WITH HEADERS FROM '{file_url_prefix}/products.csv' AS row
MERGE (p:product {{product_id: row.product_id}})
SET p.name = row.name,
    p.category = row.category,
    p.price = toFloat(row.price);

// Load Purchases (relationships)
LOAD CSV WITH HEADERS FROM '{file_url_prefix}/purchased.csv' AS row
MATCH (c:customer {{customer_id: row.customer_id}})
MATCH (p:product {{product_id: row.product_id}})
MERGE (c)-[r:PURCHASED]->(p)
SET r.order_id = row.order_id,
    r.order_date = date(row.order_date),
    r.quantity = toInteger(row.quantity),
    r.total_amount = toFloat(row.total_amount);

// ============================================
// Verify the data was loaded
// ============================================

// Count nodes
MATCH (n)
RETURN labels(n) AS type, count(n) AS count
ORDER BY type;

// Count relationships
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(r) AS count;

// Show sample data
MATCH (c:customer)-[p:PURCHASED]->(prod:product)
RETURN c.name, prod.name, p.order_date, p.total_amount
ORDER BY p.order_date
LIMIT 5;
"""
        (project_dir / "load_data.cypher").write_text(load_cypher)

        # Create README
        readme = f"""# {name}

A knowledge graph project built with [grai.build](https://github.com/grai-build/grai.build).

## Project Structure

```
{name}/
├── grai.yml           # Project configuration
├── entities/          # Entity definitions
│   ├── customer.yml
│   └── product.yml
├── relations/         # Relation definitions
│   └── purchased.yml
├── data/              # Sample CSV data
│   ├── customers.csv
│   ├── products.csv
│   └── purchased.csv
├── load_data.py       # Script to load CSV data
└── target/            # Compiled output
    └── neo4j/
        └── compiled.cypher
```

## Getting Started

### 1. Validate your project

```bash
grai validate
```

### 2. Create the schema in Neo4j

```bash
grai run --uri bolt://localhost:7687 --user neo4j --password password
```

This creates constraints and indexes but no data yet.

### 3. Load sample data from CSV files

```bash
# Edit connection details in load_data.py first!
python load_data.py
```

This loads:
- 5 sample customers
- 6 sample products
- 10 sample purchase orders

### 4. Explore your graph

Open Neo4j Browser at http://localhost:7474 and run:

```cypher
// View the entire graph
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50

// Count nodes
MATCH (n)
RETURN labels(n) AS type, count(n) AS count

// Find high-value customers
MATCH (c:customer)-[p:PURCHASED]->()
WITH c, sum(p.total_amount) AS total_spent
WHERE total_spent > 1000
RETURN c.name, c.email, total_spent
ORDER BY total_spent DESC
```

## Next Steps

1. Start your Neo4j database
2. Run `grai run` to create the schema (constraints & indexes)
3. Load sample data:
   - Open Neo4j Browser (http://localhost:7474)
   - Copy/paste the contents of `load_data.cypher` and run it
4. Edit entity definitions in `entities/` as needed
5. Edit relation definitions in `relations/` as needed
6. Modify CSV files in `data/` with your own data
7. Run `grai validate` to check for errors
8. Run `grai build` to see the compiled Cypher

## Source Configuration Formats

This project demonstrates both source configuration formats:

### Enhanced Format (customer.yml)
```yaml
source:
  name: customers
  type: table
  db_schema: analytics
  database: warehouse
  connection: prod_db
  metadata:
    owner: data-team
    refresh_schedule: daily
```

Benefits:
- Explicit source type (table, csv, api, stream, etc.)
- Additional metadata for documentation
- Support for multiple connections
- Better integration with data catalogs

### Simple Format (product.yml)
```yaml
source: analytics.products
```

Benefits:
- Backward compatible with existing projects
- Concise for simple use cases
- Auto-infers type from format (e.g., `schema.table` → type: table)

Both formats work identically - use whichever fits your needs!

See the project's `docs/` folder for more examples.

## Learn More

- [grai.build Documentation](https://github.com/grai-build/grai.build)
- [Neo4j Documentation](https://neo4j.com/docs/)
"""
        (project_dir / "README.md").write_text(readme)

        console.print("[green]✓[/green] Created project structure")
        console.print("[green]✓[/green] Created [cyan]grai.yml[/cyan]")
        console.print("[green]✓[/green] Created [cyan]entities/customer.yml[/cyan]")
        console.print("[green]✓[/green] Created [cyan]entities/product.yml[/cyan]")
        console.print("[green]✓[/green] Created [cyan]relations/purchased.yml[/cyan]")
        console.print(
            "[green]✓[/green] Created [cyan]data/customers.csv[/cyan] (5 sample customers)"
        )
        console.print("[green]✓[/green] Created [cyan]data/products.csv[/cyan] (6 sample products)")
        console.print("[green]✓[/green] Created [cyan]data/purchased.csv[/cyan] (10 sample orders)")
        console.print(
            "[green]✓[/green] Created [cyan]load_data.cypher[/cyan] (data loading script)"
        )
        console.print("[green]✓[/green] Created [cyan]README.md[/cyan]")

        console.print(f"\n[bold green]✓ Successfully initialized project: {name}[/bold green]\n")

        # Show next steps
        next_steps = "[bold]Next Steps:[/bold]\n\n"
        if project_dir != Path(".").resolve():
            next_steps += f"1. cd {project_dir}\n"
            next_steps += "2. grai validate   # Check your definitions\n"
            next_steps += "3. grai build      # Compile to Cypher\n"
            next_steps += "4. grai run        # Create schema in Neo4j\n"
            next_steps += "5. Copy/paste load_data.cypher in Neo4j Browser to load data"
        else:
            next_steps += "1. grai validate   # Check your definitions\n"
            next_steps += "2. grai build      # Compile to Cypher\n"
            next_steps += "3. grai run        # Create schema in Neo4j\n"
            next_steps += "4. Copy/paste load_data.cypher in Neo4j Browser to load data"

        panel = Panel(
            next_steps,
            title="[bold cyan]Get Started[/bold cyan]",
            border_style="cyan",
        )
        console.print(panel)

    except Exception as e:
        console.print(f"[red]✗ Error initializing project: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def validate(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Treat warnings as errors.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation output.",
    ),
):
    """
    Validate entity and relation definitions.

    Checks for:
    - Missing entity references
    - Invalid key mappings
    - Duplicate property names
    - Circular dependencies
    """
    console.print("\n[bold cyan]🔍 Validating project...[/bold cyan]\n")

    try:
        # Load project
        project = load_project(project_dir)
        console.print(
            f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan] (v{project.version})"
        )
        console.print(f"  - {len(project.entities)} entities")
        console.print(f"  - {len(project.relations)} relations\n")

        # Validate project
        result = validate_project(project, strict=strict)

        # Show results
        if result.valid:
            console.print("[bold green]✓ Validation passed![/bold green]\n")

            if verbose and result.warnings:
                console.print("[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  [yellow]⚠[/yellow]  {warning}")
                console.print()

            return
        else:
            console.print("[bold red]✗ Validation failed![/bold red]\n")

            if result.errors:
                console.print("[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  [red]✗[/red]  {error}")
                console.print()

            if result.warnings:
                console.print("[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  [yellow]⚠[/yellow]  {warning}")
                console.print()

            raise typer.Exit(code=1)

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error during validation: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def build(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for compiled Cypher (default: target/neo4j).",
    ),
    filename: str = typer.Option(
        "compiled.cypher",
        "--filename",
        "-f",
        help="Output filename.",
    ),
    schema_only: bool = typer.Option(
        True,
        "--schema-only/--with-data",
        help="Generate only schema (constraints and indexes) without data loading statements.",
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip validation before compiling.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed build output.",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Force full rebuild, ignoring cache.",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't update cache after build.",
    ),
):
    """
    Build the project by compiling to Cypher.

    By default, only generates schema (constraints and indexes).
    Use --with-data to include data loading statements (requires LOAD CSV context).

    Validates the project (unless --skip-validation) and generates
    Neo4j Cypher statements in the target directory.

    Supports incremental builds by tracking file changes.
    """
    console.print("\n[bold cyan]🔨 Building project...[/bold cyan]\n")

    try:
        # Check for incremental build
        if not full:
            needs_rebuild, changes = should_rebuild(project_dir)

            if not needs_rebuild:
                console.print("[green]✓[/green] No changes detected, build is up to date")
                console.print("[dim]Use --full to force a complete rebuild[/dim]")
                return

            if verbose:
                total_changes = sum(len(files) for files in changes.values())
                console.print(f"[cyan]→[/cyan] Detected {total_changes} file change(s)")
                if changes["added"]:
                    console.print(f"  [green]+[/green] Added: {len(changes['added'])} file(s)")
                if changes["modified"]:
                    console.print(
                        f"  [yellow]~[/yellow] Modified: {len(changes['modified'])} file(s)"
                    )
                if changes["deleted"]:
                    console.print(f"  [red]-[/red] Deleted: {len(changes['deleted'])} file(s)")
                console.print()

        # Load project
        project = load_project(project_dir)
        console.print(
            f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan] (v{project.version})"
        )

        if verbose:
            console.print(f"  - {len(project.entities)} entities")
            console.print(f"  - {len(project.relations)} relations")

        # Validate unless skipped
        if not skip_validation:
            console.print("[cyan]→[/cyan] Validating...")
            result = validate_project(project)

            if not result.valid:
                console.print("[bold red]✗ Validation failed![/bold red]\n")

                for error in result.errors:
                    console.print(f"  [red]✗[/red]  {error}")

                console.print("\n[yellow]Fix validation errors before building[/yellow]")
                console.print("[yellow]Or use --skip-validation to bypass[/yellow]")
                raise typer.Exit(code=1)

            console.print("[green]✓[/green] Validation passed")

            if result.warnings and verbose:
                for warning in result.warnings:
                    console.print(f"  [yellow]⚠[/yellow]  {warning}")

        # Compile
        console.print("[cyan]→[/cyan] Compiling to Cypher...")

        # Determine output directory
        if output_dir is None:
            output_dir = project_dir / "target" / "neo4j"

        # Compile
        if schema_only:
            cypher = compile_schema_only(project)
            # Write manually for schema-only
            output_path = output_dir / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(cypher)
        else:
            output_path = compile_and_write(project, output_dir=output_dir, filename=filename)

        console.print("[green]✓[/green] Compiled successfully")
        console.print(f"[green]✓[/green] Wrote output to: [cyan]{output_path}[/cyan]")

        # Update cache
        if not no_cache:
            console.print("[cyan]→[/cyan] Updating build cache...")
            update_cache(project_dir, project.name, project.version)
            console.print("[green]✓[/green] Cache updated")

        # Show summary
        console.print("\n[bold green]✓ Build complete![/bold green]\n")

        if verbose:
            # Count constraints and statements
            cypher_content = output_path.read_text()
            constraint_count = cypher_content.count("CREATE CONSTRAINT")
            index_count = cypher_content.count("CREATE INDEX")
            merge_count = cypher_content.count("MERGE")

            table = Table(title="Build Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")

            table.add_row("Entities", str(len(project.entities)))
            table.add_row("Relations", str(len(project.relations)))
            table.add_row("Constraints", str(constraint_count))
            table.add_row("Indexes", str(index_count))
            table.add_row("Statements", str(merge_count))

            console.print(table)
            console.print()

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error during build: {e}[/red]")
        raise typer.Exit(code=1)


def _load_csv_data(driver, project_dir: Path, database: str, verbose: bool = False) -> bool:
    """
    Load CSV data from data/ directory if it exists.

    Reads CSV files and executes parameterized Cypher queries.
    Returns True if data was loaded successfully, False otherwise.
    """
    import csv

    from grai.core.loader import execute_cypher

    data_dir = project_dir / "data"

    if not data_dir.exists():
        return False

    try:
        total_records = 0

        # Load customers
        customers_csv = data_dir / "customers.csv"
        if customers_csv.exists():
            with open(customers_csv, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cypher = """
                    MERGE (c:customer {customer_id: $customer_id})
                    SET c.name = $name,
                        c.email = $email,
                        c.created_at = datetime($created_at)
                    """
                    result = execute_cypher(driver, cypher, parameters=row, database=database)
                    if result.success:
                        total_records += result.records_affected

        # Load products
        products_csv = data_dir / "products.csv"
        if products_csv.exists():
            with open(products_csv, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cypher = """
                    MERGE (p:product {product_id: $product_id})
                    SET p.name = $name,
                        p.category = $category,
                        p.price = toFloat($price)
                    """
                    result = execute_cypher(driver, cypher, parameters=row, database=database)
                    if result.success:
                        total_records += result.records_affected

        # Load purchases
        purchased_csv = data_dir / "purchased.csv"
        if purchased_csv.exists():
            with open(purchased_csv, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cypher = """
                    MATCH (c:customer {customer_id: $customer_id})
                    MATCH (p:product {product_id: $product_id})
                    MERGE (c)-[r:PURCHASED]->(p)
                    SET r.order_id = $order_id,
                        r.order_date = date($order_date),
                        r.quantity = toInteger($quantity),
                        r.total_amount = toFloat($total_amount)
                    """
                    result = execute_cypher(driver, cypher, parameters=row, database=database)
                    if result.success:
                        total_records += result.records_affected

        console.print("[green]✓[/green] CSV data loaded successfully")
        console.print(f"  Records affected: {total_records}")
        return True

    except Exception as e:
        console.print(f"[red]✗[/red] Error loading CSV data: {e}")
        return False


@app.command()
def compile(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for compiled Cypher.",
    ),
):
    """
    Compile project to Cypher (alias for 'build --skip-validation').

    Compiles without validation. Use 'build' for validation + compilation.
    """
    # Call build with skip_validation=True
    build(
        project_dir=project_dir,
        output_dir=output_dir,
        filename="compiled.cypher",
        schema_only=False,
        skip_validation=True,
        verbose=False,
    )


@app.command()
def run(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    uri: str = typer.Option(
        "bolt://localhost:7687",
        "--uri",
        "-u",
        help="Neo4j connection URI.",
    ),
    user: str = typer.Option(
        "neo4j",
        "--user",
        help="Neo4j username.",
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        help="Neo4j password.",
    ),
    database: str = typer.Option(
        "neo4j",
        "--database",
        "-d",
        help="Neo4j database name.",
    ),
    cypher_file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Cypher file to execute (default: target/neo4j/compiled.cypher).",
    ),
    schema_only: bool = typer.Option(
        True,
        "--schema-only/--with-data",
        help="Create only schema (constraints/indexes) without data loading statements.",
    ),
    load_csv: bool = typer.Option(
        False,
        "--load-csv",
        help="Load CSV data from data/ directory after creating schema.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be executed without running.",
    ),
    skip_build: bool = typer.Option(
        False,
        "--skip-build",
        help="Skip building before execution.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed execution output.",
    ),
):
    """
    Execute compiled Cypher against Neo4j database.

    By default, only creates the schema (constraints and indexes).
    Use --with-data to also execute data loading statements (requires LOAD CSV context).

    Builds the project (unless --skip-build) and executes the
    generated Cypher statements against a Neo4j database.
    """
    from grai.core.loader import (
        close_connection,
        connect_neo4j,
        execute_cypher_file,
        get_database_info,
        verify_connection,
    )

    console.print("\n[bold cyan]🚀 Running project against Neo4j...[/bold cyan]\n")

    driver = None

    try:
        # Build project first (unless skipped)
        if not skip_build:
            console.print("[cyan]→[/cyan] Building project...")
            build(
                project_dir=project_dir,
                output_dir=None,
                filename="compiled.cypher",
                schema_only=schema_only,
                skip_validation=False,
                verbose=False,
            )
            console.print()

        # Determine Cypher file
        if cypher_file is None:
            cypher_file = project_dir / "target" / "neo4j" / "compiled.cypher"

        if not cypher_file.exists():
            console.print(f"[red]✗ Cypher file not found: {cypher_file}[/red]")
            console.print("[yellow]Hint: Run 'grai build' first[/yellow]")
            raise typer.Exit(code=1)

        # Show dry run info
        if dry_run:
            console.print("[yellow]🔍 Dry run mode - showing what would be executed[/yellow]\n")
            console.print("[cyan]Connection:[/cyan]")
            console.print(f"  URI: {uri}")
            console.print(f"  User: {user}")
            console.print(f"  Database: {database}")
            console.print(f"\n[cyan]Cypher file:[/cyan] {cypher_file}\n")

            # Show first few lines of Cypher
            cypher_content = cypher_file.read_text()
            lines = cypher_content.split("\n")[:20]
            console.print("[cyan]First 20 lines of Cypher:[/cyan]")
            for line in lines:
                console.print(f"  {line}")

            if len(cypher_content.split("\n")) > 20:
                console.print("  ...")

            console.print("\n[yellow]ℹ️  Run without --dry-run to execute[/yellow]")
            return

        # Connect to Neo4j
        console.print(f"[cyan]→[/cyan] Connecting to Neo4j at {uri}...")

        try:
            driver = connect_neo4j(
                uri=uri,
                user=user,
                password=password,
                database=database,
            )
        except Exception as e:
            console.print(f"[red]✗ Connection failed: {e}[/red]")
            console.print("\n[yellow]Troubleshooting tips:[/yellow]")
            console.print("  1. Check that Neo4j is running")
            console.print("  2. Verify the URI is correct")
            console.print("  3. Check username and password")
            raise typer.Exit(code=1)

        console.print("[green]✓[/green] Connected to Neo4j")

        # Verify connection
        if not verify_connection(driver, database):
            console.print(f"[red]✗ Cannot access database: {database}[/red]")
            raise typer.Exit(code=1)

        # Get database info before execution
        if verbose:
            console.print("\n[cyan]Database info (before execution):[/cyan]")
            info = get_database_info(driver, database)
            console.print(f"  Nodes: {info.get('node_count', 0)}")
            console.print(f"  Relationships: {info.get('relationship_count', 0)}")
            console.print(f"  Labels: {', '.join(info.get('labels', []))}")
            console.print()

        # Execute Cypher
        console.print(f"[cyan]→[/cyan] Executing Cypher from {cypher_file.name}...")

        result = execute_cypher_file(driver, cypher_file, database=database)

        if result.success:
            console.print("[green]✓[/green] Execution successful")
            console.print(f"  Statements executed: {result.statements_executed}")
            console.print(f"  Records affected: {result.records_affected}")
            console.print(f"  Execution time: {result.execution_time:.2f}s")

            # Load CSV data if requested
            if load_csv:
                console.print("\n[cyan]→[/cyan] Loading CSV data...")
                csv_result = _load_csv_data(driver, project_dir, database, verbose)

                if not csv_result:
                    console.print(
                        "[yellow]⚠  No CSV data loaded (load_data.cypher not found or failed)[/yellow]"
                    )

            # Get database info after execution
            if verbose:
                console.print("\n[cyan]Database info (after execution):[/cyan]")
                info = get_database_info(driver, database)
                console.print(f"  Nodes: {info.get('node_count', 0)}")
                console.print(f"  Relationships: {info.get('relationship_count', 0)}")
                console.print(f"  Labels: {', '.join(info.get('labels', []))}")

            console.print("\n[bold green]✓ Successfully loaded data into Neo4j![/bold green]\n")
        else:
            console.print("[bold red]✗ Execution failed![/bold red]\n")

            for error in result.errors:
                console.print(f"  [red]✗[/red]  {error}")

            console.print()
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠  Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"[red]✗ Error during execution: {e}[/red]")
        raise typer.Exit(code=1)
    finally:
        if driver:
            close_connection(driver)


@app.command()
def export(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: graph-ir.json in project directory).",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format (currently only 'json' supported).",
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty/--compact",
        help="Pretty-print JSON output.",
    ),
    indent: int = typer.Option(
        2,
        "--indent",
        "-i",
        help="Number of spaces for JSON indentation.",
    ),
):
    """
    Export project to Graph IR (Intermediate Representation).

    Generates a JSON representation of the complete graph structure
    including entities, relations, properties, and metadata.
    """
    from grai.core.exporter import write_ir_file

    console.print("\n[bold cyan]📤 Exporting project to Graph IR...[/bold cyan]\n")

    try:
        # Load project
        project = load_project(project_dir)
        console.print(
            f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan] (v{project.version})"
        )

        # Determine output path
        if output is None:
            output = project_dir / "graph-ir.json"

        # Validate format
        if format.lower() != "json":
            console.print(f"[red]✗ Unsupported format: {format}[/red]")
            console.print("[yellow]Currently only 'json' format is supported[/yellow]")
            raise typer.Exit(code=1)

        # Export to file
        console.print(f"[cyan]→[/cyan] Exporting to {output}...")
        write_ir_file(project, output, pretty=pretty, indent=indent)

        # Show statistics
        from grai.core.exporter import export_to_ir

        ir = export_to_ir(project)
        stats = ir["statistics"]

        console.print("[green]✓[/green] Export complete!")
        console.print("\n[cyan]Statistics:[/cyan]")
        console.print(f"  Entities: {stats['entity_count']}")
        console.print(f"  Relations: {stats['relation_count']}")
        console.print(f"  Total Properties: {stats['total_properties']}")
        console.print(f"  File size: {output.stat().st_size:,} bytes")

        console.print(f"\n[bold green]✓ Graph IR exported to: {output}[/bold green]\n")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error during export: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def info(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
):
    """
    Show project information and statistics.
    """
    console.print("\n[bold cyan]📊 Project Information[/bold cyan]\n")

    try:
        # Load project
        project = load_project(project_dir)

        # Create info table
        table = Table(title=f"Project: {project.name}", show_header=False)
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row("Name", project.name)
        table.add_row("Version", project.version)
        table.add_row("Entities", str(len(project.entities)))
        table.add_row("Relations", str(len(project.relations)))

        # Count total properties
        total_entity_props = sum(len(e.properties) for e in project.entities)
        total_relation_props = sum(len(r.properties) for r in project.relations)

        table.add_row("Entity Properties", str(total_entity_props))
        table.add_row("Relation Properties", str(total_relation_props))

        console.print(table)
        console.print()

        # Show entities
        if project.entities:
            entity_table = Table(title="Entities")
            entity_table.add_column("Entity", style="cyan")
            entity_table.add_column("Source", style="white")
            entity_table.add_column("Keys", style="yellow")
            entity_table.add_column("Properties", style="green")

            for entity in project.entities:
                entity_table.add_row(
                    entity.entity,
                    entity.get_source_name(),
                    ", ".join(entity.keys),
                    str(len(entity.properties)),
                )

            console.print(entity_table)
            console.print()

        # Show relations
        if project.relations:
            relation_table = Table(title="Relations")
            relation_table.add_column("Relation", style="cyan")
            relation_table.add_column("From → To", style="white")
            relation_table.add_column("Source", style="white")
            relation_table.add_column("Properties", style="green")

            for relation in project.relations:
                relation_table.add_row(
                    relation.relation,
                    f"{relation.from_entity} → {relation.to_entity}",
                    relation.get_source_name(),
                    str(len(relation.properties)),
                )

            console.print(relation_table)
            console.print()

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error loading project: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def cache(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    clear: bool = typer.Option(
        False,
        "--clear",
        "-c",
        help="Clear the build cache.",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show cache contents.",
    ),
):
    """
    Manage build cache for incremental builds.

    View cache information or clear cached build data.
    """
    console.print("\n[bold cyan]💾 Build Cache Management[/bold cyan]\n")

    try:
        if clear:
            # Clear cache
            if clear_cache(project_dir):
                console.print("[green]✓[/green] Cache cleared successfully")
            else:
                console.print("[yellow]⚠[/yellow] No cache found")
            return

        # Load and show cache info
        build_cache = load_cache(project_dir)

        if build_cache is None:
            console.print("[yellow]⚠[/yellow] No cache found")
            console.print("[dim]Run 'grai build' to create cache[/dim]")
            return

        # Show cache summary
        console.print(f"[cyan]Project:[/cyan] {build_cache.project_name or 'Unknown'}")
        console.print(f"[cyan]Version:[/cyan] {build_cache.project_version or 'Unknown'}")
        console.print(f"[cyan]Created:[/cyan] {build_cache.created_at}")
        console.print(f"[cyan]Updated:[/cyan] {build_cache.last_updated}")
        console.print(f"[cyan]Cached files:[/cyan] {len(build_cache.entries)}")
        console.print()

        if show and build_cache.entries:
            # Show detailed cache entries
            table = Table(title="Cached Files")
            table.add_column("File", style="cyan")
            table.add_column("Hash", style="white")
            table.add_column("Size", style="green")
            table.add_column("Modified", style="yellow")

            for path, entry in sorted(build_cache.entries.items()):
                # Format size
                size_kb = entry.size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb > 1 else f"{entry.size} B"

                # Truncate hash for display
                short_hash = entry.hash[:12] + "..."

                # Format timestamp
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(entry.last_modified.replace("Z", "+00:00"))
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:  # noqa: BLE001
                    time_str = entry.last_modified[:16]

                table.add_row(path, short_hash, size_str, time_str)

            console.print(table)
            console.print()

        # Check for changes
        needs_rebuild, changes = should_rebuild(project_dir, build_cache)

        if needs_rebuild:
            total_changes = sum(len(files) for files in changes.values())
            console.print(f"[yellow]⚠[/yellow] {total_changes} file(s) changed since last build")

            if changes["added"]:
                console.print(f"  [green]+[/green] Added: {len(changes['added'])} file(s)")
                if show:
                    for file in sorted(changes["added"]):
                        console.print(f"    - {file.relative_to(project_dir)}")

            if changes["modified"]:
                console.print(f"  [yellow]~[/yellow] Modified: {len(changes['modified'])} file(s)")
                if show:
                    for file in sorted(changes["modified"]):
                        console.print(f"    - {file.relative_to(project_dir)}")

            if changes["deleted"]:
                console.print(f"  [red]-[/red] Deleted: {len(changes['deleted'])} file(s)")
                if show:
                    for file in sorted(changes["deleted"]):
                        console.print(f"    - {file.relative_to(project_dir)}")
        else:
            console.print("[green]✓[/green] Build is up to date")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def lineage(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    entity: Optional[str] = typer.Option(
        None,
        "--entity",
        "-e",
        help="Show lineage for specific entity.",
    ),
    relation: Optional[str] = typer.Option(
        None,
        "--relation",
        "-r",
        help="Show lineage for specific relation.",
    ),
    impact: Optional[str] = typer.Option(
        None,
        "--impact",
        "-i",
        help="Calculate impact analysis for entity.",
    ),
    visualize: Optional[str] = typer.Option(
        None,
        "--visualize",
        "-v",
        help="Generate visualization (mermaid or graphviz).",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for visualization.",
    ),
    focus: Optional[str] = typer.Option(
        None,
        "--focus",
        "-f",
        help="Focus visualization on specific entity.",
    ),
):
    """
    Analyze lineage and dependencies in the knowledge graph.

    Track entity relationships, calculate impact, and visualize dependencies.
    """
    console.print("\n[bold cyan]🔍 Lineage Analysis[/bold cyan]\n")

    try:
        # Load project
        project = load_project(project_dir)
        console.print(f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan]")

        # Build lineage graph
        console.print("[cyan]→[/cyan] Building lineage graph...")
        graph = build_lineage_graph(project)
        console.print(
            f"[green]✓[/green] Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges"
        )

        # Show entity lineage
        if entity:
            console.print(f"\n[bold]Entity Lineage: {entity}[/bold]\n")
            lineage = get_entity_lineage(graph, entity)

            if "error" in lineage:
                console.print(f"[red]✗ {lineage['error']}[/red]")
                raise typer.Exit(code=1)

            # Show source
            console.print(f"[cyan]Source:[/cyan] {lineage['source']}")

            # Show upstream
            if lineage["upstream"]:
                console.print(f"\n[cyan]Upstream ({len(lineage['upstream'])}):[/cyan]")
                for up in lineage["upstream"]:
                    console.print(f"  ← {up['node']} ({up['type']}) via {up['relation']}")
            else:
                console.print("\n[dim]No upstream dependencies[/dim]")

            # Show downstream
            if lineage["downstream"]:
                console.print(f"\n[cyan]Downstream ({len(lineage['downstream'])}):[/cyan]")
                for down in lineage["downstream"]:
                    console.print(f"  → {down['node']} ({down['type']}) via {down['relation']}")
            else:
                console.print("\n[dim]No downstream dependencies[/dim]")

        # Show relation lineage
        elif relation:
            console.print(f"\n[bold]Relation Lineage: {relation}[/bold]\n")
            lineage = get_relation_lineage(graph, relation)

            if "error" in lineage:
                console.print(f"[red]✗ {lineage['error']}[/red]")
                raise typer.Exit(code=1)

            # Show connection
            console.print(
                f"[cyan]Connects:[/cyan] {lineage['from_entity']} → {lineage['to_entity']}"
            )
            console.print(f"[cyan]Source:[/cyan] {lineage['source']}")

            # Show upstream
            if lineage["upstream"]:
                console.print(f"\n[cyan]Upstream ({len(lineage['upstream'])}):[/cyan]")
                for up in lineage["upstream"]:
                    console.print(f"  ← {up['node']} ({up['type']}) via {up['relation']}")

            # Show downstream
            if lineage["downstream"]:
                console.print(f"\n[cyan]Downstream ({len(lineage['downstream'])}):[/cyan]")
                for down in lineage["downstream"]:
                    console.print(f"  → {down['node']} ({down['type']}) via {down['relation']}")

        # Calculate impact
        elif impact:
            console.print(f"\n[bold]Impact Analysis: {impact}[/bold]\n")
            analysis = calculate_impact_analysis(graph, impact)

            if "error" in analysis:
                console.print(f"[red]✗ {analysis['error']}[/red]")
                raise typer.Exit(code=1)

            # Show impact score
            level_color = {
                "none": "dim",
                "low": "green",
                "medium": "yellow",
                "high": "red",
            }
            color = level_color.get(analysis["impact_level"], "white")

            console.print(f"[cyan]Impact Score:[/cyan] {analysis['impact_score']}")
            console.print(
                f"[cyan]Impact Level:[/cyan] [{color}]{analysis['impact_level'].upper()}[/{color}]"
            )

            # Show affected entities
            if analysis["affected_entities"]:
                console.print(
                    f"\n[cyan]Affected Entities ({len(analysis['affected_entities'])}):[/cyan]"
                )
                for ent in analysis["affected_entities"]:
                    console.print(f"  • {ent}")
            else:
                console.print("\n[dim]No affected entities[/dim]")

            # Show affected relations
            if analysis["affected_relations"]:
                console.print(
                    f"\n[cyan]Affected Relations ({len(analysis['affected_relations'])}):[/cyan]"
                )
                for rel in analysis["affected_relations"]:
                    console.print(f"  • {rel}")

        # Generate visualization
        elif visualize:
            console.print(f"\n[bold]Generating {visualize.upper()} visualization...[/bold]\n")

            if visualize.lower() == "mermaid":
                diagram = visualize_lineage_mermaid(graph, focus_entity=focus)
            elif visualize.lower() == "graphviz" or visualize.lower() == "dot":
                diagram = visualize_lineage_graphviz(graph, focus_entity=focus)
            else:
                console.print(f"[red]✗ Unknown visualization format: {visualize}[/red]")
                console.print("[yellow]Use 'mermaid' or 'graphviz'[/yellow]")
                raise typer.Exit(code=1)

            # Save to file or print
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(diagram)
                console.print(f"[green]✓[/green] Wrote visualization to: [cyan]{output}[/cyan]")
            else:
                console.print(diagram)

        # Show general statistics
        else:
            console.print("\n[bold]Lineage Statistics[/bold]\n")
            stats = get_lineage_statistics(graph)

            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Total Nodes", str(stats["total_nodes"]))
            table.add_row("Total Edges", str(stats["total_edges"]))
            table.add_row("Entities", str(stats["entity_count"]))
            table.add_row("Relations", str(stats["relation_count"]))
            table.add_row("Sources", str(stats["source_count"]))
            table.add_row("Max Downstream", str(stats["max_downstream_connections"]))
            if stats["most_connected_entity"]:
                table.add_row("Most Connected", stats["most_connected_entity"])

            console.print(table)
            console.print()

            console.print(
                "[dim]Use --entity, --relation, --impact, or --visualize for detailed analysis[/dim]"
            )

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def visualize(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    output: Path = typer.Option(
        Path("graph.html"),
        "--output",
        "-o",
        help="Output HTML file path.",
    ),
    format: str = typer.Option(
        "d3",
        "--format",
        "-f",
        help="Visualization format: d3 or cytoscape.",
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Custom title for visualization (defaults to project name).",
    ),
    width: int = typer.Option(
        1200,
        "--width",
        "-w",
        help="Width of visualization canvas in pixels.",
    ),
    height: int = typer.Option(
        800,
        "--height",
        "-h",
        help="Height of visualization canvas in pixels.",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        help="Open visualization in default browser after generation.",
    ),
):
    """
    Generate interactive HTML visualization of the knowledge graph.

    Creates an interactive web-based visualization using D3.js or Cytoscape.js.
    The resulting HTML file can be opened in any modern web browser.
    """
    console.print("\n[bold cyan]🎨 Generating Interactive Visualization[/bold cyan]\n")

    try:
        # Load project
        project = load_project(project_dir)
        console.print(f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan]")

        # Generate visualization based on format
        console.print(f"[cyan]→[/cyan] Generating {format.upper()} visualization...")

        if format.lower() == "d3":
            generate_d3_visualization(
                project=project,
                output_path=output,
                title=title,
                width=width,
                height=height,
            )
        elif format.lower() == "cytoscape":
            generate_cytoscape_visualization(
                project=project,
                output_path=output,
                title=title,
                width=width,
                height=height,
            )
        else:
            console.print(f"[red]✗ Unknown format: {format}[/red]")
            console.print("[yellow]Supported formats: d3, cytoscape[/yellow]")
            raise typer.Exit(code=1)

        console.print(f"[green]✓[/green] Generated visualization: [cyan]{output}[/cyan]")
        console.print(f"[dim]   Size: {output.stat().st_size:,} bytes[/dim]")
        console.print()
        console.print(
            "[bold]📱 Open the HTML file in your browser to view the interactive graph![/bold]"
        )

        # Optionally open in browser
        if open_browser:
            import webbrowser

            console.print("[cyan]→[/cyan] Opening in browser...")
            webbrowser.open(f"file://{output.absolute()}")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def docs(
    project_dir: Path = typer.Argument(
        Path("."),
        help="Path to grai.build project directory.",
    ),
    output_dir: Path = typer.Option(
        Path("target/docs"),
        "--output",
        "-o",
        help="Output directory for documentation.",
    ),
    serve: bool = typer.Option(
        False,
        "--serve",
        "-s",
        help="Start local server to view documentation.",
    ),
    port: int = typer.Option(
        8080,
        "--port",
        "-p",
        help="Port for documentation server.",
    ),
    open_browser: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open documentation in browser when serving.",
    ),
):
    """
    Generate and serve interactive documentation for your knowledge graph.

    Similar to 'dbt docs generate/serve', this command creates comprehensive
    HTML documentation including:
    - Entity and relation catalogs
    - Interactive graph visualization
    - Lineage diagrams
    - Searchable property reference

    Examples:
        grai docs                      # Generate docs in target/docs
        grai docs --serve              # Generate and serve on http://localhost:8080
        grai docs --serve --port 3000  # Serve on custom port
        grai docs --output ./my-docs   # Custom output directory
    """
    import http.server
    import socketserver
    import webbrowser

    from grai.core.exporter import export_to_json

    console.print("\n[bold cyan]📚 Generating Knowledge Graph Documentation[/bold cyan]\n")

    try:
        # Load project
        project = load_project(project_dir)
        console.print(f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan]")
        console.print(f"  - {len(project.entities)} entities")
        console.print(f"  - {len(project.relations)} relations")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export project data as JSON
        console.print("\n[cyan]→[/cyan] Exporting project data...")
        ir_data = export_to_json(project, pretty=False)

        # Generate main documentation HTML
        console.print("[cyan]→[/cyan] Generating documentation pages...")

        # Create index.html
        index_html = _generate_docs_index_html(project, ir_data)
        index_path = output_dir / "index.html"
        index_path.write_text(index_html)
        console.print("[green]✓[/green] Created index.html")

        # Create entity catalog page
        entities_html = _generate_entity_catalog_html(project)
        entities_path = output_dir / "entities.html"
        entities_path.write_text(entities_html)
        console.print("[green]✓[/green] Created entities.html")

        # Create relation catalog page
        relations_html = _generate_relation_catalog_html(project)
        relations_path = output_dir / "relations.html"
        relations_path.write_text(relations_html)
        console.print("[green]✓[/green] Created relations.html")

        # Create graph visualization page
        from grai.core.visualizer import generate_d3_visualization

        viz_path = output_dir / "graph.html"
        generate_d3_visualization(
            project=project,
            output_path=viz_path,
            title=f"{project.name} - Graph Visualization",
            width=1400,
            height=900,
        )
        console.print("[green]✓[/green] Created graph.html")

        # Create lineage page
        from grai.core.lineage import build_lineage_graph, visualize_lineage_mermaid

        lineage_graph = build_lineage_graph(project)
        mermaid_diagram = visualize_lineage_mermaid(lineage_graph)
        lineage_html = _generate_lineage_html(project, mermaid_diagram)
        lineage_path = output_dir / "lineage.html"
        lineage_path.write_text(lineage_html)
        console.print("[green]✓[/green] Created lineage.html")

        console.print(
            f"\n[green]✓[/green] Documentation generated in: [cyan]{output_dir.absolute()}[/cyan]"
        )

        # Serve documentation if requested
        if serve:
            console.print("\n[bold cyan]🌐 Starting documentation server...[/bold cyan]\n")

            # Change to docs directory
            import os

            os.chdir(output_dir.absolute())

            # Create server with address reuse enabled
            handler = http.server.SimpleHTTPRequestHandler  # noqa: N806

            # Enable address reuse to avoid "Address already in use" errors
            socketserver.TCPServer.allow_reuse_address = True

            try:
                with socketserver.TCPServer(("", port), handler) as httpd:
                    console.print(
                        f"[green]✓[/green] Server running at: [cyan]http://localhost:{port}[/cyan]"
                    )
                    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

                    # Open browser
                    if open_browser:
                        console.print("[cyan]→[/cyan] Opening in browser...")
                        webbrowser.open(f"http://localhost:{port}")

                    # Serve forever
                    try:
                        httpd.serve_forever()
                    except KeyboardInterrupt:
                        console.print("\n\n[yellow]Stopping server...[/yellow]")

            except KeyboardInterrupt:
                # Catch any interrupt that happens during setup
                console.print("\n\n[yellow]Server stopped[/yellow]")
            except OSError as e:
                if "Address already in use" in str(e):
                    console.print(f"[red]✗ Port {port} is already in use[/red]")
                    console.print(
                        f"[yellow]Try a different port: grai docs --serve --port {port + 1}[/yellow]"
                    )
                else:
                    raise
        else:
            console.print("\n[bold]💡 To view documentation:[/bold]")
            console.print(f"   Open: [cyan]file://{index_path.absolute()}[/cyan]")
            console.print("   Or run: [cyan]grai docs --serve[/cyan]")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        raise typer.Exit(code=1)


def _generate_docs_index_html(project: Project, ir_data: str) -> str:
    """Generate the main documentation index page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} - Knowledge Graph Documentation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        nav {{
            background: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        nav a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 2rem;
            font-weight: 500;
            transition: color 0.2s;
        }}

        nav a:hover {{
            color: #764ba2;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}

        .card {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}

        .card h3 {{
            color: #667eea;
            margin-bottom: 0.5rem;
            font-size: 1.3rem;
        }}

        .card p {{
            color: #666;
            margin-bottom: 1rem;
        }}

        .card a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}

        .stat {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #666;
            margin-top: 0.5rem;
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: #999;
            margin-top: 4rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 {project.name}</h1>
        <p>{project.description if hasattr(project, 'description') and project.description else 'Knowledge Graph Documentation'}</p>
        <p style="opacity: 0.7; font-size: 0.9rem; margin-top: 0.5rem;">Version {project.version}</p>
    </div>

    <nav>
        <a href="index.html">Home</a>
        <a href="entities.html">Entities</a>
        <a href="relations.html">Relations</a>
        <a href="graph.html">Graph Visualization</a>
        <a href="lineage.html">Lineage</a>
    </nav>

    <div class="container">
        <h2>Project Overview</h2>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(project.entities)}</div>
                <div class="stat-label">Entities</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(project.relations)}</div>
                <div class="stat-label">Relations</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(len(e.properties) for e in project.entities)}</div>
                <div class="stat-label">Entity Properties</div>
            </div>
            <div class="stat">
                <div class="stat-value">{sum(len(r.properties) for r in project.relations)}</div>
                <div class="stat-label">Relation Properties</div>
            </div>
        </div>

        <h2>Documentation Sections</h2>

        <div class="card-grid">
            <div class="card">
                <h3>📦 Entities</h3>
                <p>Browse all entities in your knowledge graph, including their properties, keys, and source definitions.</p>
                <a href="entities.html">View Entities →</a>
            </div>

            <div class="card">
                <h3>🔗 Relations</h3>
                <p>Explore relationships between entities, their mappings, and additional properties.</p>
                <a href="relations.html">View Relations →</a>
            </div>

            <div class="card">
                <h3>🕸️ Graph Visualization</h3>
                <p>Interactive visualization of your entire knowledge graph showing entities and their connections.</p>
                <a href="graph.html">View Graph →</a>
            </div>

            <div class="card">
                <h3>🔄 Lineage</h3>
                <p>Visualize data lineage and dependencies between entities, relations, and source systems.</p>
                <a href="lineage.html">View Lineage →</a>
            </div>
        </div>
    </div>

    <footer>
        <p>Generated by <strong>grai.build</strong> - Declarative Knowledge Graph Modeling</p>
    </footer>
</body>
</html>
"""


def _generate_entity_catalog_html(project: Project) -> str:
    """Generate entity catalog HTML page."""
    entities_html = ""
    for entity in sorted(project.entities, key=lambda e: e.entity):
        props_html = "".join(
            [
                f"<tr><td><code>{p.name}</code></td><td>{p.type.value}</td><td>{'✓' if getattr(p, 'required', False) else ''}</td><td>{getattr(p, 'description', '')}</td></tr>"
                for p in entity.properties
            ]
        )

        # Build source info with enhanced details if available
        source_config = entity.get_source_config()
        source_html = f"<div><strong>Source:</strong> <code>{source_config.name}</code>"
        if source_config.type:
            source_html += f" <span style='color: #667eea; font-size: 0.9em;'>({source_config.type.value})</span>"
        source_html += "</div>"

        # Add additional source metadata if present
        source_meta_items = []
        if source_config.database:
            source_meta_items.append(
                f"<div><strong>Database:</strong> <code>{source_config.database}</code></div>"
            )
        if source_config.db_schema:
            source_meta_items.append(
                f"<div><strong>Schema:</strong> <code>{source_config.db_schema}</code></div>"
            )
        if source_config.connection:
            source_meta_items.append(
                f"<div><strong>Connection:</strong> <code>{source_config.connection}</code></div>"
            )
        source_meta_html = "".join(source_meta_items)

        entities_html += f"""
        <div class="entity-card">
            <h3>🔹 {entity.entity}</h3>
            <div class="meta">
                {source_html}
                <div><strong>Keys:</strong> <code>{', '.join(entity.keys)}</code></div>
                {source_meta_html}
            </div>
            {f'<p class="description">{entity.description}</p>' if hasattr(entity, 'description') and entity.description else ''}
            <h4>Properties ({len(entity.properties)})</h4>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {props_html if props_html else '<tr><td colspan="4"><em>No properties defined</em></td></tr>'}
                </tbody>
            </table>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Entities - {project.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        nav {{
            background: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        nav a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 2rem;
            font-weight: 500;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .entity-card {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .entity-card h3 {{
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }}
        .meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .description {{
            padding: 1rem;
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            margin: 1rem 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        code {{
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 Entities</h1>
        <p>{project.name} - Entity Catalog</p>
    </div>

    <nav>
        <a href="index.html">Home</a>
        <a href="entities.html">Entities</a>
        <a href="relations.html">Relations</a>
        <a href="graph.html">Graph Visualization</a>
        <a href="lineage.html">Lineage</a>
    </nav>

    <div class="container">
        <p style="margin-bottom: 2rem;">
            This page lists all entities in your knowledge graph. Each entity represents a node type with defined properties and keys.
        </p>
        {entities_html}
    </div>
</body>
</html>
"""


def _generate_relation_catalog_html(project: Project) -> str:
    """Generate relation catalog HTML page."""
    relations_html = ""
    for relation in sorted(project.relations, key=lambda r: r.relation):
        props_html = "".join(
            [
                f"<tr><td><code>{p.name}</code></td><td>{p.type.value}</td><td>{'✓' if getattr(p, 'required', False) else ''}</td><td>{getattr(p, 'description', '')}</td></tr>"
                for p in relation.properties
            ]
        )

        # Build source info with enhanced details if available
        source_config = relation.get_source_config()
        source_html = f"<div><strong>Source:</strong> <code>{source_config.name}</code>"
        if source_config.type:
            source_html += f" <span style='color: #667eea; font-size: 0.9em;'>({source_config.type.value})</span>"
        source_html += "</div>"

        # Add additional source metadata if present
        source_meta_items = []
        if source_config.database:
            source_meta_items.append(
                f"<div><strong>Database:</strong> <code>{source_config.database}</code></div>"
            )
        if source_config.db_schema:
            source_meta_items.append(
                f"<div><strong>Schema:</strong> <code>{source_config.db_schema}</code></div>"
            )
        if source_config.connection:
            source_meta_items.append(
                f"<div><strong>Connection:</strong> <code>{source_config.connection}</code></div>"
            )

        relations_html += f"""
        <div class="relation-card">
            <h3>🔗 {relation.relation}</h3>
            <div class="mapping">
                <span class="entity">{relation.from_entity}</span>
                <span class="arrow">→</span>
                <span class="entity">{relation.to_entity}</span>
            </div>
            <div class="meta">
                {source_html}
                <div><strong>From Key:</strong> <code>{relation.mappings.from_key}</code></div>
                <div><strong>To Key:</strong> <code>{relation.mappings.to_key}</code></div>
                {("".join(source_meta_items))}
            </div>
            {f'<p class="description">{relation.description}</p>' if hasattr(relation, 'description') and relation.description else ''}
            <h4>Properties ({len(relation.properties)})</h4>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Required</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {props_html if props_html else '<tr><td colspan="4"><em>No properties defined</em></td></tr>'}
                </tbody>
            </table>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relations - {project.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        nav {{
            background: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        nav a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 2rem;
            font-weight: 500;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .relation-card {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .relation-card h3 {{
            color: #764ba2;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }}
        .mapping {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 1rem;
            background: #f8f3ff;
            border-radius: 4px;
            font-size: 1.1rem;
        }}
        .entity {{
            background: #667eea;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 500;
        }}
        .arrow {{
            font-size: 1.5rem;
            color: #764ba2;
        }}
        .meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .description {{
            padding: 1rem;
            background: #f0f4ff;
            border-left: 4px solid #764ba2;
            margin: 1rem 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        code {{
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔗 Relations</h1>
        <p>{project.name} - Relation Catalog</p>
    </div>

    <nav>
        <a href="index.html">Home</a>
        <a href="entities.html">Entities</a>
        <a href="relations.html">Relations</a>
        <a href="graph.html">Graph Visualization</a>
        <a href="lineage.html">Lineage</html>
    </nav>

    <div class="container">
        <p style="margin-bottom: 2rem;">
            This page lists all relations in your knowledge graph. Each relation represents an edge type connecting two entity types.
        </p>
        {relations_html}
    </div>
</body>
</html>
"""


def _generate_lineage_html(project: Project, mermaid_diagram: str) -> str:
    """Generate lineage HTML page with Mermaid diagram."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lineage - {project.name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        nav {{
            background: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        nav a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 2rem;
            font-weight: 500;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .diagram-container {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin: 2rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow-x: auto;
        }}
    </style>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</head>
<body>
    <div class="header">
        <h1>🔄 Lineage</h1>
        <p>{project.name} - Data Lineage & Dependencies</p>
    </div>

    <nav>
        <a href="index.html">Home</a>
        <a href="entities.html">Entities</a>
        <a href="relations.html">Relations</a>
        <a href="graph.html">Graph Visualization</a>
        <a href="lineage.html">Lineage</a>
    </nav>

    <div class="container">
        <p style="margin-bottom: 2rem;">
            This diagram shows the data lineage of your knowledge graph, illustrating how source systems flow into entities and how entities connect through relations.
        </p>

        <div class="diagram-container">
            <pre class="mermaid">
{mermaid_diagram}
            </pre>
        </div>
    </div>
</body>
</html>
"""


def main_cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main_cli()

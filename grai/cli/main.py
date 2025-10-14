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

from grai.core.parser import load_project
from grai.core.validator import validate_project
from grai.core.compiler import compile_and_write, compile_schema_only
from grai.core.cache import (
    should_rebuild,
    update_cache,
    load_cache,
    clear_cache,
    get_changed_files,
)
from grai.core.lineage import (
    build_lineage_graph,
    get_entity_lineage,
    get_relation_lineage,
    calculate_impact_analysis,
    get_lineage_statistics,
    export_lineage_to_dict,
    visualize_lineage_mermaid,
    visualize_lineage_graphviz,
)
from grai.core.visualizer import (
    generate_d3_visualization,
    generate_cytoscape_visualization,
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
        console.print("grai.build version 0.1.0", style="bold green")
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
        console.print(f"[red]✗ Project already initialized (grai.yml exists)[/red]")
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
        
        # Create example entity
        customer_yml = """entity: customer
source: analytics.customers
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
"""
        (project_dir / "entities" / "customer.yml").write_text(customer_yml)
        
        # Create example entity
        product_yml = """entity: product
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
"""
        (project_dir / "entities" / "product.yml").write_text(product_yml)
        
        # Create example relation
        purchased_yml = """relation: PURCHASED
from: customer
to: product
source: analytics.orders
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
        
        # Create data loading script
        load_script = f"""#!/usr/bin/env python3
\"\"\"
Load sample data from CSV files into Neo4j.

This script demonstrates how to use LOAD CSV to import data
that matches the grai.build schema definitions.
\"\"\"

from pathlib import Path
from grai.core.loader.neo4j_loader import (
    connect_neo4j,
    execute_cypher,
    close_connection,
)

# Connection details (update these for your Neo4j instance)
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "graipassword"  # Change this!

# Get the project directory (where this script is located)
PROJECT_DIR = Path(__file__).parent.absolute()
DATA_DIR = PROJECT_DIR / "data"


def load_customers(driver):
    \\\"\\\"\\\"Load customers from CSV.\\\"\\\"\\\"
    csv_path = DATA_DIR / "customers.csv"
    
    cypher = f\\\"\\\"\\\"
    LOAD CSV WITH HEADERS FROM 'file:///{{csv_path}}' AS row
    MERGE (c:customer {{{{customer_id: row.customer_id}}}})
    SET c.name = row.name,
        c.email = row.email,
        c.created_at = datetime(row.created_at)
    \\\"\\\"\\\"
    
    result = execute_cypher(driver, cypher)
    return result


def load_products(driver):
    \\\"\\\"\\\"Load products from CSV.\\\"\\\"\\\"
    csv_path = DATA_DIR / "products.csv"
    
    cypher = f\\\"\\\"\\\"
    LOAD CSV WITH HEADERS FROM 'file:///{{csv_path}}' AS row
    MERGE (p:product {{{{product_id: row.product_id}}}})
    SET p.name = row.name,
        p.category = row.category,
        p.price = toFloat(row.price)
    \\\"\\\"\\\"
    
    result = execute_cypher(driver, cypher)
    return result


def load_purchases(driver):
    \\\"\\\"\\\"Load purchase relationships from CSV.\\\"\\\"\\\"
    csv_path = DATA_DIR / "purchased.csv"
    
    cypher = f\\\"\\\"\\\"
    LOAD CSV WITH HEADERS FROM 'file:///{{csv_path}}' AS row
    MATCH (c:customer {{{{customer_id: row.customer_id}}}})
    MATCH (p:product {{{{product_id: row.product_id}}}})
    MERGE (c)-[r:PURCHASED]->(p)
    SET r.order_id = row.order_id,
        r.order_date = date(row.order_date),
        r.quantity = toInteger(row.quantity),
        r.total_amount = toFloat(row.total_amount)
    \\\"\\\"\\\"
    
    result = execute_cypher(driver, cypher)
    return result


def main():
    \"\"\"Main function to load all data.\"\"\"
    print("\\n📦 Loading sample data from CSV files...\\n")
    
    try:
        # Connect to Neo4j
        print(f"🔌 Connecting to {{{{URI}}}}...")
        driver = connect_neo4j(uri=URI, user=USER, password=PASSWORD)
        print("✅ Connected successfully!\\\\n")
        
        # Load customers
        print("📊 Loading customers...")
        result = load_customers(driver)
        if result.success:
            print(f"   ✅ Loaded customers successfully")
        else:
            print(f"   ❌ Error loading customers:")
            for error in result.errors:
                print(f"      {{{{error}}}}")
        
        # Load products
        print("📊 Loading products...")
        result = load_products(driver)
        if result.success:
            print(f"   ✅ Loaded products successfully")
        else:
            print(f"   ❌ Error loading products:")
            for error in result.errors:
                print(f"      {{{{error}}}}")
        
        # Load purchases
        print("📊 Loading purchases...")
        result = load_purchases(driver)
        if result.success:
            print(f"   ✅ Loaded purchases successfully")
        else:
            print(f"   ❌ Error loading purchases:")
            for error in result.errors:
                print(f"      {{{{error}}}}")
        
        # Close connection
        close_connection(driver)
        
        print("\\\\n✅ Data loading complete!\\\\n")
        print("🌐 Open Neo4j Browser (http://localhost:7474) to explore your graph\\\\n")
        
    except Exception as e:
        print(f"\\\\n❌ Error: {{{{e}}}}\\\\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
"""
        (project_dir / "load_data.py").write_text(load_script)
        
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

1. Edit entity definitions in `entities/`
2. Edit relation definitions in `relations/`
3. Modify CSV files in `data/` with your own data
4. Run `grai validate` to check for errors
5. Run `grai build` to compile to Cypher
6. Run `grai run` to update schema
7. Run `python load_data.py` to load your data

## Learn More

- [grai.build Documentation](https://github.com/grai-build/grai.build)
- [Neo4j Documentation](https://neo4j.com/docs/)
"""
        (project_dir / "README.md").write_text(readme)
        
        console.print("[green]✓[/green] Created project structure")
        console.print(f"[green]✓[/green] Created [cyan]grai.yml[/cyan]")
        console.print(f"[green]✓[/green] Created [cyan]entities/customer.yml[/cyan]")
        console.print(f"[green]✓[/green] Created [cyan]entities/product.yml[/cyan]")
        console.print(f"[green]✓[/green] Created [cyan]relations/purchased.yml[/cyan]")
        console.print(f"[green]✓[/green] Created [cyan]data/customers.csv[/cyan] (5 sample customers)")
        console.print(f"[green]✓[/green] Created [cyan]data/products.csv[/cyan] (6 sample products)")
        console.print(f"[green]✓[/green] Created [cyan]data/purchased.csv[/cyan] (10 sample orders)")
        console.print(f"[green]✓[/green] Created [cyan]load_data.py[/cyan] (data loading script)")
        console.print(f"[green]✓[/green] Created [cyan]README.md[/cyan]")
        
        console.print(f"\n[bold green]✓ Successfully initialized project: {name}[/bold green]\n")
        
        # Show next steps
        next_steps = "[bold]Next Steps:[/bold]\n\n"
        if project_dir != Path(".").resolve():
            next_steps += f"1. cd {project_dir}\n"
            next_steps += f"2. grai validate   # Check your definitions\n"
            next_steps += f"3. grai build      # Compile to Cypher\n"
            next_steps += f"4. grai run        # Execute against Neo4j"
        else:
            next_steps += f"1. grai validate   # Check your definitions\n"
            next_steps += f"2. grai build      # Compile to Cypher\n"
            next_steps += f"3. grai run        # Execute against Neo4j"
        
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
    console.print(f"\n[bold cyan]🔍 Validating project...[/bold cyan]\n")
    
    try:
        # Load project
        project = load_project(project_dir)
        console.print(f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan] (v{project.version})")
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
        False,
        "--schema-only",
        help="Generate only schema (constraints and indexes).",
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
    
    Validates the project (unless --skip-validation) and generates
    Neo4j Cypher statements in the target directory.
    
    Supports incremental builds by tracking file changes.
    """
    console.print(f"\n[bold cyan]🔨 Building project...[/bold cyan]\n")
    
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
                    console.print(f"  [yellow]~[/yellow] Modified: {len(changes['modified'])} file(s)")
                if changes["deleted"]:
                    console.print(f"  [red]-[/red] Deleted: {len(changes['deleted'])} file(s)")
                console.print()
        
        # Load project
        project = load_project(project_dir)
        console.print(f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan] (v{project.version})")
        
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
        
        console.print(f"[green]✓[/green] Compiled successfully")
        console.print(f"[green]✓[/green] Wrote output to: [cyan]{output_path}[/cyan]")
        
        # Update cache
        if not no_cache:
            console.print("[cyan]→[/cyan] Updating build cache...")
            update_cache(project_dir, project.name, project.version)
            console.print("[green]✓[/green] Cache updated")
        
        # Show summary
        console.print(f"\n[bold green]✓ Build complete![/bold green]\n")
        
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
    from grai.core.loader import connect_neo4j, execute_cypher_file, verify_connection, close_connection, get_database_info
    
    console.print(f"\n[bold cyan]🚀 Running project against Neo4j...[/bold cyan]\n")
    
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
            console.print(f"[cyan]Connection:[/cyan]")
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
            
            console.print(f"\n[yellow]ℹ️  Run without --dry-run to execute[/yellow]")
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
            
            # Get database info after execution
            if verbose:
                console.print("\n[cyan]Database info (after execution):[/cyan]")
                info = get_database_info(driver, database)
                console.print(f"  Nodes: {info.get('node_count', 0)}")
                console.print(f"  Relationships: {info.get('relationship_count', 0)}")
                console.print(f"  Labels: {', '.join(info.get('labels', []))}")
            
            console.print(f"\n[bold green]✓ Successfully loaded data into Neo4j![/bold green]\n")
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
    from grai.core.exporter import export_to_json, write_ir_file
    
    console.print(f"\n[bold cyan]📤 Exporting project to Graph IR...[/bold cyan]\n")
    
    try:
        # Load project
        project = load_project(project_dir)
        console.print(f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan] (v{project.version})")
        
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
        
        console.print(f"[green]✓[/green] Export complete!")
        console.print(f"\n[cyan]Statistics:[/cyan]")
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
    console.print(f"\n[bold cyan]📊 Project Information[/bold cyan]\n")
    
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
                    entity.source,
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
                    relation.source,
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
    console.print(f"\n[bold cyan]💾 Build Cache Management[/bold cyan]\n")
    
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
                except:
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
    console.print(f"\n[bold cyan]🔍 Lineage Analysis[/bold cyan]\n")
    
    try:
        # Load project
        project = load_project(project_dir)
        console.print(f"[green]✓[/green] Loaded project: [cyan]{project.name}[/cyan]")
        
        # Build lineage graph
        console.print("[cyan]→[/cyan] Building lineage graph...")
        graph = build_lineage_graph(project)
        console.print(f"[green]✓[/green] Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        
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
            console.print(f"[cyan]Connects:[/cyan] {lineage['from_entity']} → {lineage['to_entity']}")
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
            console.print(f"[cyan]Impact Level:[/cyan] [{color}]{analysis['impact_level'].upper()}[/{color}]")
            
            # Show affected entities
            if analysis["affected_entities"]:
                console.print(f"\n[cyan]Affected Entities ({len(analysis['affected_entities'])}):[/cyan]")
                for ent in analysis["affected_entities"]:
                    console.print(f"  • {ent}")
            else:
                console.print("\n[dim]No affected entities[/dim]")
            
            # Show affected relations
            if analysis["affected_relations"]:
                console.print(f"\n[cyan]Affected Relations ({len(analysis['affected_relations'])}):[/cyan]")
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
            
            console.print("[dim]Use --entity, --relation, --impact, or --visualize for detailed analysis[/dim]")
        
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
    console.print(f"\n[bold cyan]🎨 Generating Interactive Visualization[/bold cyan]\n")
    
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
        console.print("[bold]📱 Open the HTML file in your browser to view the interactive graph![/bold]")
        
        # Optionally open in browser
        if open_browser:
            import webbrowser
            console.print(f"[cyan]→[/cyan] Opening in browser...")
            webbrowser.open(f"file://{output.absolute()}")
        
    except FileNotFoundError as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("[yellow]Hint: Run 'grai init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)


def main_cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main_cli()

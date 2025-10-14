#!/usr/bin/env python3
"""Demo script for the Cypher Compiler.

This demonstrates:
1. Loading a project from YAML files
2. Compiling entities and relations to Cypher
3. Writing compiled output to target directory
4. Generating schema-only scripts
5. Generating LOAD CSV statements
"""

from pathlib import Path
from grai.core.parser import load_project
from grai.core.compiler import (
    compile_entity,
    compile_relation,
    compile_project,
    compile_and_write,
    compile_schema_only,
    generate_load_csv_statements,
)


def main():
    print("=" * 80)
    print("Cypher Compiler Demo")
    print("=" * 80)
    print()

    # Load the project
    templates_dir = Path(__file__).parent / "templates"
    print(f"📂 Loading project from: {templates_dir}")
    project = load_project(templates_dir)
    print(f"✅ Loaded project: {project.name} (v{project.version})")
    print(f"   - Entities: {len(project.entities)}")
    print(f"   - Relations: {len(project.relations)}")
    print()

    # Compile individual entities
    print("=" * 80)
    print("1. Compiling Individual Entities")
    print("=" * 80)
    print()
    
    for entity in project.entities:
        print(f"Entity: {entity.entity}")
        print("-" * 80)
        cypher = compile_entity(entity)
        print(cypher)
        print()

    # Compile individual relations
    print("=" * 80)
    print("2. Compiling Individual Relations")
    print("=" * 80)
    print()
    
    for relation in project.relations:
        print(f"Relation: {relation.relation}")
        print("-" * 80)
        cypher = compile_relation(relation)
        print(cypher)
        print()

    # Compile full project
    print("=" * 80)
    print("3. Compiling Full Project")
    print("=" * 80)
    print()
    
    full_cypher = compile_project(project)
    print(full_cypher[:500] + "..." if len(full_cypher) > 500 else full_cypher)
    print()

    # Write to file
    print("=" * 80)
    print("4. Writing Compiled Output")
    print("=" * 80)
    print()
    
    output_path = compile_and_write(project, output_dir=templates_dir / "target/neo4j")
    print(f"✅ Wrote compiled Cypher to: {output_path}")
    print()

    # Generate schema-only script
    print("=" * 80)
    print("5. Generating Schema-Only Script")
    print("=" * 80)
    print()
    
    schema_cypher = compile_schema_only(project)
    print(schema_cypher)
    print()

    # Generate LOAD CSV statements
    print("=" * 80)
    print("6. Generating LOAD CSV Statements")
    print("=" * 80)
    print()
    
    csv_statements = generate_load_csv_statements(project, data_dir="file:///data")
    for name, statement in csv_statements.items():
        print(f"--- {name} ---")
        print(statement)
        print()

    print("=" * 80)
    print("✅ Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

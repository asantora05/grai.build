"""
Demo script showing how to use the YAML parser.

This demonstrates loading entity and relation definitions from YAML files.
"""

from pathlib import Path

from grai.core.parser import (
    load_entities_from_directory,
    load_project,
    load_relations_from_directory,
    parse_entity_file,
    parse_relation_file,
)


def demo_parser():
    """Demonstrate the YAML parser."""
    
    print("📦 grai.build YAML Parser Demo\n")
    
    # Get the templates directory
    templates_dir = Path(__file__).parent / "templates"
    
    if not templates_dir.exists():
        print("⚠️  Templates directory not found. Please run this from the project root.")
        return
    
    # 1. Parse individual entity file
    print("1️⃣ Parsing individual entity file...")
    customer_file = templates_dir / "entities" / "customer.yml"
    if customer_file.exists():
        customer = parse_entity_file(customer_file)
        print(f"   ✅ Parsed entity: {customer.entity}")
        print(f"      Source: {customer.source}")
        print(f"      Keys: {customer.keys}")
        print(f"      Properties: {len(customer.properties)}")
        print(f"      Description: {customer.description}")
    
    # 2. Parse individual relation file
    print("\n2️⃣ Parsing individual relation file...")
    purchased_file = templates_dir / "relations" / "purchased.yml"
    if purchased_file.exists():
        purchased = parse_relation_file(purchased_file)
        print(f"   ✅ Parsed relation: {purchased.relation}")
        print(f"      From: {purchased.from_entity} -> To: {purchased.to_entity}")
        print(f"      Source: {purchased.source}")
        print(f"      Mappings: {purchased.mappings.from_key} -> {purchased.mappings.to_key}")
        print(f"      Properties: {len(purchased.properties)}")
    
    # 3. Load all entities from directory
    print("\n3️⃣ Loading all entities from directory...")
    entities_dir = templates_dir / "entities"
    if entities_dir.exists():
        entities = load_entities_from_directory(entities_dir)
        print(f"   ✅ Loaded {len(entities)} entities:")
        for entity in entities:
            print(f"      • {entity.entity} (keys: {', '.join(entity.keys)})")
    
    # 4. Load all relations from directory
    print("\n4️⃣ Loading all relations from directory...")
    relations_dir = templates_dir / "relations"
    if relations_dir.exists():
        relations = load_relations_from_directory(relations_dir)
        print(f"   ✅ Loaded {len(relations)} relations:")
        for relation in relations:
            print(f"      • {relation.relation}: {relation.from_entity} -> {relation.to_entity}")
    
    # 5. Load complete project
    print("\n5️⃣ Loading complete project...")
    try:
        project = load_project(templates_dir)
        print(f"   ✅ Loaded project: {project.name} (v{project.version})")
        print(f"      Entities: {len(project.entities)}")
        print(f"      Relations: {len(project.relations)}")
        print(f"      Config keys: {', '.join(project.config.keys())}")
        
        # Show entity details
        if project.entities:
            print(f"\n   📊 Entity Details:")
            for entity in project.entities:
                print(f"      • {entity.entity}:")
                print(f"        - Source: {entity.source}")
                print(f"        - Keys: {entity.keys}")
                print(f"        - Properties: {[p.name for p in entity.properties]}")
        
        # Show relation details
        if project.relations:
            print(f"\n   🔗 Relation Details:")
            for relation in project.relations:
                print(f"      • {relation.relation}:")
                print(f"        - From: {relation.from_entity} ({relation.mappings.from_key})")
                print(f"        - To: {relation.to_entity} ({relation.mappings.to_key})")
                print(f"        - Properties: {[p.name for p in relation.properties]}")
        
        # Show config
        if project.config:
            print(f"\n   ⚙️  Configuration:")
            for key, value in project.config.items():
                print(f"      • {key}: {value}")
    
    except Exception as e:
        print(f"   ⚠️  Error loading project: {e}")
    
    print("\n✨ Parser demo complete!\n")
    print("📝 The parser successfully:")
    print("   ✅ Loads YAML files into Pydantic models")
    print("   ✅ Validates entity and relation definitions")
    print("   ✅ Handles properties with types and metadata")
    print("   ✅ Discovers files recursively in directories")
    print("   ✅ Loads complete projects with manifest + entities + relations")
    print("\n🚀 Next steps:")
    print("   - Implement the validator to check entity references")
    print("   - Implement the Cypher compiler")
    print("   - Build the CLI commands")


if __name__ == "__main__":
    demo_parser()

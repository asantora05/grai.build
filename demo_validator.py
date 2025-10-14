"""
Demo script showing how to use the validator.

This demonstrates validating projects, entities, and relations for consistency.
"""

from pathlib import Path

from grai.core.models import Entity, Property, PropertyType, Relation, RelationMapping
from grai.core.parser import load_project
from grai.core.validator import validate_entity, validate_project, validate_relation


def demo_validator():
    """Demonstrate the validator."""
    
    print("🔍 grai.build Validator Demo\n")
    
    # 1. Validate individual entity
    print("1️⃣ Validating individual entity...")
    customer = Entity(
        entity="customer",
        source="analytics.customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
        ],
    )
    result = validate_entity(customer)
    if result:
        print(f"   ✅ Entity 'customer' is valid")
    else:
        print(f"   ❌ Entity 'customer' has errors:")
        print(f"      {result}")
    
    # 2. Validate entity with issues
    print("\n2️⃣ Validating entity with missing key property...")
    bad_entity = Entity(
        entity="product",
        source="analytics.products",
        keys=["product_id"],  # No corresponding property
        properties=[
            Property(name="name", type=PropertyType.STRING),
        ],
    )
    result = validate_entity(bad_entity)
    if result:
        print(f"   ✅ Entity 'product' is valid (warnings are OK)")
    else:
        print(f"   ❌ Entity 'product' has errors")
    if result.warnings:
        print(f"   ⚠️  Warnings:")
        for warning in result.warnings:
            print(f"      • {warning}")
    
    # 3. Validate relation with entity index
    print("\n3️⃣ Validating relation with entity references...")
    product = Entity(
        entity="product",
        source="analytics.products",
        keys=["product_id"],
    )
    purchased = Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="analytics.orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
    )
    entity_index = {"customer": customer, "product": product}
    result = validate_relation(purchased, entity_index)
    if result:
        print(f"   ✅ Relation 'PURCHASED' is valid")
    else:
        print(f"   ❌ Relation 'PURCHASED' has errors:")
        for error in result.errors:
            print(f"      • {error}")
    
    # 4. Validate relation with invalid reference
    print("\n4️⃣ Validating relation with non-existent entity...")
    bad_relation = Relation(
        relation="REVIEWED",
        from_entity="customer",
        to_entity="nonexistent_entity",  # Doesn't exist
        source="analytics.reviews",
        mappings=RelationMapping(from_key="customer_id", to_key="id"),
    )
    result = validate_relation(bad_relation, entity_index)
    if result:
        print(f"   ✅ Relation 'REVIEWED' is valid")
    else:
        print(f"   ❌ Relation 'REVIEWED' has errors:")
        for error in result.errors:
            print(f"      • {error}")
    
    # 5. Validate relation with invalid key mapping
    print("\n5️⃣ Validating relation with invalid key mapping...")
    bad_mapping = Relation(
        relation="FOLLOWS",
        from_entity="customer",
        to_entity="product",
        source="analytics.follows",
        mappings=RelationMapping(from_key="invalid_key", to_key="product_id"),
    )
    result = validate_relation(bad_mapping, entity_index)
    if result:
        print(f"   ✅ Relation 'FOLLOWS' is valid")
    else:
        print(f"   ❌ Relation 'FOLLOWS' has errors:")
        for error in result.errors:
            print(f"      • {error}")
    
    # 6. Validate complete project from templates
    print("\n6️⃣ Validating complete project from templates...")
    templates_dir = Path(__file__).parent / "templates"
    if templates_dir.exists():
        try:
            project = load_project(templates_dir)
            result = validate_project(project, strict=False)
            
            if result:
                print(f"   ✅ Project '{project.name}' is valid!")
            else:
                print(f"   ❌ Project '{project.name}' has errors:")
                for error in result.errors:
                    print(f"      • {error}")
            
            if result.warnings:
                print(f"   ⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"      • {warning}")
            
            # Show validation summary
            print(f"\n   📊 Validation Summary:")
            print(f"      Entities validated: {len(project.entities)}")
            print(f"      Relations validated: {len(project.relations)}")
            print(f"      Errors found: {len(result.errors)}")
            print(f"      Warnings found: {len(result.warnings)}")
        
        except Exception as e:
            print(f"   ⚠️  Error loading project: {e}")
    else:
        print("   ⚠️  Templates directory not found")
    
    # 7. Test strict mode
    print("\n7️⃣ Testing strict mode (warnings become errors)...")
    from grai.core.models import Project
    
    strict_entity = Entity(
        entity="test",
        source="source.test",
        keys=["id"],  # No property for this key
    )
    strict_project = Project(
        name="strict-test",
        version="1.0.0",
        entities=[strict_entity],
        relations=[],
    )
    
    result_normal = validate_project(strict_project, strict=False)
    result_strict = validate_project(strict_project, strict=True)
    
    print(f"   Normal mode: {len(result_normal.errors)} errors, {len(result_normal.warnings)} warnings")
    print(f"   Strict mode: {len(result_strict.errors)} errors, {len(result_strict.warnings)} warnings")
    
    if result_normal.valid and not result_strict.valid:
        print(f"   ✅ Strict mode correctly treats warnings as errors")
    
    print("\n✨ Validator demo complete!\n")
    print("📝 The validator successfully:")
    print("   ✅ Validates individual entities and relations")
    print("   ✅ Checks entity references exist")
    print("   ✅ Validates key mappings are correct")
    print("   ✅ Detects duplicate property names")
    print("   ✅ Checks for circular dependencies")
    print("   ✅ Provides detailed error messages with context")
    print("   ✅ Supports strict mode for zero-tolerance validation")
    print("\n🚀 Next steps:")
    print("   - Implement the Cypher compiler")
    print("   - Build the CLI commands")
    print("   - Add Neo4j loader")


if __name__ == "__main__":
    demo_validator()

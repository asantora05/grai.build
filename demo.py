"""
Demo script showing how to use grai.build core models.

Run this to verify the installation and see the models in action.
"""

from grai.core.models import Entity, Project, Property, PropertyType, Relation, RelationMapping


def demo_models():
    """Demonstrate the core models."""

    print("🎯 grai.build Core Models Demo\n")

    # Create a Property
    print("1️⃣ Creating a Property...")
    customer_id_prop = Property(
        name="customer_id",
        type=PropertyType.STRING,
        required=True,
        description="Unique customer identifier",
    )
    print(f"   ✅ Property: {customer_id_prop.name} ({customer_id_prop.type.value})")

    # Create an Entity
    print("\n2️⃣ Creating an Entity...")
    customer = Entity(
        entity="customer",
        source="analytics.customers",
        keys=["customer_id"],
        properties=[
            customer_id_prop,
            Property(name="name", type=PropertyType.STRING),
            Property(name="email", type=PropertyType.STRING),
            Property(name="region", type=PropertyType.STRING),
        ],
        description="Customer entity from analytics database",
    )
    print(f"   ✅ Entity: {customer.entity}")
    print(f"      Source: {customer.source}")
    print(f"      Keys: {customer.keys}")
    print(f"      Properties: {len(customer.properties)}")

    # Create another Entity
    product = Entity(
        entity="product",
        source="analytics.products",
        keys=["product_id"],
        properties=[
            Property(name="product_id", type=PropertyType.STRING, required=True),
            Property(name="name", type=PropertyType.STRING),
            Property(name="price", type=PropertyType.FLOAT),
        ],
    )
    print(f"   ✅ Entity: {product.entity}")

    # Create a Relation
    print("\n3️⃣ Creating a Relation...")
    purchased = Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="analytics.orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[
            Property(name="order_id", type=PropertyType.STRING),
            Property(name="order_date", type=PropertyType.DATETIME),
            Property(name="quantity", type=PropertyType.INTEGER),
        ],
        description="Represents a purchase transaction",
    )
    print(f"   ✅ Relation: {purchased.relation}")
    print(f"      From: {purchased.from_entity} -> To: {purchased.to_entity}")
    print(f"      Mappings: {purchased.mappings.from_key} -> {purchased.mappings.to_key}")

    # Create a Project
    print("\n4️⃣ Creating a Project...")
    project = Project(
        name="ecommerce-graph",
        version="1.0.0",
        entities=[customer, product],
        relations=[purchased],
        config={"neo4j": {"uri": "bolt://localhost:7687"}},
    )
    print(f"   ✅ Project: {project.name} (v{project.version})")
    print(f"      Entities: {len(project.entities)}")
    print(f"      Relations: {len(project.relations)}")

    # Demonstrate lookup methods
    print("\n5️⃣ Using lookup methods...")
    found_customer = project.get_entity("customer")
    print(f"   ✅ Found entity: {found_customer.entity if found_customer else 'None'}")

    found_relation = project.get_relation("PURCHASED")
    print(f"   ✅ Found relation: {found_relation.relation if found_relation else 'None'}")

    # Show property lookup
    name_prop = customer.get_property("name")
    print(f"   ✅ Found property: {name_prop.name if name_prop else 'None'}")

    # Show key properties
    key_props = customer.get_key_properties()
    print(f"   ✅ Key properties: {[p.name for p in key_props]}")

    print("\n✨ Demo complete! The core models are working correctly.\n")
    print("📝 Next steps:")
    print("   - Implement the YAML parser (grai/core/parser/)")
    print("   - Implement the validator (grai/core/validator/)")
    print("   - Implement the Cypher compiler (grai/core/compiler/)")
    print("   - Implement the CLI (grai/cli/)")


if __name__ == "__main__":
    demo_models()

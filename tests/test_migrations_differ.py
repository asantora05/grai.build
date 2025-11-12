"""
Tests for migration system - differ functionality.
"""

from grai.core.migrations.differ import diff_schemas
from grai.core.migrations.models import ChangeType
from grai.core.models import Entity, Property, PropertyType, Relation


def test_diff_no_changes():
    """Test that identical schemas produce no changes."""
    entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
        ],
    )

    changes = diff_schemas(
        old_entities=[entity],
        old_relations=[],
        new_entities=[entity],
        new_relations=[],
    )

    assert not changes.has_changes()
    assert len(changes.entities) == 0
    assert len(changes.relations) == 0


def test_diff_added_entity():
    """Test detecting a new entity."""
    new_entity = Entity(
        entity="product",
        source="products",
        keys=["product_id"],
        properties=[
            Property(name="product_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
        ],
    )

    changes = diff_schemas(
        old_entities=[],
        old_relations=[],
        new_entities=[new_entity],
        new_relations=[],
    )

    assert changes.has_changes()
    assert len(changes.entities) == 1
    assert changes.entities[0].change_type == ChangeType.ADDED
    assert changes.entities[0].name == "product"
    assert len(changes.entities[0].properties_added) == 2


def test_diff_removed_entity():
    """Test detecting removed entity."""
    old_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
        ],
    )

    changes = diff_schemas(
        old_entities=[old_entity],
        old_relations=[],
        new_entities=[],
        new_relations=[],
    )

    assert changes.has_changes()
    assert len(changes.entities) == 1
    assert changes.entities[0].change_type == ChangeType.REMOVED
    assert changes.entities[0].name == "customer"


def test_diff_added_property():
    """Test detecting added property to entity."""
    old_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
        ],
    )

    new_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
            Property(name="email", type=PropertyType.STRING),
        ],
    )

    changes = diff_schemas(
        old_entities=[old_entity],
        old_relations=[],
        new_entities=[new_entity],
        new_relations=[],
    )

    assert changes.has_changes()
    assert len(changes.entities) == 1
    assert changes.entities[0].change_type == ChangeType.MODIFIED
    assert changes.entities[0].name == "customer"
    assert len(changes.entities[0].properties_added) == 1
    assert changes.entities[0].properties_added[0]["name"] == "email"


def test_diff_removed_property():
    """Test detecting removed property from entity."""
    old_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
            Property(name="email", type=PropertyType.STRING),
        ],
    )

    new_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
        ],
    )

    changes = diff_schemas(
        old_entities=[old_entity],
        old_relations=[],
        new_entities=[new_entity],
        new_relations=[],
    )

    assert changes.has_changes()
    assert len(changes.entities) == 1
    assert changes.entities[0].change_type == ChangeType.MODIFIED
    assert len(changes.entities[0].properties_removed) == 1
    assert changes.entities[0].properties_removed[0] == "email"


def test_diff_modified_property_type():
    """Test detecting property type change."""
    old_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="age", type=PropertyType.STRING),
        ],
    )

    new_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="age", type=PropertyType.INTEGER),
        ],
    )

    changes = diff_schemas(
        old_entities=[old_entity],
        old_relations=[],
        new_entities=[new_entity],
        new_relations=[],
    )

    assert changes.has_changes()
    assert len(changes.entities) == 1
    assert changes.entities[0].change_type == ChangeType.MODIFIED
    assert len(changes.entities[0].properties_modified) == 1
    prop_change = changes.entities[0].properties_modified[0]
    assert prop_change.name == "age"
    assert prop_change.old_type == "string"
    assert prop_change.new_type == "integer"


def test_diff_added_relation():
    """Test detecting new relation."""
    from grai.core.models import RelationMapping

    new_relation = Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[
            Property(name="order_id", type=PropertyType.STRING),
        ],
    )

    changes = diff_schemas(
        old_entities=[],
        old_relations=[],
        new_entities=[],
        new_relations=[new_relation],
    )

    assert changes.has_changes()
    assert len(changes.relations) == 1
    assert changes.relations[0].change_type == ChangeType.ADDED
    assert changes.relations[0].name == "PURCHASED"
    assert changes.relations[0].new_from == "customer"
    assert changes.relations[0].new_to == "product"


def test_diff_removed_relation():
    """Test detecting removed relation."""
    from grai.core.models import RelationMapping

    old_relation = Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[],
    )

    changes = diff_schemas(
        old_entities=[],
        old_relations=[old_relation],
        new_entities=[],
        new_relations=[],
    )

    assert changes.has_changes()
    assert len(changes.relations) == 1
    assert changes.relations[0].change_type == ChangeType.REMOVED
    assert changes.relations[0].name == "PURCHASED"


def test_diff_complex_changes():
    """Test multiple changes happening at once."""
    from grai.core.models import RelationMapping

    # Old schema
    old_customer = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
            Property(name="old_field", type=PropertyType.STRING),
        ],
    )

    old_relation = Relation(
        relation="OLD_RELATION",
        from_entity="customer",
        to_entity="product",
        source="old_orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[],
    )

    # New schema
    new_customer = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
            Property(name="email", type=PropertyType.STRING),  # Added
        ],
    )

    new_product = Entity(
        entity="product",
        source="products",
        keys=["product_id"],
        properties=[
            Property(name="product_id", type=PropertyType.STRING),
        ],
    )

    new_relation = Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[
            Property(name="order_date", type=PropertyType.DATETIME),
        ],
    )

    changes = diff_schemas(
        old_entities=[old_customer],
        old_relations=[old_relation],
        new_entities=[new_customer, new_product],
        new_relations=[new_relation],
    )

    assert changes.has_changes()

    # Should have 2 entity changes: 1 modified (customer), 1 added (product)
    assert len(changes.entities) == 2

    # Should have 2 relation changes: 1 removed (OLD_RELATION), 1 added (PURCHASED)
    assert len(changes.relations) == 2

    # Check summary
    summary = changes.summary()
    assert "entities added" in summary
    assert "entities modified" in summary
    assert "relations added" in summary
    assert "relations removed" in summary


def test_diff_keys_changed():
    """Test detecting changed entity keys."""
    old_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
        ],
    )

    new_entity = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id", "email"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
        ],
    )

    changes = diff_schemas(
        old_entities=[old_entity],
        old_relations=[],
        new_entities=[new_entity],
        new_relations=[],
    )

    assert changes.has_changes()
    assert len(changes.entities) == 1
    assert changes.entities[0].keys_changed
    assert changes.entities[0].old_keys == ["customer_id"]
    assert changes.entities[0].new_keys == ["customer_id", "email"]

"""Tests for core Pydantic models."""

import pytest
from pydantic import ValidationError

from grai.core.models import (
    Entity,
    Project,
    Property,
    PropertyType,
    Relation,
    RelationMapping,
)


class TestProperty:
    """Test Property model."""

    def test_valid_property(self):
        """Test creating a valid property."""
        prop = Property(
            name="customer_id",
            type=PropertyType.STRING,
            required=True,
            description="Unique customer identifier",
        )
        assert prop.name == "customer_id"
        assert prop.type == PropertyType.STRING
        assert prop.required is True

    def test_property_name_validation(self):
        """Test that invalid property names are rejected."""
        with pytest.raises(ValidationError):
            Property(name="invalid-name!", type=PropertyType.STRING)

    def test_property_with_default(self):
        """Test property with default value."""
        prop = Property(name="status", type=PropertyType.STRING, default="active")
        assert prop.default == "active"


class TestEntity:
    """Test Entity model."""

    def test_valid_entity(self):
        """Test creating a valid entity."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING, required=True),
                Property(name="name", type=PropertyType.STRING),
                Property(name="region", type=PropertyType.STRING),
            ],
            description="Customer entity",
        )
        assert entity.entity == "customer"
        assert len(entity.properties) == 3
        assert entity.keys == ["customer_id"]

    def test_entity_requires_keys(self):
        """Test that entity must have at least one key."""
        with pytest.raises(ValidationError):
            Entity(entity="customer", source="analytics.customers", keys=[])

    def test_get_property(self):
        """Test getting a property by name."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
            ],
        )
        prop = entity.get_property("name")
        assert prop is not None
        assert prop.name == "name"
        assert entity.get_property("nonexistent") is None

    def test_get_key_properties(self):
        """Test getting key properties."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id", "email"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING),
                Property(name="email", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
            ],
        )
        key_props = entity.get_key_properties()
        assert len(key_props) == 2
        assert all(p.name in ["customer_id", "email"] for p in key_props)


class TestRelation:
    """Test Relation model."""

    def test_valid_relation(self):
        """Test creating a valid relation."""
        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
            properties=[Property(name="order_id", type=PropertyType.STRING)],
        )
        assert relation.relation == "PURCHASED"
        assert relation.from_entity == "customer"
        assert relation.to_entity == "product"

    def test_relation_name_must_be_uppercase(self):
        """Test that relation names must be uppercase."""
        with pytest.raises(ValidationError, match="uppercase"):
            Relation(
                relation="purchased",
                from_entity="customer",
                to_entity="product",
                source="analytics.orders",
                mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
            )

    def test_relation_alias_fields(self):
        """Test that 'from' and 'to' aliases work."""
        relation = Relation(
            relation="PURCHASED",
            **{
                "from": "customer",
                "to": "product",
                "source": "analytics.orders",
                "mappings": RelationMapping(from_key="customer_id", to_key="product_id"),
            },
        )
        assert relation.from_entity == "customer"
        assert relation.to_entity == "product"


class TestProject:
    """Test Project model."""

    def test_valid_project(self):
        """Test creating a valid project."""
        project = Project(
            name="my-graph",
            version="1.0.0",
            entities=[
                Entity(
                    entity="customer",
                    source="analytics.customers",
                    keys=["customer_id"],
                )
            ],
            relations=[
                Relation(
                    relation="PURCHASED",
                    from_entity="customer",
                    to_entity="product",
                    source="analytics.orders",
                    mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
                )
            ],
        )
        assert project.name == "my-graph"
        assert len(project.entities) == 1
        assert len(project.relations) == 1

    def test_get_entity(self):
        """Test getting an entity by name."""
        project = Project(
            name="my-graph",
            entities=[
                Entity(entity="customer", source="analytics.customers", keys=["id"]),
                Entity(entity="product", source="analytics.products", keys=["id"]),
            ],
        )
        entity = project.get_entity("customer")
        assert entity is not None
        assert entity.entity == "customer"
        assert project.get_entity("nonexistent") is None

    def test_get_relation(self):
        """Test getting a relation by name."""
        project = Project(
            name="my-graph",
            relations=[
                Relation(
                    relation="PURCHASED",
                    from_entity="customer",
                    to_entity="product",
                    source="analytics.orders",
                    mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
                )
            ],
        )
        relation = project.get_relation("PURCHASED")
        assert relation is not None
        assert relation.relation == "PURCHASED"
        assert project.get_relation("NONEXISTENT") is None

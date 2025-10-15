"""Tests for the project validator."""

from grai.core.models import Entity, Project, Property, PropertyType, Relation, RelationMapping
from grai.core.validator import (
    ValidationResult,
    validate_entity,
    validate_entity_references,
    validate_key_mappings,
    validate_project,
    validate_relation,
)


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_valid_by_default(self):
        """Test that ValidationResult is valid by default."""
        result = ValidationResult()
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error_makes_invalid(self):
        """Test that adding an error makes result invalid."""
        result = ValidationResult()
        result.add_error("Test error")
        assert result.valid is False
        assert len(result.errors) == 1
        assert "Test error" in result.errors[0]

    def test_add_warning_keeps_valid(self):
        """Test that adding a warning keeps result valid."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_bool_conversion(self):
        """Test that ValidationResult can be used as boolean."""
        result = ValidationResult()
        assert bool(result) is True
        result.add_error("Error")
        assert bool(result) is False

    def test_string_representation(self):
        """Test string representation of ValidationResult."""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_warning("Warning 1")
        output = str(result)
        assert "Error 1" in output
        assert "Warning 1" in output


class TestValidateEntity:
    """Test validating individual entities."""

    def test_validate_valid_entity(self):
        """Test validating a valid entity."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
            ],
        )
        result = validate_entity(entity)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_entity_with_missing_key_property(self):
        """Test entity with key that has no property definition."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="name", type=PropertyType.STRING),
            ],
        )
        result = validate_entity(entity)
        assert result.valid is True  # Warning, not error
        assert len(result.warnings) == 1
        assert "customer_id" in result.warnings[0]

    def test_validate_entity_with_duplicate_properties(self):
        """Test entity with duplicate property names."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="name", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
            ],
        )
        result = validate_entity(entity)
        assert result.valid is False
        assert len(result.errors) == 1
        assert "Duplicate property names" in result.errors[0]

    def test_validate_entity_with_empty_source(self):
        """Test entity with whitespace-only source."""
        entity = Entity(
            entity="customer",
            source="   ",  # Whitespace only
            keys=["customer_id"],
        )
        result = validate_entity(entity)
        assert result.valid is False
        assert any("source" in error.lower() for error in result.errors)


class TestValidateRelation:
    """Test validating individual relations."""

    def test_validate_valid_relation(self):
        """Test validating a valid relation."""
        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )
        result = validate_relation(relation)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_relation_with_entity_index(self):
        """Test relation validation with entity reference checking."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        entity_index = {"customer": customer, "product": product}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )
        result = validate_relation(relation, entity_index)
        assert result.valid is True

    def test_validate_relation_with_invalid_entity_reference(self):
        """Test relation with non-existent entity reference."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        entity_index = {"customer": customer}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="nonexistent",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )
        result = validate_relation(relation, entity_index)
        assert result.valid is False
        assert any("nonexistent" in error for error in result.errors)

    def test_validate_relation_with_invalid_key_mapping(self):
        """Test relation with invalid key mapping."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        entity_index = {"customer": customer, "product": product}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="invalid_key", to_key="product_id"),
        )
        result = validate_relation(relation, entity_index)
        assert result.valid is False
        assert any("invalid_key" in error for error in result.errors)

    def test_validate_relation_with_duplicate_properties(self):
        """Test relation with duplicate property names."""
        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
            properties=[
                Property(name="order_id", type=PropertyType.STRING),
                Property(name="order_id", type=PropertyType.STRING),
            ],
        )
        result = validate_relation(relation)
        assert result.valid is False
        assert "Duplicate property names" in result.errors[0]


class TestValidateEntityReferences:
    """Test entity reference validation."""

    def test_validate_valid_entity_references(self):
        """Test validation with valid entity references."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        entity_index = {"customer": customer, "product": product}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        result = validate_entity_references([relation], entity_index)
        assert result.valid is True

    def test_validate_missing_from_entity(self):
        """Test validation with missing from_entity."""
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        entity_index = {"product": product}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        result = validate_entity_references([relation], entity_index)
        assert result.valid is False
        assert any("customer" in error for error in result.errors)

    def test_validate_missing_to_entity(self):
        """Test validation with missing to_entity."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        entity_index = {"customer": customer}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        result = validate_entity_references([relation], entity_index)
        assert result.valid is False
        assert any("product" in error for error in result.errors)


class TestValidateKeyMappings:
    """Test key mapping validation."""

    def test_validate_valid_key_mappings(self):
        """Test validation with valid key mappings."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        entity_index = {"customer": customer, "product": product}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        result = validate_key_mappings([relation], entity_index)
        assert result.valid is True

    def test_validate_invalid_from_key(self):
        """Test validation with invalid from_key."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        entity_index = {"customer": customer, "product": product}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="invalid_key", to_key="product_id"),
        )

        result = validate_key_mappings([relation], entity_index)
        assert result.valid is False
        assert any("invalid_key" in error for error in result.errors)

    def test_validate_invalid_to_key(self):
        """Test validation with invalid to_key."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        entity_index = {"customer": customer, "product": product}

        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="invalid_key"),
        )

        result = validate_key_mappings([relation], entity_index)
        assert result.valid is False
        assert any("invalid_key" in error for error in result.errors)


class TestValidateProject:
    """Test complete project validation."""

    def test_validate_valid_project(self):
        """Test validation of a valid project."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
            ],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
            properties=[
                Property(name="product_id", type=PropertyType.STRING),
            ],
        )
        purchased = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        project = Project(
            name="test-project",
            version="1.0.0",
            entities=[customer, product],
            relations=[purchased],
        )

        result = validate_project(project, strict=False)
        assert result.valid is True

    def test_validate_project_with_missing_entity(self):
        """Test validation with missing entity reference."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        purchased = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",  # product doesn't exist
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        project = Project(
            name="test-project",
            version="1.0.0",
            entities=[customer],
            relations=[purchased],
        )

        result = validate_project(project)
        assert result.valid is False
        assert any("product" in error for error in result.errors)

    def test_validate_project_with_duplicate_entity_names(self):
        """Test validation with duplicate entity names."""
        customer1 = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        customer2 = Entity(
            entity="customer",
            source="analytics.customers_v2",
            keys=["customer_id"],
        )

        project = Project(
            name="test-project",
            version="1.0.0",
            entities=[customer1, customer2],
            relations=[],
        )

        result = validate_project(project)
        assert result.valid is False
        assert any("Duplicate entity names" in error for error in result.errors)

    def test_validate_project_with_duplicate_relation_names(self):
        """Test validation with duplicate relation names."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
        )
        purchased1 = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )
        purchased2 = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders_v2",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        project = Project(
            name="test-project",
            version="1.0.0",
            entities=[customer, product],
            relations=[purchased1, purchased2],
        )

        result = validate_project(project)
        assert result.valid is False
        assert any("Duplicate relation names" in error for error in result.errors)

    def test_validate_project_strict_mode(self):
        """Test validation in strict mode treats warnings as errors."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],  # No corresponding property
        )

        project = Project(
            name="test-project",
            version="1.0.0",
            entities=[customer],
            relations=[],
        )

        result = validate_project(project, strict=True)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_empty_project(self):
        """Test validation of empty project."""
        project = Project(
            name="empty-project",
            version="1.0.0",
            entities=[],
            relations=[],
        )

        result = validate_project(project)
        assert result.valid is True

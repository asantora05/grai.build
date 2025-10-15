"""Tests for the Cypher compiler."""

import pytest

from grai.core.compiler import (
    CompilerError,
    compile_and_write,
    compile_entity,
    compile_project,
    compile_relation,
    compile_schema_only,
    generate_load_csv_statements,
    write_cypher_file,
)
from grai.core.models import Entity, Project, Property, PropertyType, Relation, RelationMapping


class TestCompileEntity:
    """Test compiling entities to Cypher."""

    def test_compile_simple_entity(self):
        """Test compiling a simple entity with one key."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
            ],
        )

        cypher = compile_entity(entity)

        assert "MERGE (n:customer" in cypher
        assert "customer_id: row.customer_id" in cypher
        assert "SET n.name = row.name" in cypher
        assert "// Create customer nodes" in cypher

    def test_compile_entity_with_multiple_keys(self):
        """Test compiling entity with composite key."""
        entity = Entity(
            entity="user",
            source="analytics.users",
            keys=["user_id", "tenant_id"],
            properties=[
                Property(name="user_id", type=PropertyType.STRING),
                Property(name="tenant_id", type=PropertyType.STRING),
                Property(name="email", type=PropertyType.STRING),
            ],
        )

        cypher = compile_entity(entity)

        assert "user_id: row.user_id" in cypher
        assert "tenant_id: row.tenant_id" in cypher
        assert "SET n.email = row.email" in cypher

    def test_compile_entity_key_only(self):
        """Test compiling entity with only key properties."""
        entity = Entity(
            entity="tag",
            source="analytics.tags",
            keys=["tag_id"],
            properties=[
                Property(name="tag_id", type=PropertyType.STRING),
            ],
        )

        cypher = compile_entity(entity)

        assert "MERGE (n:tag {tag_id: row.tag_id});" in cypher
        assert "SET" not in cypher

    def test_compile_entity_with_many_properties(self):
        """Test compiling entity with many properties."""
        entity = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
            properties=[
                Property(name="product_id", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
                Property(name="price", type=PropertyType.FLOAT),
                Property(name="category", type=PropertyType.STRING),
            ],
        )

        cypher = compile_entity(entity)

        assert "SET n.name = row.name" in cypher
        assert "n.price = row.price" in cypher
        assert "n.category = row.category" in cypher


class TestCompileRelation:
    """Test compiling relations to Cypher."""

    def test_compile_simple_relation(self):
        """Test compiling a simple relation."""
        relation = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        )

        cypher = compile_relation(relation)

        assert "MATCH (from:customer {customer_id: row.customer_id})" in cypher
        assert "MATCH (to:product {product_id: row.product_id})" in cypher
        assert "MERGE (from)-[r:PURCHASED]->(to)" in cypher
        assert "// Create PURCHASED relationships" in cypher

    def test_compile_relation_with_properties(self):
        """Test compiling relation with properties."""
        relation = Relation(
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
        )

        cypher = compile_relation(relation)

        assert "SET r.order_id = row.order_id" in cypher
        assert "r.order_date = row.order_date" in cypher
        assert "r.quantity = row.quantity" in cypher

    def test_compile_relation_different_key_names(self):
        """Test relation with different key names."""
        relation = Relation(
            relation="FOLLOWS",
            from_entity="user",
            to_entity="user",
            source="analytics.follows",
            mappings=RelationMapping(from_key="follower_id", to_key="followee_id"),
        )

        cypher = compile_relation(relation)

        assert "follower_id: row.follower_id" in cypher
        assert "followee_id: row.followee_id" in cypher


class TestCompileProject:
    """Test compiling complete projects."""

    def test_compile_project_with_entities_and_relations(self):
        """Test compiling a complete project."""
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
                Property(name="name", type=PropertyType.STRING),
            ],
        )
        purchased = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
            properties=[
                Property(name="order_id", type=PropertyType.STRING),
            ],
        )

        project = Project(
            name="test-project",
            version="1.0.0",
            entities=[customer, product],
            relations=[purchased],
        )

        cypher = compile_project(project)

        # Check header
        assert "test-project" in cypher
        assert "1.0.0" in cypher

        # Check constraints
        assert "CREATE CONSTRAINT constraint_customer_customer_id" in cypher
        assert "CREATE CONSTRAINT constraint_product_product_id" in cypher

        # Check entities
        assert "// Create customer nodes" in cypher
        assert "// Create product nodes" in cypher

        # Check relations
        assert "// Create PURCHASED relationships" in cypher

    def test_compile_project_without_header(self):
        """Test compiling without header."""
        entity = Entity(
            entity="test",
            source="test.source",
            keys=["id"],
            properties=[Property(name="id", type=PropertyType.STRING)],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[entity],
            relations=[],
        )

        cypher = compile_project(project, include_header=False)

        assert "Generated Cypher script" not in cypher
        assert "CREATE CONSTRAINT" in cypher

    def test_compile_project_without_constraints(self):
        """Test compiling without constraints."""
        entity = Entity(
            entity="test",
            source="test.source",
            keys=["id"],
            properties=[Property(name="id", type=PropertyType.STRING)],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[entity],
            relations=[],
        )

        cypher = compile_project(project, include_constraints=False)

        assert "CREATE CONSTRAINT" not in cypher
        assert "MERGE" in cypher

    def test_compile_empty_project(self):
        """Test compiling an empty project."""
        project = Project(
            name="empty",
            version="1.0.0",
            entities=[],
            relations=[],
        )

        cypher = compile_project(project)

        assert "empty" in cypher
        assert "Generated by grai.build" in cypher


class TestWriteCypherFile:
    """Test writing Cypher to files."""

    def test_write_cypher_file(self, tmp_path):
        """Test writing Cypher to a file."""
        cypher = "MERGE (n:test {id: 'test'});"
        output_path = tmp_path / "output.cypher"

        result_path = write_cypher_file(cypher, output_path)

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.read_text() == cypher

    def test_write_cypher_file_creates_dirs(self, tmp_path):
        """Test that parent directories are created."""
        cypher = "MERGE (n:test);"
        output_path = tmp_path / "subdir" / "nested" / "output.cypher"

        result_path = write_cypher_file(cypher, output_path, create_dirs=True)

        assert result_path.exists()
        assert output_path.read_text() == cypher

    def test_write_cypher_file_error_handling(self):
        """Test error handling when writing fails."""
        cypher = "MERGE (n:test);"
        output_path = "/invalid/path/that/does/not/exist/output.cypher"

        with pytest.raises(CompilerError, match="Failed to write"):
            write_cypher_file(cypher, output_path, create_dirs=False)


class TestCompileAndWrite:
    """Test the compile_and_write function."""

    def test_compile_and_write(self, tmp_path):
        """Test compiling and writing in one step."""
        entity = Entity(
            entity="test",
            source="test.source",
            keys=["id"],
            properties=[Property(name="id", type=PropertyType.STRING)],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[entity],
            relations=[],
        )

        output_dir = tmp_path / "target" / "neo4j"
        result_path = compile_and_write(project, output_dir)

        assert result_path.exists()
        content = result_path.read_text()
        assert "test" in content
        assert "MERGE" in content

    def test_compile_and_write_custom_filename(self, tmp_path):
        """Test with custom filename."""
        entity = Entity(
            entity="test",
            source="test.source",
            keys=["id"],
            properties=[Property(name="id", type=PropertyType.STRING)],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[entity],
            relations=[],
        )

        result_path = compile_and_write(
            project,
            output_dir=tmp_path,
            filename="custom.cypher",
        )

        assert result_path.name == "custom.cypher"
        assert result_path.exists()


class TestGenerateLoadCSVStatements:
    """Test generating LOAD CSV statements."""

    def test_generate_load_csv_for_entities(self):
        """Test generating LOAD CSV for entities."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
            ],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[entity],
            relations=[],
        )

        statements = generate_load_csv_statements(project)

        assert "customer" in statements
        csv_stmt = statements["customer"]
        assert "LOAD CSV WITH HEADERS" in csv_stmt
        assert "analytics_customers.csv" in csv_stmt
        assert "MERGE (n:customer" in csv_stmt
        assert "SET n.name = row.name" in csv_stmt

    def test_generate_load_csv_for_relations(self):
        """Test generating LOAD CSV for relations."""
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
        purchased = Relation(
            relation="PURCHASED",
            from_entity="customer",
            to_entity="product",
            source="analytics.orders",
            mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
            properties=[Property(name="order_id", type=PropertyType.STRING)],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[customer, product],
            relations=[purchased],
        )

        statements = generate_load_csv_statements(project)

        assert "PURCHASED" in statements
        csv_stmt = statements["PURCHASED"]
        assert "LOAD CSV WITH HEADERS" in csv_stmt
        assert "analytics_orders.csv" in csv_stmt
        assert "MATCH (from:customer" in csv_stmt
        assert "MATCH (to:product" in csv_stmt
        assert "MERGE (from)-[r:PURCHASED]->(to)" in csv_stmt
        assert "SET r.order_id = row.order_id" in csv_stmt


class TestCompileSchemaOnly:
    """Test compiling schema definitions only."""

    def test_compile_schema_only(self):
        """Test generating only schema (constraints and indexes)."""
        entity = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[
                Property(name="customer_id", type=PropertyType.STRING),
                Property(name="name", type=PropertyType.STRING),
                Property(name="email", type=PropertyType.STRING),
            ],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[entity],
            relations=[],
        )

        schema = compile_schema_only(project)

        # Check constraints
        assert "CREATE CONSTRAINT constraint_customer_customer_id" in schema
        assert "REQUIRE n.customer_id IS UNIQUE" in schema

        # Check indexes
        assert "CREATE INDEX index_customer_name" in schema
        assert "CREATE INDEX index_customer_email" in schema

        # Should not include data loading
        assert "MERGE" not in schema

    def test_compile_schema_with_multiple_entities(self):
        """Test schema with multiple entities."""
        customer = Entity(
            entity="customer",
            source="analytics.customers",
            keys=["customer_id"],
            properties=[Property(name="customer_id", type=PropertyType.STRING)],
        )
        product = Entity(
            entity="product",
            source="analytics.products",
            keys=["product_id"],
            properties=[Property(name="product_id", type=PropertyType.STRING)],
        )

        project = Project(
            name="test",
            version="1.0.0",
            entities=[customer, product],
            relations=[],
        )

        schema = compile_schema_only(project)

        assert "constraint_customer_customer_id" in schema
        assert "constraint_product_product_id" in schema

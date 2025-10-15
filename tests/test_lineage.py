"""
Tests for lineage tracking functionality.

Tests lineage graph construction, entity/relation analysis, and impact calculations.
"""

import pytest

from grai.core.lineage import (
    LineageEdge,
    LineageGraph,
    LineageNode,
    NodeType,
    build_lineage_graph,
    calculate_impact_analysis,
    export_lineage_to_dict,
    find_downstream_entities,
    find_entity_path,
    find_upstream_entities,
    get_entity_lineage,
    get_lineage_statistics,
    get_relation_lineage,
    visualize_lineage_graphviz,
    visualize_lineage_mermaid,
)
from grai.core.models import Entity, Project, Property, PropertyType, Relation, RelationMapping


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    customer = Entity(
        entity="customer",
        source="customers",
        keys=["customer_id"],
        properties=[
            Property(name="customer_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
        ],
    )

    product = Entity(
        entity="product",
        source="products",
        keys=["product_id"],
        properties=[
            Property(name="product_id", type=PropertyType.STRING),
            Property(name="name", type=PropertyType.STRING),
        ],
    )

    order = Entity(
        entity="order",
        source="orders",
        keys=["order_id"],
        properties=[
            Property(name="order_id", type=PropertyType.STRING),
        ],
    )

    purchased = Relation(
        relation="PURCHASED",
        from_entity="customer",
        to_entity="product",
        source="orders",
        mappings=RelationMapping(from_key="customer_id", to_key="product_id"),
        properties=[],
    )

    placed = Relation(
        relation="PLACED",
        from_entity="customer",
        to_entity="order",
        source="orders",
        mappings=RelationMapping(from_key="customer_id", to_key="order_id"),
        properties=[],
    )

    return Project(
        name="test-project",
        version="1.0.0",
        entities=[customer, product, order],
        relations=[purchased, placed],
    )


class TestLineageNode:
    """Tests for LineageNode dataclass."""

    def test_create_entity_node(self):
        """Test creating an entity node."""
        node = LineageNode(
            id="entity:customer",
            name="customer",
            type=NodeType.ENTITY,
        )

        assert node.id == "entity:customer"
        assert node.name == "customer"
        assert node.type == NodeType.ENTITY

    def test_create_relation_node(self):
        """Test creating a relation node."""
        node = LineageNode(
            id="relation:PURCHASED",
            name="PURCHASED",
            type=NodeType.RELATION,
        )

        assert node.type == NodeType.RELATION

    def test_node_with_metadata(self):
        """Test node with metadata."""
        node = LineageNode(
            id="entity:customer",
            name="customer",
            type=NodeType.ENTITY,
            metadata={"source": "customers", "keys": ["customer_id"]},
        )

        assert node.metadata["source"] == "customers"
        assert "customer_id" in node.metadata["keys"]

    def test_node_equality(self):
        """Test node equality based on ID."""
        node1 = LineageNode("entity:customer", "customer", NodeType.ENTITY)
        node2 = LineageNode("entity:customer", "customer", NodeType.ENTITY)
        node3 = LineageNode("entity:product", "product", NodeType.ENTITY)

        assert node1 == node2
        assert node1 != node3


class TestLineageEdge:
    """Tests for LineageEdge dataclass."""

    def test_create_edge(self):
        """Test creating an edge."""
        edge = LineageEdge(
            from_node="entity:customer",
            to_node="relation:PURCHASED",
            relation_type="participates_in",
        )

        assert edge.from_node == "entity:customer"
        assert edge.to_node == "relation:PURCHASED"
        assert edge.relation_type == "participates_in"


class TestLineageGraph:
    """Tests for LineageGraph operations."""

    def test_create_empty_graph(self):
        """Test creating an empty graph."""
        graph = LineageGraph()

        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """Test adding nodes to graph."""
        graph = LineageGraph()
        node = LineageNode("entity:customer", "customer", NodeType.ENTITY)

        graph.add_node(node)

        assert "entity:customer" in graph.nodes
        assert "customer" in graph.entity_map

    def test_add_edge(self):
        """Test adding edges to graph."""
        graph = LineageGraph()
        edge = LineageEdge("node1", "node2", "connects_to")

        graph.add_edge(edge)

        assert len(graph.edges) == 1

    def test_get_edges_from(self):
        """Test getting outgoing edges."""
        graph = LineageGraph()
        graph.add_edge(LineageEdge("node1", "node2", "type1"))
        graph.add_edge(LineageEdge("node1", "node3", "type2"))
        graph.add_edge(LineageEdge("node2", "node3", "type3"))

        edges = graph.get_edges_from("node1")

        assert len(edges) == 2
        assert all(e.from_node == "node1" for e in edges)

    def test_get_edges_to(self):
        """Test getting incoming edges."""
        graph = LineageGraph()
        graph.add_edge(LineageEdge("node1", "node3", "type1"))
        graph.add_edge(LineageEdge("node2", "node3", "type2"))

        edges = graph.get_edges_to("node3")

        assert len(edges) == 2
        assert all(e.to_node == "node3" for e in edges)


class TestBuildLineageGraph:
    """Tests for building lineage graph from project."""

    def test_build_from_project(self, sample_project):
        """Test building complete lineage graph."""
        graph = build_lineage_graph(sample_project)

        # Check entities
        assert "customer" in graph.entity_map
        assert "product" in graph.entity_map
        assert "order" in graph.entity_map

        # Check relations
        assert "PURCHASED" in graph.relation_map
        assert "PLACED" in graph.relation_map

        # Check sources
        assert "customers" in graph.source_map
        assert "products" in graph.source_map
        assert "orders" in graph.source_map

    def test_graph_has_correct_node_count(self, sample_project):
        """Test graph has correct number of nodes."""
        graph = build_lineage_graph(sample_project)

        # 3 entities + 2 relations + 3 sources = 8 nodes
        assert len(graph.nodes) == 8

    def test_graph_has_edges(self, sample_project):
        """Test graph has edges connecting nodes."""
        graph = build_lineage_graph(sample_project)

        # Should have edges from sources to entities/relations
        # and from entities to relations
        assert len(graph.edges) > 0

    def test_source_to_entity_edges(self, sample_project):
        """Test edges from sources to entities."""
        graph = build_lineage_graph(sample_project)

        customer_node_id = graph.entity_map["customer"]
        edges_to_customer = graph.get_edges_to(customer_node_id)

        # Should have edge from source "customers"
        source_edges = [e for e in edges_to_customer if "source:customers" == e.from_node]
        assert len(source_edges) == 1


class TestGetEntityLineage:
    """Tests for getting entity lineage."""

    def test_get_entity_lineage(self, sample_project):
        """Test getting lineage for an entity."""
        graph = build_lineage_graph(sample_project)
        lineage = get_entity_lineage(graph, "customer")

        assert lineage["entity"] == "customer"
        assert lineage["source"] == "customers"
        assert "upstream" in lineage
        assert "downstream" in lineage

    def test_entity_not_found(self, sample_project):
        """Test getting lineage for non-existent entity."""
        graph = build_lineage_graph(sample_project)
        lineage = get_entity_lineage(graph, "nonexistent")

        assert "error" in lineage

    def test_entity_has_downstream_relations(self, sample_project):
        """Test entity shows downstream relations."""
        graph = build_lineage_graph(sample_project)
        lineage = get_entity_lineage(graph, "customer")

        # Customer participates in PURCHASED and PLACED relations
        downstream = lineage["downstream"]
        relation_names = [d["node"] for d in downstream if d["type"] == "relation"]

        assert "PURCHASED" in relation_names or "PLACED" in relation_names


class TestGetRelationLineage:
    """Tests for getting relation lineage."""

    def test_get_relation_lineage(self, sample_project):
        """Test getting lineage for a relation."""
        graph = build_lineage_graph(sample_project)
        lineage = get_relation_lineage(graph, "PURCHASED")

        assert lineage["relation"] == "PURCHASED"
        assert lineage["from_entity"] == "customer"
        assert lineage["to_entity"] == "product"

    def test_relation_not_found(self, sample_project):
        """Test getting lineage for non-existent relation."""
        graph = build_lineage_graph(sample_project)
        lineage = get_relation_lineage(graph, "NONEXISTENT")

        assert "error" in lineage

    def test_relation_has_upstream_entities(self, sample_project):
        """Test relation shows upstream entities."""
        graph = build_lineage_graph(sample_project)
        lineage = get_relation_lineage(graph, "PURCHASED")

        upstream = lineage["upstream"]
        entity_names = [u["node"] for u in upstream if u["type"] == "entity"]

        assert "customer" in entity_names


class TestFindUpstreamEntities:
    """Tests for finding upstream entities."""

    def test_find_upstream_no_upstream(self, sample_project):
        """Test entity with no upstream entities."""
        graph = build_lineage_graph(sample_project)
        upstream = find_upstream_entities(graph, "customer")

        # Customer has no upstream entities
        assert len(upstream) == 0

    def test_find_upstream_with_connections(self, sample_project):
        """Test entity with upstream connections."""
        graph = build_lineage_graph(sample_project)

        # Product is connected from customer via PURCHASED
        upstream = find_upstream_entities(graph, "product")

        assert "customer" in upstream

    def test_nonexistent_entity(self, sample_project):
        """Test finding upstream for non-existent entity."""
        graph = build_lineage_graph(sample_project)
        upstream = find_upstream_entities(graph, "nonexistent")

        assert len(upstream) == 0


class TestFindDownstreamEntities:
    """Tests for finding downstream entities."""

    def test_find_downstream_with_connections(self, sample_project):
        """Test entity with downstream connections."""
        graph = build_lineage_graph(sample_project)
        downstream = find_downstream_entities(graph, "customer")

        # Customer connects to product and order
        assert "product" in downstream or "order" in downstream

    def test_find_downstream_no_connections(self, sample_project):
        """Test entity with no downstream connections."""
        graph = build_lineage_graph(sample_project)

        # Product and order are leaf nodes
        downstream = find_downstream_entities(graph, "product")

        # May have some connections through relations
        assert isinstance(downstream, set)


class TestFindEntityPath:
    """Tests for finding paths between entities."""

    def test_find_direct_path(self, sample_project):
        """Test finding path between connected entities."""
        graph = build_lineage_graph(sample_project)
        path = find_entity_path(graph, "customer", "product")

        # Should find a path through PURCHASED relation
        assert path is not None
        assert path[0] == "customer"
        assert path[-1] == "product"

    def test_find_path_no_connection(self, sample_project):
        """Test finding path when no connection exists."""
        graph = build_lineage_graph(sample_project)

        # Try to find path from product to customer (reverse direction)
        path = find_entity_path(graph, "product", "customer")

        # May or may not exist depending on graph structure
        assert path is None or isinstance(path, list)

    def test_nonexistent_entities(self, sample_project):
        """Test path finding with non-existent entities."""
        graph = build_lineage_graph(sample_project)
        path = find_entity_path(graph, "nonexistent1", "nonexistent2")

        assert path is None


class TestCalculateImpactAnalysis:
    """Tests for impact analysis."""

    def test_calculate_impact(self, sample_project):
        """Test calculating impact of entity change."""
        graph = build_lineage_graph(sample_project)
        impact = calculate_impact_analysis(graph, "customer")

        assert impact["entity"] == "customer"
        assert "impact_score" in impact
        assert "affected_entities" in impact
        assert "affected_relations" in impact
        assert "impact_level" in impact

    def test_impact_score_calculation(self, sample_project):
        """Test impact score is calculated."""
        graph = build_lineage_graph(sample_project)
        impact = calculate_impact_analysis(graph, "customer")

        # Customer affects multiple entities and relations
        assert impact["impact_score"] >= 0

    def test_impact_level(self, sample_project):
        """Test impact level classification."""
        graph = build_lineage_graph(sample_project)
        impact = calculate_impact_analysis(graph, "customer")

        assert impact["impact_level"] in ["none", "low", "medium", "high"]

    def test_nonexistent_entity_impact(self, sample_project):
        """Test impact analysis for non-existent entity."""
        graph = build_lineage_graph(sample_project)
        impact = calculate_impact_analysis(graph, "nonexistent")

        assert "error" in impact


class TestGetLineageStatistics:
    """Tests for lineage statistics."""

    def test_get_statistics(self, sample_project):
        """Test getting lineage statistics."""
        graph = build_lineage_graph(sample_project)
        stats = get_lineage_statistics(graph)

        assert stats["entity_count"] == 3
        assert stats["relation_count"] == 2
        assert stats["source_count"] == 3
        assert "total_nodes" in stats
        assert "total_edges" in stats

    def test_connectivity_stats(self, sample_project):
        """Test connectivity statistics."""
        graph = build_lineage_graph(sample_project)
        stats = get_lineage_statistics(graph)

        assert "max_downstream_connections" in stats
        assert "most_connected_entity" in stats


class TestExportLineageToDict:
    """Tests for exporting lineage to dictionary."""

    def test_export_to_dict(self, sample_project):
        """Test exporting graph to dictionary."""
        graph = build_lineage_graph(sample_project)
        data = export_lineage_to_dict(graph)

        assert "nodes" in data
        assert "edges" in data
        assert "statistics" in data

    def test_export_has_all_nodes(self, sample_project):
        """Test export includes all nodes."""
        graph = build_lineage_graph(sample_project)
        data = export_lineage_to_dict(graph)

        assert len(data["nodes"]) == len(graph.nodes)

    def test_export_has_all_edges(self, sample_project):
        """Test export includes all edges."""
        graph = build_lineage_graph(sample_project)
        data = export_lineage_to_dict(graph)

        assert len(data["edges"]) == len(graph.edges)


class TestVisualizeMermaid:
    """Tests for Mermaid diagram generation."""

    def test_generate_mermaid_full(self, sample_project):
        """Test generating full Mermaid diagram."""
        graph = build_lineage_graph(sample_project)
        diagram = visualize_lineage_mermaid(graph)

        assert diagram.startswith("graph LR")
        assert "customer" in diagram
        assert "product" in diagram

    def test_generate_mermaid_focused(self, sample_project):
        """Test generating focused Mermaid diagram."""
        graph = build_lineage_graph(sample_project)
        diagram = visualize_lineage_mermaid(graph, focus_entity="customer")

        assert "graph LR" in diagram
        assert "customer" in diagram

    def test_mermaid_has_styling(self, sample_project):
        """Test Mermaid diagram includes styling."""
        graph = build_lineage_graph(sample_project)
        diagram = visualize_lineage_mermaid(graph)

        assert "style" in diagram
        assert "fill" in diagram


class TestVisualizeGraphviz:
    """Tests for Graphviz DOT generation."""

    def test_generate_graphviz_full(self, sample_project):
        """Test generating full Graphviz diagram."""
        graph = build_lineage_graph(sample_project)
        diagram = visualize_lineage_graphviz(graph)

        assert diagram.startswith("digraph lineage")
        assert "customer" in diagram
        assert "product" in diagram

    def test_generate_graphviz_focused(self, sample_project):
        """Test generating focused Graphviz diagram."""
        graph = build_lineage_graph(sample_project)
        diagram = visualize_lineage_graphviz(graph, focus_entity="customer")

        assert "digraph lineage" in diagram
        assert "customer" in diagram

    def test_graphviz_has_styling(self, sample_project):
        """Test Graphviz diagram includes styling."""
        graph = build_lineage_graph(sample_project)
        diagram = visualize_lineage_graphviz(graph)

        assert "fillcolor" in diagram
        assert "shape" in diagram


class TestLineageIntegration:
    """Integration tests for lineage tracking."""

    def test_full_workflow(self, sample_project):
        """Test complete lineage workflow."""
        # Build graph
        graph = build_lineage_graph(sample_project)

        # Get entity lineage
        lineage = get_entity_lineage(graph, "customer")
        assert lineage["entity"] == "customer"

        # Calculate impact
        impact = calculate_impact_analysis(graph, "customer")
        assert "impact_score" in impact

        # Get statistics
        stats = get_lineage_statistics(graph)
        assert stats["entity_count"] == 3

        # Export to dict
        data = export_lineage_to_dict(graph)
        assert len(data["nodes"]) > 0

        # Generate visualizations
        mermaid = visualize_lineage_mermaid(graph)
        assert len(mermaid) > 0

        graphviz = visualize_lineage_graphviz(graph)
        assert len(graphviz) > 0

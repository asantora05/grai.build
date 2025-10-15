"""
Tests for the visualization module.
"""

import pytest

from grai.core.models import Entity, Project, Property, PropertyType, Relation, RelationMapping
from grai.core.visualizer import (
    generate_cytoscape_visualization,
    generate_d3_visualization,
)


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    return Project(
        name="test-graph",
        version="1.0.0",
        entities=[
            Entity(
                entity="customer",
                source="db.customers",
                keys=["customer_id"],
                properties=[
                    Property(name="customer_id", type=PropertyType.STRING),
                    Property(name="name", type=PropertyType.STRING),
                ],
            ),
            Entity(
                entity="product",
                source="db.products",
                keys=["product_id"],
                properties=[
                    Property(name="product_id", type=PropertyType.STRING),
                    Property(name="title", type=PropertyType.STRING),
                ],
            ),
        ],
        relations=[
            Relation(
                relation="PURCHASED",
                from_entity="customer",
                to_entity="product",
                source="db.orders",
                mappings=RelationMapping(
                    from_key="customer_id",
                    to_key="product_id",
                ),
                properties=[
                    Property(name="order_id", type=PropertyType.STRING),
                ],
            ),
        ],
    )


class TestGenerateD3Visualization:
    """Tests for D3.js visualization generation."""

    def test_generate_d3_basic(self, sample_project, tmp_path):
        """Test generating basic D3 visualization."""
        output_path = tmp_path / "graph.html"

        generate_d3_visualization(sample_project, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 1000  # Should be substantial file

    def test_d3_contains_html_structure(self, sample_project, tmp_path):
        """Test D3 visualization contains proper HTML structure."""
        output_path = tmp_path / "graph.html"

        generate_d3_visualization(sample_project, output_path)

        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content
        assert "d3js.org" in content

    def test_d3_contains_project_data(self, sample_project, tmp_path):
        """Test D3 visualization contains project data."""
        output_path = tmp_path / "graph.html"

        generate_d3_visualization(sample_project, output_path)

        content = output_path.read_text()
        assert "customer" in content
        assert "product" in content
        assert "PURCHASED" in content

    def test_d3_with_custom_title(self, sample_project, tmp_path):
        """Test D3 visualization with custom title."""
        output_path = tmp_path / "graph.html"

        generate_d3_visualization(sample_project, output_path, title="My Graph")

        content = output_path.read_text()
        assert "My Graph" in content

    def test_d3_with_custom_dimensions(self, sample_project, tmp_path):
        """Test D3 visualization with custom dimensions."""
        output_path = tmp_path / "graph.html"

        generate_d3_visualization(sample_project, output_path, width=800, height=600)

        content = output_path.read_text()
        assert 'width="800"' in content or "800" in content
        assert 'height="600"' in content or "600" in content

    def test_d3_creates_parent_directories(self, sample_project, tmp_path):
        """Test D3 visualization creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "graph.html"

        generate_d3_visualization(sample_project, output_path)

        assert output_path.exists()

    def test_d3_contains_statistics(self, sample_project, tmp_path):
        """Test D3 visualization includes project statistics."""
        output_path = tmp_path / "graph.html"

        generate_d3_visualization(sample_project, output_path)

        content = output_path.read_text()
        assert "nodes" in content
        assert "edges" in content
        assert "entities" in content


class TestGenerateCytoscapeVisualization:
    """Tests for Cytoscape.js visualization generation."""

    def test_generate_cytoscape_basic(self, sample_project, tmp_path):
        """Test generating basic Cytoscape visualization."""
        output_path = tmp_path / "graph.html"

        generate_cytoscape_visualization(sample_project, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 1000

    def test_cytoscape_contains_html_structure(self, sample_project, tmp_path):
        """Test Cytoscape visualization contains proper HTML structure."""
        output_path = tmp_path / "graph.html"

        generate_cytoscape_visualization(sample_project, output_path)

        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content
        assert "cytoscape" in content.lower()

    def test_cytoscape_contains_project_data(self, sample_project, tmp_path):
        """Test Cytoscape visualization contains project data."""
        output_path = tmp_path / "graph.html"

        generate_cytoscape_visualization(sample_project, output_path)

        content = output_path.read_text()
        assert "customer" in content
        assert "product" in content
        assert "PURCHASED" in content

    def test_cytoscape_with_custom_title(self, sample_project, tmp_path):
        """Test Cytoscape visualization with custom title."""
        output_path = tmp_path / "graph.html"

        generate_cytoscape_visualization(sample_project, output_path, title="My Graph")

        content = output_path.read_text()
        assert "My Graph" in content

    def test_cytoscape_with_custom_dimensions(self, sample_project, tmp_path):
        """Test Cytoscape visualization with custom dimensions."""
        output_path = tmp_path / "graph.html"

        generate_cytoscape_visualization(sample_project, output_path, width=800, height=600)

        content = output_path.read_text()
        assert "800" in content
        assert "600" in content

    def test_cytoscape_creates_parent_directories(self, sample_project, tmp_path):
        """Test Cytoscape visualization creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "graph.html"

        generate_cytoscape_visualization(sample_project, output_path)

        assert output_path.exists()

    def test_cytoscape_contains_statistics(self, sample_project, tmp_path):
        """Test Cytoscape visualization includes project statistics."""
        output_path = tmp_path / "graph.html"

        generate_cytoscape_visualization(sample_project, output_path)

        content = output_path.read_text()
        assert "nodes" in content
        assert "edges" in content
        assert "entities" in content


class TestVisualizationIntegration:
    """Integration tests for visualization module."""

    def test_both_formats_work(self, sample_project, tmp_path):
        """Test both D3 and Cytoscape formats work."""
        d3_path = tmp_path / "d3.html"
        cytoscape_path = tmp_path / "cytoscape.html"

        generate_d3_visualization(sample_project, d3_path)
        generate_cytoscape_visualization(sample_project, cytoscape_path)

        assert d3_path.exists()
        assert cytoscape_path.exists()
        assert d3_path.stat().st_size > 1000
        assert cytoscape_path.stat().st_size > 1000

    def test_visualization_with_complex_project(self, tmp_path):
        """Test visualization with more complex project."""
        project = Project(
            name="complex-graph",
            version="1.0.0",
            entities=[
                Entity(
                    entity=f"entity{i}",
                    source=f"db.table{i}",
                    keys=["id"],
                    properties=[Property(name="id", type=PropertyType.STRING)],
                )
                for i in range(5)
            ],
            relations=[
                Relation(
                    relation=f"REL{i}",
                    from_entity="entity0",
                    to_entity=f"entity{i+1}",
                    source="db.relations",
                    mappings=RelationMapping(from_key="id", to_key="id"),
                    properties=[],
                )
                for i in range(4)
            ],
        )

        output_path = tmp_path / "complex.html"
        generate_d3_visualization(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "entity0" in content
        assert "entity4" in content

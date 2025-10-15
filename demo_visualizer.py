#!/usr/bin/env python3
"""
Demo script for interactive visualization functionality.

This script demonstrates how to generate interactive HTML visualizations
of knowledge graphs using D3.js and Cytoscape.js.
"""

from pathlib import Path

from grai.core.parser.yaml_parser import load_project
from grai.core.visualizer import (
    generate_cytoscape_visualization,
    generate_d3_visualization,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def main():
    """Run visualization demonstrations."""
    project_dir = Path("templates")
    output_dir = Path("templates")

    print("\n🎨 INTERACTIVE VISUALIZATION DEMO")
    print("=" * 60)
    print(f"Project: {project_dir}")

    # Load project
    print_section("1. Load Project")
    project = load_project(project_dir)
    print(f"✓ Loaded: {project.name}")
    print(f"  Entities: {len(project.entities)}")
    print(f"  Relations: {len(project.relations)}")

    # Generate D3 visualization
    print_section("2. Generate D3.js Visualization")
    d3_output = output_dir / "graph-d3-demo.html"
    print(f"Generating: {d3_output}")

    generate_d3_visualization(
        project=project,
        output_path=d3_output,
        title="Knowledge Graph - D3.js",
        width=1200,
        height=800,
    )

    print("✓ Generated D3 visualization")
    print(f"  File: {d3_output}")
    print(f"  Size: {d3_output.stat().st_size:,} bytes")
    print("  Format: Interactive HTML with D3.js force-directed graph")
    print("\nFeatures:")
    print("  • Drag nodes to rearrange")
    print("  • Hover for tooltips")
    print("  • Physics-based layout")
    print("  • Color-coded node types")

    # Generate Cytoscape visualization
    print_section("3. Generate Cytoscape.js Visualization")
    cytoscape_output = output_dir / "graph-cytoscape-demo.html"
    print(f"Generating: {cytoscape_output}")

    generate_cytoscape_visualization(
        project=project,
        output_path=cytoscape_output,
        title="Knowledge Graph - Cytoscape.js",
        width=1200,
        height=800,
    )

    print("✓ Generated Cytoscape visualization")
    print(f"  File: {cytoscape_output}")
    print(f"  Size: {cytoscape_output.stat().st_size:,} bytes")
    print("  Format: Interactive HTML with Cytoscape.js")
    print("\nFeatures:")
    print("  • Click nodes for details")
    print("  • Hierarchical layout")
    print("  • Bezier curves for edges")
    print("  • Shape-based node types")

    # Generate with custom dimensions
    print_section("4. Custom Dimensions")
    custom_output = output_dir / "graph-custom-demo.html"
    print(f"Generating: {custom_output}")

    generate_d3_visualization(
        project=project,
        output_path=custom_output,
        title="Compact View",
        width=800,
        height=600,
    )

    print("✓ Generated custom-sized visualization")
    print("  Dimensions: 800x600 pixels")
    print("  Perfect for embedding in dashboards")

    # Summary
    print_section("5. Summary")
    print("Generated 3 interactive visualizations:")
    print("\n1. D3.js Force-Directed Graph")
    print(f"   {d3_output}")
    print("   Best for: Exploring relationships dynamically")

    print("\n2. Cytoscape.js Network")
    print(f"   {cytoscape_output}")
    print("   Best for: Detailed network analysis")

    print("\n3. Custom Dimensions")
    print(f"   {custom_output}")
    print("   Best for: Embedded views")

    print("\n" + "=" * 60)
    print("📱 Open any HTML file in your browser to view!")
    print("=" * 60)
    print("\nVisualization Features:")
    print("  ✅ Interactive node dragging")
    print("  ✅ Tooltips and labels")
    print("  ✅ Color-coded by type")
    print("  ✅ Responsive layouts")
    print("  ✅ No server required")
    print("  ✅ Works offline")

    print("\nBrowser Compatibility:")
    print("  • Chrome/Edge (recommended)")
    print("  • Firefox")
    print("  • Safari")
    print("  • Any modern browser with JavaScript")

    print("\n" + "=" * 60)
    print("✅ All visualization features demonstrated!")
    print("=" * 60)


if __name__ == "__main__":
    main()

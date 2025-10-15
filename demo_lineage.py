#!/usr/bin/env python3
"""
Demo script for lineage tracking functionality.

This script demonstrates all lineage tracking features in grai.build.
"""

from pathlib import Path

from grai.core.lineage import (
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
from grai.core.parser.yaml_parser import load_project


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def main():
    """Run lineage tracking demonstrations."""
    project_dir = Path("templates")

    print("\n🔍 LINEAGE TRACKING DEMO")
    print("=" * 60)
    print(f"Project: {project_dir}")

    # Load project
    print_section("1. Load Project")
    project = load_project(project_dir)
    print(f"✓ Loaded: {project.name}")
    print(f"  Entities: {len(project.entities)}")
    print(f"  Relations: {len(project.relations)}")

    # Build lineage graph
    print_section("2. Build Lineage Graph")
    graph = build_lineage_graph(project)
    print("✓ Built graph")
    print(f"  Nodes: {len(graph.nodes)}")
    print(f"  Edges: {len(graph.edges)}")
    print("\nNode Types:")
    for node_id, node in graph.nodes.items():
        print(f"  • {node.name} ({node.type.value})")

    # Get entity lineage
    print_section("3. Entity Lineage - customer")
    lineage = get_entity_lineage(graph, "customer")
    print(f"Source: {lineage['source']}")
    print(f"\nUpstream ({len(lineage['upstream'])}):")
    for up in lineage["upstream"]:
        print(f"  ← {up['node']} ({up['type']}) via {up['relation']}")
    print(f"\nDownstream ({len(lineage['downstream'])}):")
    for down in lineage["downstream"]:
        print(f"  → {down['node']} ({down['type']}) via {down['relation']}")

    # Get relation lineage
    print_section("4. Relation Lineage - PURCHASED")
    rel_lineage = get_relation_lineage(graph, "PURCHASED")
    print(f"Connects: {rel_lineage['from_entity']} → {rel_lineage['to_entity']}")
    print(f"Source: {rel_lineage['source']}")
    print(f"\nUpstream ({len(rel_lineage['upstream'])}):")
    for up in rel_lineage["upstream"]:
        print(f"  ← {up['node']} ({up['type']}) via {up['relation']}")
    print(f"\nDownstream ({len(rel_lineage['downstream'])}):")
    for down in rel_lineage["downstream"]:
        print(f"  → {down['node']} ({down['type']}) via {down['relation']}")

    # Find upstream entities
    print_section("5. Find Upstream Entities - product")
    upstream = find_upstream_entities(graph, "product")
    print(f"Found {len(upstream)} upstream entities:")
    for entity in upstream:
        print(f"  • {entity}")

    # Find downstream entities
    print_section("6. Find Downstream Entities - customer")
    downstream = find_downstream_entities(graph, "customer")
    print(f"Found {len(downstream)} downstream entities:")
    for entity in downstream:
        print(f"  • {entity}")

    # Find entity path
    print_section("7. Find Path - customer → product")
    path = find_entity_path(graph, "customer", "product")
    if path:
        print("Path found:")
        print(" → ".join(path))
    else:
        print("No path found")

    # Calculate impact analysis
    print_section("8. Impact Analysis - customer")
    impact = calculate_impact_analysis(graph, "customer")
    print(f"Impact Score: {impact['impact_score']}")
    print(f"Impact Level: {impact['impact_level'].upper()}")
    print(f"\nAffected Entities ({len(impact['affected_entities'])}):")
    for entity in impact["affected_entities"]:
        print(f"  • {entity}")
    print(f"\nAffected Relations ({len(impact['affected_relations'])}):")
    for relation in impact["affected_relations"]:
        print(f"  • {relation}")

    # Get statistics
    print_section("9. Lineage Statistics")
    stats = get_lineage_statistics(graph)
    print(f"Total Nodes: {stats['total_nodes']}")
    print(f"Total Edges: {stats['total_edges']}")
    print(f"Entities: {stats['entity_count']}")
    print(f"Relations: {stats['relation_count']}")
    print(f"Sources: {stats['source_count']}")
    print(f"Max Downstream: {stats['max_downstream_connections']}")
    if stats["most_connected_entity"]:
        print(f"Most Connected: {stats['most_connected_entity']}")

    # Export to JSON
    print_section("10. Export to JSON")
    lineage_dict = export_lineage_to_dict(graph)
    print(f"✓ Exported {len(lineage_dict['nodes'])} nodes")
    print(f"✓ Exported {len(lineage_dict['edges'])} edges")
    print("\nSample node:")
    sample_node = lineage_dict["nodes"][0]
    print(f"  ID: {sample_node['id']}")
    print(f"  Name: {sample_node['name']}")
    print(f"  Type: {sample_node['type']}")

    # Generate Mermaid visualization
    print_section("11. Mermaid Visualization")
    mermaid = visualize_lineage_mermaid(graph)
    print("✓ Generated Mermaid diagram")
    print(f"  Lines: {len(mermaid.splitlines())}")
    print(f"  Characters: {len(mermaid)}")
    print("\nPreview (first 5 lines):")
    for line in mermaid.splitlines()[:5]:
        print(f"  {line}")

    # Generate Graphviz visualization
    print_section("12. Graphviz Visualization")
    graphviz = visualize_lineage_graphviz(graph)
    print("✓ Generated Graphviz DOT")
    print(f"  Lines: {len(graphviz.splitlines())}")
    print(f"  Characters: {len(graphviz)}")
    print("\nPreview (first 5 lines):")
    for line in graphviz.splitlines()[:5]:
        print(f"  {line}")

    # Focused visualization
    print_section("13. Focused Visualization - customer")
    focused_mermaid = visualize_lineage_mermaid(graph, focus_entity="customer")
    print("✓ Generated focused Mermaid diagram")
    print(f"  Lines: {len(focused_mermaid.splitlines())}")
    print("  Highlight: customer node")

    print("\n" + "=" * 60)
    print("✅ All lineage tracking features demonstrated!")
    print("=" * 60)


if __name__ == "__main__":
    main()

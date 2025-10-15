"""
Lineage tracking module for knowledge graph analysis.

Exports lineage tracking functions for analyzing entity relationships,
dependencies, and impact analysis.
"""

from .lineage_tracker import (
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

__all__ = [
    "LineageGraph",
    "LineageNode",
    "LineageEdge",
    "NodeType",
    "build_lineage_graph",
    "get_entity_lineage",
    "get_relation_lineage",
    "find_upstream_entities",
    "find_downstream_entities",
    "find_entity_path",
    "calculate_impact_analysis",
    "get_lineage_statistics",
    "export_lineage_to_dict",
    "visualize_lineage_mermaid",
    "visualize_lineage_graphviz",
]

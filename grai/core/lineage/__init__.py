"""
Lineage tracking module for knowledge graph analysis.

Exports lineage tracking functions for analyzing entity relationships,
dependencies, and impact analysis.
"""

from .lineage_tracker import (
    LineageGraph,
    LineageNode,
    LineageEdge,
    NodeType,
    build_lineage_graph,
    get_entity_lineage,
    get_relation_lineage,
    find_upstream_entities,
    find_downstream_entities,
    find_entity_path,
    calculate_impact_analysis,
    get_lineage_statistics,
    export_lineage_to_dict,
    visualize_lineage_mermaid,
    visualize_lineage_graphviz,
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

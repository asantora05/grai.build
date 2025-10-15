"""
Lineage tracking for knowledge graph analysis.

This module provides functionality to track entity relationships, analyze dependencies,
and calculate impact of changes across the knowledge graph.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from grai.core.models import Project


class NodeType(Enum):
    """Type of lineage node."""

    ENTITY = "entity"
    RELATION = "relation"
    SOURCE = "source"


@dataclass
class LineageNode:
    """
    Represents a node in the lineage graph.

    Attributes:
        id: Unique identifier for the node
        name: Node name (entity name, relation name, or source)
        type: Type of node (entity, relation, or source)
        metadata: Additional metadata about the node
    """

    id: str
    name: str
    type: NodeType
    metadata: Dict = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, LineageNode) and self.id == other.id


@dataclass
class LineageEdge:
    """
    Represents an edge in the lineage graph.

    Attributes:
        from_node: Source node ID
        to_node: Target node ID
        relation_type: Type of relationship (e.g., "depends_on", "produces")
        metadata: Additional metadata about the edge
    """

    from_node: str
    to_node: str
    relation_type: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class LineageGraph:
    """
    Represents the complete lineage graph.

    Attributes:
        nodes: Dictionary mapping node IDs to LineageNode objects
        edges: List of LineageEdge objects
        entity_map: Mapping of entity names to node IDs
        relation_map: Mapping of relation names to node IDs
        source_map: Mapping of source names to node IDs
    """

    nodes: Dict[str, LineageNode] = field(default_factory=dict)
    edges: List[LineageEdge] = field(default_factory=list)
    entity_map: Dict[str, str] = field(default_factory=dict)
    relation_map: Dict[str, str] = field(default_factory=dict)
    source_map: Dict[str, str] = field(default_factory=dict)

    def add_node(self, node: LineageNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

        if node.type == NodeType.ENTITY:
            self.entity_map[node.name] = node.id
        elif node.type == NodeType.RELATION:
            self.relation_map[node.name] = node.id
        elif node.type == NodeType.SOURCE:
            self.source_map[node.name] = node.id

    def add_edge(self, edge: LineageEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[LineageNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_edges_from(self, node_id: str) -> List[LineageEdge]:
        """Get all edges originating from a node."""
        return [edge for edge in self.edges if edge.from_node == node_id]

    def get_edges_to(self, node_id: str) -> List[LineageEdge]:
        """Get all edges pointing to a node."""
        return [edge for edge in self.edges if edge.to_node == node_id]


def build_lineage_graph(project: Project) -> LineageGraph:
    """
    Build a complete lineage graph from a project.

    Args:
        project: Project to analyze

    Returns:
        LineageGraph with all entities, relations, and sources
    """
    graph = LineageGraph()

    # Add entity nodes
    for entity in project.entities:
        source_config = entity.get_source_config()
        source_name = source_config.name

        node_id = f"entity:{entity.entity}"
        node = LineageNode(
            id=node_id,
            name=entity.entity,
            type=NodeType.ENTITY,
            metadata={
                "source": source_name,
                "source_type": source_config.type.value if source_config.type else None,
                "keys": entity.keys,
                "property_count": len(entity.properties),
                "description": getattr(entity, "description", None),
            },
        )
        graph.add_node(node)

        # Add source node if not exists
        source_id = f"source:{source_name}"
        if source_id not in graph.nodes:
            source_node = LineageNode(
                id=source_id,
                name=source_name,
                type=NodeType.SOURCE,
                metadata={
                    "type": "data_source",
                    "source_type": source_config.type.value if source_config.type else None,
                },
            )
            graph.add_node(source_node)

        # Add edge from source to entity
        graph.add_edge(
            LineageEdge(
                from_node=source_id,
                to_node=node_id,
                relation_type="produces",
                metadata={"keys": entity.keys},
            )
        )

    # Add relation nodes and edges
    for relation in project.relations:
        source_config = relation.get_source_config()
        source_name = source_config.name

        node_id = f"relation:{relation.relation}"
        node = LineageNode(
            id=node_id,
            name=relation.relation,
            type=NodeType.RELATION,
            metadata={
                "source": source_name,
                "source_type": source_config.type.value if source_config.type else None,
                "from_entity": relation.from_entity,
                "to_entity": relation.to_entity,
                "property_count": len(relation.properties),
                "description": getattr(relation, "description", None),
            },
        )
        graph.add_node(node)

        # Add source node if not exists
        source_id = f"source:{source_name}"
        if source_id not in graph.nodes:
            source_node = LineageNode(
                id=source_id,
                name=source_name,
                type=NodeType.SOURCE,
                metadata={
                    "type": "data_source",
                    "source_type": source_config.type.value if source_config.type else None,
                },
            )
            graph.add_node(source_node)

        # Add edge from source to relation
        graph.add_edge(
            LineageEdge(from_node=source_id, to_node=node_id, relation_type="produces", metadata={})
        )

        # Add edges from entities to relation
        from_entity_id = f"entity:{relation.from_entity}"
        to_entity_id = f"entity:{relation.to_entity}"

        graph.add_edge(
            LineageEdge(
                from_node=from_entity_id,
                to_node=node_id,
                relation_type="participates_in",
                metadata={"role": "from", "key": relation.mappings.from_key},
            )
        )

        graph.add_edge(
            LineageEdge(
                from_node=node_id,
                to_node=to_entity_id,
                relation_type="connects_to",
                metadata={"role": "to", "key": relation.mappings.to_key},
            )
        )

    return graph


def get_entity_lineage(graph: LineageGraph, entity_name: str) -> Dict:
    """
    Get complete lineage information for an entity.

    Args:
        graph: Lineage graph
        entity_name: Name of the entity

    Returns:
        Dictionary with lineage information
    """
    node_id = graph.entity_map.get(entity_name)
    if not node_id:
        return {"error": f"Entity '{entity_name}' not found"}

    node = graph.get_node(node_id)

    # Get upstream (sources)
    upstream_edges = graph.get_edges_to(node_id)
    upstream = [
        {
            "node": graph.get_node(edge.from_node).name,
            "type": graph.get_node(edge.from_node).type.value,
            "relation": edge.relation_type,
        }
        for edge in upstream_edges
    ]

    # Get downstream (relations)
    downstream_edges = graph.get_edges_from(node_id)
    downstream = [
        {
            "node": graph.get_node(edge.to_node).name,
            "type": graph.get_node(edge.to_node).type.value,
            "relation": edge.relation_type,
        }
        for edge in downstream_edges
    ]

    return {
        "entity": entity_name,
        "source": node.metadata.get("source"),
        "upstream": upstream,
        "downstream": downstream,
        "metadata": node.metadata,
    }


def get_relation_lineage(graph: LineageGraph, relation_name: str) -> Dict:
    """
    Get complete lineage information for a relation.

    Args:
        graph: Lineage graph
        relation_name: Name of the relation

    Returns:
        Dictionary with lineage information
    """
    node_id = graph.relation_map.get(relation_name)
    if not node_id:
        return {"error": f"Relation '{relation_name}' not found"}

    node = graph.get_node(node_id)

    # Get upstream (sources and entities)
    upstream_edges = graph.get_edges_to(node_id)
    upstream = [
        {
            "node": graph.get_node(edge.from_node).name,
            "type": graph.get_node(edge.from_node).type.value,
            "relation": edge.relation_type,
        }
        for edge in upstream_edges
    ]

    # Get downstream (entities)
    downstream_edges = graph.get_edges_from(node_id)
    downstream = [
        {
            "node": graph.get_node(edge.to_node).name,
            "type": graph.get_node(edge.to_node).type.value,
            "relation": edge.relation_type,
        }
        for edge in downstream_edges
    ]

    return {
        "relation": relation_name,
        "source": node.metadata.get("source"),
        "from_entity": node.metadata.get("from_entity"),
        "to_entity": node.metadata.get("to_entity"),
        "upstream": upstream,
        "downstream": downstream,
        "metadata": node.metadata,
    }


def find_upstream_entities(graph: LineageGraph, entity_name: str, max_depth: int = 10) -> Set[str]:
    """
    Find all upstream entities (recursive).

    Args:
        graph: Lineage graph
        entity_name: Name of the entity
        max_depth: Maximum depth to traverse

    Returns:
        Set of upstream entity names
    """
    node_id = graph.entity_map.get(entity_name)
    if not node_id:
        return set()

    visited = set()
    upstream = set()

    def traverse(current_id: str, depth: int):
        if depth >= max_depth or current_id in visited:
            return

        visited.add(current_id)
        edges = graph.get_edges_to(current_id)

        for edge in edges:
            from_node = graph.get_node(edge.from_node)
            if from_node and from_node.type == NodeType.ENTITY:
                upstream.add(from_node.name)
                traverse(edge.from_node, depth + 1)
            elif from_node and from_node.type == NodeType.RELATION:
                # Traverse through relation to find entities
                traverse(edge.from_node, depth + 1)

    traverse(node_id, 0)
    return upstream


def find_downstream_entities(
    graph: LineageGraph, entity_name: str, max_depth: int = 10
) -> Set[str]:
    """
    Find all downstream entities (recursive).

    Args:
        graph: Lineage graph
        entity_name: Name of the entity
        max_depth: Maximum depth to traverse

    Returns:
        Set of downstream entity names
    """
    node_id = graph.entity_map.get(entity_name)
    if not node_id:
        return set()

    visited = set()
    downstream = set()

    def traverse(current_id: str, depth: int):
        if depth >= max_depth or current_id in visited:
            return

        visited.add(current_id)
        edges = graph.get_edges_from(current_id)

        for edge in edges:
            to_node = graph.get_node(edge.to_node)
            if to_node and to_node.type == NodeType.ENTITY:
                downstream.add(to_node.name)
                traverse(edge.to_node, depth + 1)
            elif to_node and to_node.type == NodeType.RELATION:
                # Traverse through relation to find entities
                traverse(edge.to_node, depth + 1)

    traverse(node_id, 0)
    return downstream


def find_entity_path(graph: LineageGraph, from_entity: str, to_entity: str) -> Optional[List[str]]:
    """
    Find shortest path between two entities.

    Args:
        graph: Lineage graph
        from_entity: Starting entity name
        to_entity: Target entity name

    Returns:
        List of node names representing the path, or None if no path exists
    """
    from_id = graph.entity_map.get(from_entity)
    to_id = graph.entity_map.get(to_entity)

    if not from_id or not to_id:
        return None

    # BFS to find shortest path
    queue = [(from_id, [from_entity])]
    visited = {from_id}

    while queue:
        current_id, path = queue.pop(0)

        if current_id == to_id:
            return path

        # Check outgoing edges
        for edge in graph.get_edges_from(current_id):
            if edge.to_node not in visited:
                visited.add(edge.to_node)
                node = graph.get_node(edge.to_node)
                queue.append((edge.to_node, path + [node.name]))

    return None


def calculate_impact_analysis(graph: LineageGraph, entity_name: str) -> Dict:
    """
    Calculate the impact of changes to an entity.

    Args:
        graph: Lineage graph
        entity_name: Name of the entity to analyze

    Returns:
        Dictionary with impact analysis
    """
    node_id = graph.entity_map.get(entity_name)
    if not node_id:
        return {"error": f"Entity '{entity_name}' not found"}

    # Find all affected entities and relations
    downstream_entities = find_downstream_entities(graph, entity_name)

    # Find affected relations
    affected_relations = set()
    for edge in graph.get_edges_from(node_id):
        to_node = graph.get_node(edge.to_node)
        if to_node and to_node.type == NodeType.RELATION:
            affected_relations.add(to_node.name)

    # Calculate impact score (simple: count of affected nodes)
    impact_score = len(downstream_entities) + len(affected_relations)

    return {
        "entity": entity_name,
        "impact_score": impact_score,
        "affected_entities": sorted(downstream_entities),
        "affected_relations": sorted(affected_relations),
        "impact_level": _calculate_impact_level(impact_score),
    }


def _calculate_impact_level(score: int) -> str:
    """Calculate impact level based on score."""
    if score == 0:
        return "none"
    elif score <= 2:
        return "low"
    elif score <= 5:
        return "medium"
    else:
        return "high"


def get_lineage_statistics(graph: LineageGraph) -> Dict:
    """
    Get statistics about the lineage graph.

    Args:
        graph: Lineage graph

    Returns:
        Dictionary with statistics
    """
    entity_count = len([n for n in graph.nodes.values() if n.type == NodeType.ENTITY])
    relation_count = len([n for n in graph.nodes.values() if n.type == NodeType.RELATION])
    source_count = len([n for n in graph.nodes.values() if n.type == NodeType.SOURCE])

    # Calculate connectivity
    max_downstream = 0
    most_connected_entity = None

    for entity_name in graph.entity_map.keys():
        downstream = find_downstream_entities(graph, entity_name)
        if len(downstream) > max_downstream:
            max_downstream = len(downstream)
            most_connected_entity = entity_name

    return {
        "total_nodes": len(graph.nodes),
        "total_edges": len(graph.edges),
        "entity_count": entity_count,
        "relation_count": relation_count,
        "source_count": source_count,
        "max_downstream_connections": max_downstream,
        "most_connected_entity": most_connected_entity,
    }


def export_lineage_to_dict(graph: LineageGraph) -> Dict:
    """
    Export lineage graph to dictionary format.

    Args:
        graph: Lineage graph

    Returns:
        Dictionary representation of the graph
    """
    return {
        "nodes": [
            {
                "id": node.id,
                "name": node.name,
                "type": node.type.value,
                "metadata": node.metadata,
            }
            for node in graph.nodes.values()
        ],
        "edges": [
            {
                "from": edge.from_node,
                "to": edge.to_node,
                "type": edge.relation_type,
                "metadata": edge.metadata,
            }
            for edge in graph.edges
        ],
        "statistics": get_lineage_statistics(graph),
    }


def visualize_lineage_mermaid(graph: LineageGraph, focus_entity: Optional[str] = None) -> str:
    """
    Generate Mermaid diagram representation of lineage.

    Args:
        graph: Lineage graph
        focus_entity: Optional entity to focus on (shows only related nodes)

    Returns:
        Mermaid diagram as string
    """
    lines = ["graph LR"]

    # Filter nodes if focus entity specified
    if focus_entity:
        node_id = graph.entity_map.get(focus_entity)
        if node_id:
            # Get related nodes
            related_ids = {node_id}
            for edge in graph.edges:
                if edge.from_node == node_id:
                    related_ids.add(edge.to_node)
                if edge.to_node == node_id:
                    related_ids.add(edge.from_node)

            nodes_to_show = {nid: graph.nodes[nid] for nid in related_ids if nid in graph.nodes}
            edges_to_show = [
                e for e in graph.edges if e.from_node in related_ids and e.to_node in related_ids
            ]
        else:
            nodes_to_show = graph.nodes
            edges_to_show = graph.edges
    else:
        nodes_to_show = graph.nodes
        edges_to_show = graph.edges

    # Add node definitions with styling
    for node in nodes_to_show.values():
        node.name.replace(" ", "_")
        if node.type == NodeType.ENTITY:
            lines.append(f'    {node.id.replace(":", "_")}["{node.name}"]')
            lines.append(f'    style {node.id.replace(":", "_")} fill:#e1f5ff,stroke:#0288d1')
        elif node.type == NodeType.RELATION:
            lines.append(f'    {node.id.replace(":", "_")}{{"{node.name}"}}')
            lines.append(f'    style {node.id.replace(":", "_")} fill:#fff9c4,stroke:#f57f17')
        elif node.type == NodeType.SOURCE:
            lines.append(f'    {node.id.replace(":", "_")}[("{node.name}")]')
            lines.append(f'    style {node.id.replace(":", "_")} fill:#f3e5f5,stroke:#7b1fa2')

    # Add edges
    for edge in edges_to_show:
        from_id = edge.from_node.replace(":", "_")
        to_id = edge.to_node.replace(":", "_")
        lines.append(f"    {from_id} -->|{edge.relation_type}| {to_id}")

    return "\n".join(lines)


def visualize_lineage_graphviz(graph: LineageGraph, focus_entity: Optional[str] = None) -> str:
    """
    Generate Graphviz DOT representation of lineage.

    Args:
        graph: Lineage graph
        focus_entity: Optional entity to focus on (shows only related nodes)

    Returns:
        Graphviz DOT diagram as string
    """
    lines = ["digraph lineage {"]
    lines.append("    rankdir=LR;")
    lines.append("    node [shape=box, style=rounded];")

    # Filter nodes if focus entity specified
    if focus_entity:
        node_id = graph.entity_map.get(focus_entity)
        if node_id:
            # Get related nodes
            related_ids = {node_id}
            for edge in graph.edges:
                if edge.from_node == node_id:
                    related_ids.add(edge.to_node)
                if edge.to_node == node_id:
                    related_ids.add(edge.from_node)

            nodes_to_show = {nid: graph.nodes[nid] for nid in related_ids if nid in graph.nodes}
            edges_to_show = [
                e for e in graph.edges if e.from_node in related_ids and e.to_node in related_ids
            ]
        else:
            nodes_to_show = graph.nodes
            edges_to_show = graph.edges
    else:
        nodes_to_show = graph.nodes
        edges_to_show = graph.edges

    # Add node definitions with styling
    for node in nodes_to_show.values():
        node_id = node.id.replace(":", "_")
        if node.type == NodeType.ENTITY:
            lines.append(
                f'    {node_id} [label="{node.name}", fillcolor="#e1f5ff", style="filled,rounded"];'
            )
        elif node.type == NodeType.RELATION:
            lines.append(
                f'    {node_id} [label="{node.name}", shape=diamond, fillcolor="#fff9c4", style="filled"];'
            )
        elif node.type == NodeType.SOURCE:
            lines.append(
                f'    {node_id} [label="{node.name}", shape=cylinder, fillcolor="#f3e5f5", style="filled"];'
            )

    # Add edges
    for edge in edges_to_show:
        from_id = edge.from_node.replace(":", "_")
        to_id = edge.to_node.replace(":", "_")
        lines.append(f'    {from_id} -> {to_id} [label="{edge.relation_type}"];')

    lines.append("}")
    return "\n".join(lines)

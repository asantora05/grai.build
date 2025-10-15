"""
Interactive visualization module for knowledge graphs.

Provides HTML-based interactive visualizations using D3.js and other web technologies.
"""

from pathlib import Path
from typing import Dict, Optional

from grai.core.lineage import (
    build_lineage_graph,
    export_lineage_to_dict,
    get_lineage_statistics,
)
from grai.core.models import Project


def generate_d3_visualization(
    project: Project,
    output_path: Path,
    title: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
) -> None:
    """
    Generate interactive D3.js visualization of the knowledge graph.

    Creates an HTML file with an interactive force-directed graph using D3.js.

    Args:
        project: The Project to visualize
        output_path: Path to save the HTML file
        title: Optional title for the visualization (defaults to project name)
        width: Width of the visualization canvas in pixels
        height: Height of the visualization canvas in pixels

    Example:
        >>> from grai.core.parser.yaml_parser import load_project
        >>> project = load_project(Path("."))
        >>> generate_d3_visualization(project, Path("graph.html"))
    """
    # Build lineage graph
    graph = build_lineage_graph(project)
    graph_data = export_lineage_to_dict(graph)
    stats = get_lineage_statistics(graph)

    # Use project name as default title
    if title is None:
        title = project.name

    # Generate HTML with embedded D3.js visualization
    html_content = _generate_d3_html(
        title=title,
        graph_data=graph_data,
        stats=stats,
        width=width,
        height=height,
    )

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")


def generate_cytoscape_visualization(
    project: Project,
    output_path: Path,
    title: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
) -> None:
    """
    Generate interactive Cytoscape.js visualization of the knowledge graph.

    Creates an HTML file with an interactive graph using Cytoscape.js.

    Args:
        project: The Project to visualize
        output_path: Path to save the HTML file
        title: Optional title for the visualization (defaults to project name)
        width: Width of the visualization canvas in pixels
        height: Height of the visualization canvas in pixels

    Example:
        >>> from grai.core.parser.yaml_parser import load_project
        >>> project = load_project(Path("."))
        >>> generate_cytoscape_visualization(project, Path("graph.html"))
    """
    # Build lineage graph
    graph = build_lineage_graph(project)
    graph_data = export_lineage_to_dict(graph)
    stats = get_lineage_statistics(graph)

    # Use project name as default title
    if title is None:
        title = project.name

    # Generate HTML with embedded Cytoscape.js visualization
    html_content = _generate_cytoscape_html(
        title=title,
        graph_data=graph_data,
        stats=stats,
        width=width,
        height=height,
    )

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")


def _generate_d3_html(
    title: str,
    graph_data: Dict,
    stats: Dict,
    width: int,
    height: int,
) -> str:
    """Generate HTML with D3.js force-directed graph."""

    # Convert graph data to D3 format
    nodes = []
    links = []

    for node in graph_data["nodes"]:
        nodes.append(
            {
                "id": node["id"],
                "name": node["name"],
                "type": node["type"],
            }
        )

    for edge in graph_data["edges"]:
        links.append(
            {
                "source": edge["from"],
                "target": edge["to"],
                "type": edge["type"],
            }
        )

    import json

    nodes_json = json.dumps(nodes)
    links_json = json.dumps(links)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Knowledge Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: {width + 40}px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            font-size: 14px;
            opacity: 0.9;
        }}
        .stat {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        #graph {{
            background: white;
        }}
        .legend {{
            padding: 20px;
            background: #f9f9f9;
            border-top: 1px solid #e0e0e0;
        }}
        .legend-title {{
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .legend-items {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}
        .node {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}
        .node.entity {{
            fill: #4fc3f7;
        }}
        .node.relation {{
            fill: #ffd54f;
        }}
        .node.source {{
            fill: #ba68c8;
        }}
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 2px;
        }}
        .node-label {{
            font-size: 12px;
            pointer-events: none;
            text-anchor: middle;
            fill: #333;
        }}
        .tooltip {{
            position: absolute;
            padding: 8px 12px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 {title}</h1>
            <div class="stats">
                <div class="stat">
                    <span>📊</span>
                    <span>{stats['total_nodes']} nodes</span>
                </div>
                <div class="stat">
                    <span>🔗</span>
                    <span>{stats['total_edges']} edges</span>
                </div>
                <div class="stat">
                    <span>🏢</span>
                    <span>{stats['entity_count']} entities</span>
                </div>
                <div class="stat">
                    <span>↔️</span>
                    <span>{stats['relation_count']} relations</span>
                </div>
                <div class="stat">
                    <span>📁</span>
                    <span>{stats['source_count']} sources</span>
                </div>
            </div>
        </div>

        <svg id="graph" width="{width}" height="{height}"></svg>

        <div class="legend">
            <div class="legend-title">Legend</div>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background: #4fc3f7;"></div>
                    <span>Entity</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffd54f;"></div>
                    <span>Relation</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ba68c8;"></div>
                    <span>Source</span>
                </div>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const nodes = {nodes_json};
        const links = {links_json};

        const svg = d3.select("#graph");
        const width = {width};
        const height = {height};

        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(40));

        // Create links
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "link");

        // Create nodes
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("class", d => `node ${{d.type}}`)
            .attr("r", 15)
            .call(drag(simulation))
            .on("mouseover", showTooltip)
            .on("mouseout", hideTooltip);

        // Create labels
        const label = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .join("text")
            .attr("class", "node-label")
            .attr("dy", 30)
            .text(d => d.name);

        // Update positions on tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});

        // Drag functionality
        function drag(simulation) {{
            function dragstarted(event) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }}

            function dragged(event) {{
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }}

            function dragended(event) {{
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }}

            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }}

        // Tooltip functions
        function showTooltip(event, d) {{
            const tooltip = d3.select("#tooltip");
            tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px")
                .html(`<strong>${{d.name}}</strong><br>Type: ${{d.type}}`);
        }}

        function hideTooltip() {{
            d3.select("#tooltip").style("opacity", 0);
        }}
    </script>
</body>
</html>
"""


def _generate_cytoscape_html(
    title: str,
    graph_data: Dict,
    stats: Dict,
    width: int,
    height: int,
) -> str:
    """Generate HTML with Cytoscape.js graph."""

    # Convert graph data to Cytoscape format
    elements = []

    for node in graph_data["nodes"]:
        elements.append(
            {
                "data": {
                    "id": node["id"],
                    "label": node["name"],
                    "type": node["type"],
                }
            }
        )

    for edge in graph_data["edges"]:
        elements.append(
            {
                "data": {
                    "source": edge["from"],
                    "target": edge["to"],
                    "label": edge["type"],
                }
            }
        )

    import json

    elements_json = json.dumps(elements)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Knowledge Graph Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: {width + 40}px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            font-size: 14px;
            opacity: 0.9;
        }}
        .stat {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        #cy {{
            width: {width}px;
            height: {height}px;
            background: white;
        }}
        .legend {{
            padding: 20px;
            background: #f9f9f9;
            border-top: 1px solid #e0e0e0;
        }}
        .legend-title {{
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .legend-items {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 {title}</h1>
            <div class="stats">
                <div class="stat">
                    <span>📊</span>
                    <span>{stats['total_nodes']} nodes</span>
                </div>
                <div class="stat">
                    <span>🔗</span>
                    <span>{stats['total_edges']} edges</span>
                </div>
                <div class="stat">
                    <span>🏢</span>
                    <span>{stats['entity_count']} entities</span>
                </div>
                <div class="stat">
                    <span>↔️</span>
                    <span>{stats['relation_count']} relations</span>
                </div>
                <div class="stat">
                    <span>📁</span>
                    <span>{stats['source_count']} sources</span>
                </div>
            </div>
        </div>

        <div id="cy"></div>

        <div class="legend">
            <div class="legend-title">Legend</div>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background: #4fc3f7;"></div>
                    <span>Entity</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffd54f;"></div>
                    <span>Relation</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ba68c8;"></div>
                    <span>Source</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {elements_json},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'background-color': '#4fc3f7',
                        'border-width': 2,
                        'border-color': '#fff',
                        'width': 40,
                        'height': 40
                    }}
                }},
                {{
                    selector: 'node[type="entity"]',
                    style: {{
                        'background-color': '#4fc3f7',
                        'shape': 'roundrectangle'
                    }}
                }},
                {{
                    selector: 'node[type="relation"]',
                    style: {{
                        'background-color': '#ffd54f',
                        'shape': 'diamond'
                    }}
                }},
                {{
                    selector: 'node[type="source"]',
                    style: {{
                        'background-color': '#ba68c8',
                        'shape': 'ellipse'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 2,
                        'line-color': '#999',
                        'target-arrow-color': '#999',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'text-rotation': 'autorotate',
                        'text-margin-y': -10
                    }}
                }}
            ],
            layout: {{
                name: 'cose',
                animate: true,
                animationDuration: 1000,
                nodeRepulsion: 8000,
                idealEdgeLength: 100,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0
            }}
        }});

        // Add click handlers
        cy.on('tap', 'node', function(evt) {{
            const node = evt.target;
            console.log('Clicked node:', node.data());
        }});
    </script>
</body>
</html>
"""

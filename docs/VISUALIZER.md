# Interactive Visualization - grai.build

## Overview

The visualization module provides interactive HTML-based visualizations of knowledge graphs using modern web technologies like D3.js and Cytoscape.js. Generate beautiful, interactive diagrams that can be opened in any web browser without requiring a server.

## Features

- **D3.js Force-Directed Graphs**: Physics-based interactive layouts
- **Cytoscape.js Networks**: Professional network visualization
- **Drag-and-Drop**: Rearrange nodes interactively
- **Tooltips**: Hover to see node details
- **Color Coding**: Visual distinction by node type
- **Responsive**: Works on desktop and mobile browsers
- **Offline**: No server or internet connection required
- **Customizable**: Control dimensions, titles, and styles

## Architecture

### Core Components

```
grai/core/visualizer/
├── __init__.py           # Module exports
└── visualizer.py         # Visualization generators
```

### Supported Formats

1. **D3.js** - Force-directed graph with physics simulation
2. **Cytoscape.js** - Network visualization with hierarchical layout

## API Reference

### D3.js Visualization

#### `generate_d3_visualization(project, output_path, title=None, width=1200, height=800)`

Generate an interactive D3.js force-directed graph visualization.

**Parameters:**

- `project` (Project): The grai.build Project to visualize
- `output_path` (Path): Path to save the HTML file
- `title` (str, optional): Custom title (defaults to project name)
- `width` (int): Canvas width in pixels (default: 1200)
- `height` (int): Canvas height in pixels (default: 800)

**Returns:**

- None (writes HTML file to disk)

**Example:**

```python
from pathlib import Path
from grai.core.parser.yaml_parser import load_project
from grai.core.visualizer import generate_d3_visualization

# Load project
project = load_project(Path("."))

# Generate visualization
generate_d3_visualization(
    project=project,
    output_path=Path("graph.html"),
    title="My Knowledge Graph",
    width=1200,
    height=800,
)
```

**Features:**

- Physics-based force simulation
- Drag nodes to rearrange
- Automatic collision detection
- Smooth animations
- Hover tooltips
- Color-coded node types:
  - 🔵 Entities (light blue)
  - 🟡 Relations (yellow)
  - 🟣 Sources (purple)

### Cytoscape.js Visualization

#### `generate_cytoscape_visualization(project, output_path, title=None, width=1200, height=800)`

Generate an interactive Cytoscape.js network visualization.

**Parameters:**

- `project` (Project): The grai.build Project to visualize
- `output_path` (Path): Path to save the HTML file
- `title` (str, optional): Custom title (defaults to project name)
- `width` (int): Canvas width in pixels (default: 1200)
- `height` (int): Canvas height in pixels (default: 800)

**Returns:**

- None (writes HTML file to disk)

**Example:**

```python
from pathlib import Path
from grai.core.parser.yaml_parser import load_project
from grai.core.visualizer import generate_cytoscape_visualization

# Load project
project = load_project(Path("."))

# Generate visualization
generate_cytoscape_visualization(
    project=project,
    output_path=Path("graph.html"),
    title="My Knowledge Graph",
    width=1200,
    height=800,
)
```

**Features:**

- COSE (Compound Spring Embedder) layout
- Shape-based node types:
  - ▭ Entities (rounded rectangles)
  - ◇ Relations (diamonds)
  - ⬭ Sources (ellipses)
- Bezier edge curves
- Edge labels
- Click interactions
- Professional styling

## CLI Usage

The `grai visualize` command provides easy access to visualization generation.

### Basic Usage

```bash
grai visualize [PROJECT_DIR] [OPTIONS]
```

### Options

- `--output`, `-o`: Output HTML file path (default: `graph.html`)
- `--format`, `-f`: Visualization format: `d3` or `cytoscape` (default: `d3`)
- `--title`, `-t`: Custom title (defaults to project name)
- `--width`, `-w`: Canvas width in pixels (default: 1200)
- `--height`, `-h`: Canvas height in pixels (default: 800)
- `--open`: Open in default browser after generation

### Examples

#### Generate D3 visualization

```bash
grai visualize
```

**Output:**

```
🎨 Generating Interactive Visualization

✓ Loaded project: example-ecommerce-graph
→ Generating D3 visualization...
✓ Generated visualization: graph.html
   Size: 8,595 bytes

📱 Open the HTML file in your browser to view the interactive graph!
```

#### Generate Cytoscape visualization

```bash
grai visualize --format cytoscape --output cytoscape.html
```

#### Custom dimensions

```bash
grai visualize --width 800 --height 600 --output compact.html
```

#### Custom title

```bash
grai visualize --title "E-Commerce Knowledge Graph"
```

#### Open in browser automatically

```bash
grai visualize --open
```

#### Generate for specific project

```bash
grai visualize templates --output templates/graph.html
```

## Visualization Comparison

### D3.js vs Cytoscape.js

| Feature         | D3.js                    | Cytoscape.js         |
| --------------- | ------------------------ | -------------------- |
| **Layout**      | Force-directed (physics) | Hierarchical (COSE)  |
| **Interaction** | Drag to rearrange        | Click for details    |
| **Performance** | Best for < 100 nodes     | Best for < 500 nodes |
| **Aesthetics**  | Dynamic, organic         | Clean, structured    |
| **Use Case**    | Exploration              | Analysis             |
| **File Size**   | ~8-10 KB                 | ~7-9 KB              |

### When to Use Each

**Use D3.js when:**

- Exploring relationships dynamically
- Want physics-based layouts
- Prefer organic, flowing visualizations
- Need drag-and-drop interaction

**Use Cytoscape.js when:**

- Performing network analysis
- Need hierarchical layouts
- Want professional, clean styling
- Prefer structured arrangements

## Use Cases

### 1. Documentation

Generate visualizations for project documentation:

```python
from grai.core.parser.yaml_parser import load_project
from grai.core.visualizer import generate_d3_visualization

project = load_project(".")

# Generate for docs
generate_d3_visualization(
    project=project,
    output_path="docs/graph.html",
    title="System Architecture",
)
```

Then embed in markdown:

```markdown
# System Architecture

[View Interactive Graph](./graph.html)
```

### 2. Data Lineage Dashboard

Create a dashboard showing data lineage:

```python
# Generate multiple views
generate_d3_visualization(
    project,
    "dashboard/overview.html",
    title="Data Lineage Overview"
)

generate_cytoscape_visualization(
    project,
    "dashboard/detailed.html",
    title="Detailed Network Analysis"
)
```

### 3. Presentations

Generate compact visualizations for slides:

```python
generate_d3_visualization(
    project,
    "presentation/graph.html",
    width=800,
    height=600,
)
```

### 4. Reports

Include in automated reports:

```python
import datetime

timestamp = datetime.datetime.now().strftime("%Y-%m-%d")

generate_cytoscape_visualization(
    project,
    f"reports/lineage-{timestamp}.html",
    title=f"Lineage Report - {timestamp}",
)
```

### 5. CI/CD Integration

Generate visualizations in CI pipeline:

```bash
#!/bin/bash
# In .github/workflows/docs.yml

grai visualize --output docs/graph.html
git add docs/graph.html
git commit -m "Update graph visualization"
```

## Customization

### HTML Structure

Each generated HTML file includes:

1. **Header**: Project name and statistics
2. **Canvas**: Interactive graph visualization
3. **Legend**: Node type color guide
4. **Embedded Scripts**: D3.js or Cytoscape.js from CDN

### Modifying Visualizations

To customize styling, edit the generated HTML:

```html
<!-- Change node colors -->
<style>
  .node.entity {
    fill: #ff6b6b; /* Custom red for entities */
  }
</style>
```

### Responsive Design

Visualizations are responsive by default. For mobile optimization:

```python
# Mobile-friendly dimensions
generate_d3_visualization(
    project,
    "mobile.html",
    width=600,
    height=400,
)
```

## Performance

### File Sizes

- D3 visualization: ~8-10 KB
- Cytoscape visualization: ~7-9 KB
- Both use CDN for libraries (no local dependencies)

### Loading Times

- Small graphs (< 10 nodes): Instant
- Medium graphs (10-100 nodes): < 1 second
- Large graphs (100-500 nodes): 1-3 seconds

### Optimization Tips

1. **For large graphs**: Use Cytoscape (better performance)
2. **For web embedding**: Compress HTML with gzip
3. **For offline use**: Download CDN libraries locally

## Browser Compatibility

### Supported Browsers

✅ Chrome/Edge 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Opera 76+

### Requirements

- JavaScript enabled
- Modern browser with SVG/Canvas support
- No plugins or extensions needed

## Troubleshooting

### Visualization doesn't load

**Problem:** HTML file opens but shows blank page

**Solution:**

1. Check browser console for errors
2. Ensure JavaScript is enabled
3. Try a different browser
4. Check internet connection (CDN libraries)

### Nodes overlap

**Problem:** Nodes are clustered together

**Solution:**

- For D3: Drag nodes apart (physics will stabilize)
- For Cytoscape: Increase canvas size
- Use larger dimensions: `--width 1600 --height 1200`

### File won't open

**Problem:** Double-click doesn't open file

**Solution:**

- Right-click → "Open With" → Browser
- Or drag file into browser window
- Or use CLI: `grai visualize --open`

### Missing node labels

**Problem:** Labels are cut off

**Solution:**

- Increase canvas height
- Zoom out in browser (Ctrl/Cmd + -)

## Best Practices

### 1. Choose the Right Format

- **Quick exploration**: Use D3
- **Formal analysis**: Use Cytoscape
- **Both**: Generate both formats

### 2. Optimize Dimensions

- **Default (1200x800)**: Good for most cases
- **Compact (800x600)**: Embedded views
- **Large (1600x1200)**: Complex graphs

### 3. Naming Conventions

```bash
grai visualize --output graphs/v1.0-d3.html
grai visualize --format cytoscape --output graphs/v1.0-cytoscape.html
```

### 4. Version Control

Add to `.gitignore` if regenerated:

```
# Generated visualizations
*.html
graphs/
```

Or commit for documentation:

```bash
grai visualize --output docs/graph.html
git add docs/graph.html
```

### 5. Automation

```python
# In your build script
def generate_visualizations(project_dir):
    """Generate all visualization formats."""
    project = load_project(project_dir)

    formats = [
        ("d3", "graph-d3.html"),
        ("cytoscape", "graph-cytoscape.html"),
    ]

    for fmt, filename in formats:
        if fmt == "d3":
            generate_d3_visualization(project, Path(filename))
        else:
            generate_cytoscape_visualization(project, Path(filename))
```

## Testing

The visualization module includes comprehensive tests:

```bash
# Run visualization tests
pytest tests/test_visualizer.py -v

# Check coverage
pytest tests/test_visualizer.py --cov=grai.core.visualizer
```

**Test Coverage:**

- HTML generation
- File creation
- Custom parameters
- Both formats
- Integration tests

**Total:** 16 tests, 100% coverage

## Examples

See `demo_visualizer.py` for a comprehensive demonstration:

```bash
python demo_visualizer.py
```

**Demonstration includes:**

- D3.js visualization generation
- Cytoscape.js visualization generation
- Custom dimensions
- File size comparison
- Feature overview

## Future Enhancements

Planned features for future versions:

1. **3D Visualization** - WebGL-based 3D graphs
2. **Animated Transitions** - Show graph evolution over time
3. **Filter Controls** - Interactive filtering in browser
4. **Export Features** - Save as PNG/SVG from browser
5. **Themes** - Dark mode and custom color schemes
6. **Clustering** - Automatic node grouping
7. **Search** - Find nodes in large graphs
8. **Zoom Controls** - Better navigation for large graphs

## Summary

The visualization module provides:

✅ Interactive HTML visualizations  
✅ Two professional formats (D3.js, Cytoscape.js)  
✅ No server required  
✅ Browser-based interaction  
✅ Customizable dimensions and titles  
✅ Comprehensive testing (16 tests)  
✅ CLI integration (`grai visualize`)  
✅ Perfect for documentation and analysis

Create beautiful, interactive visualizations with a single command!

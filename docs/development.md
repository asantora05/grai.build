# Development Setup

Guide for setting up grai.build for local development.

---

## Prerequisites

- **Python 3.11+**
- **Git**
- **Neo4j** (for testing, optional)

---

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/asantora05/grai.build.git
cd grai.build
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or manually install dev tools
pip install pytest pytest-cov black ruff mypy pre-commit
```

### 4. Install Pre-commit Hooks

```bash
pre-commit install
```

---

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=grai --cov-report=html

# Specific test file
pytest tests/test_validator.py

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## Code Quality

### Formatting

```bash
# Format code
black grai/ tests/

# Check formatting
black --check grai/ tests/
```

### Linting

```bash
# Run linter
ruff check grai/ tests/

# Auto-fix issues
ruff check --fix grai/ tests/
```

### Type Checking

```bash
# Run mypy
mypy grai/
```

---

## Documentation

### Build Docs Locally

```bash
# Install docs dependencies
pip install -r requirements-docs.txt

# Serve locally
mkdocs serve

# Open http://localhost:8000
```

### Build Static Site

```bash
mkdocs build
```

---

## Testing with Neo4j

### Using Docker

```bash
# Start Neo4j
docker run -d \
  --name neo4j-dev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/devpassword \
  neo4j:latest

# Stop Neo4j
docker stop neo4j-dev

# Remove container
docker rm neo4j-dev
```

### Connection Details

- **URI:** `bolt://localhost:7687`
- **User:** `neo4j`
- **Password:** `devpassword`
- **Browser:** `http://localhost:7474`

---

## Project Structure

```
grai.build/
├── grai/                    # Main package
│   ├── __init__.py
│   ├── cli/                # CLI commands
│   ├── core/               # Core functionality
│   │   ├── models.py       # Pydantic models
│   │   ├── parser/         # YAML parsing
│   │   ├── validator/      # Schema validation
│   │   ├── compiler/       # Cypher generation
│   │   ├── loader/         # Neo4j & data loading
│   │   ├── lineage/        # Lineage tracking
│   │   └── visualizer/     # Visualizations
│   └── templates/          # Project templates
├── tests/                   # Test suite
├── docs/                    # MkDocs documentation
├── pyproject.toml          # Project config
└── README.md
```

---

## Common Tasks

### Create a New Feature

```bash
# Create branch
git checkout -b feat/my-feature

# Make changes
# ...

# Run tests
pytest

# Format and lint
black grai/ tests/
ruff check --fix grai/ tests/

# Commit
git add .
git commit -m "feat: Add my feature"

# Push
git push origin feat/my-feature
```

### Add a New Test

```python
# tests/test_myfeature.py
import pytest
from grai.core.mymodule import my_function

def test_my_function():
    """Test that my_function works correctly."""
    result = my_function("input")
    assert result == "expected output"
```

### Update Documentation

```bash
# Edit docs
vim docs/my-page.md

# Preview locally
mkdocs serve

# Commit changes
git add docs/
git commit -m "docs: Update my-page documentation"
```

---

## Troubleshooting

### Import Errors

```bash
# Make sure package is installed in editable mode
pip install -e .
```

### Pre-commit Hook Failures

```bash
# Run hooks manually to see errors
pre-commit run --all-files

# Fix issues and try again
black grai/ tests/
ruff check --fix grai/ tests/
```

### Test Failures

```bash
# Run with verbose output
pytest -v

# Run specific failing test
pytest tests/test_file.py::test_name -v
```

---

## IDE Setup

### VS Code

Recommended extensions:

- Python
- Pylance
- Black Formatter
- Ruff

Settings (`.vscode/settings.json`):

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. Set Python interpreter to venv
2. Enable Black as formatter
3. Configure Ruff for linting

---

## Getting Help

- Read the [Contributing Guide](https://github.com/asantora05/grai.build/blob/main/CONTRIBUTING.md)
- Ask on [GitHub Discussions](https://github.com/asantora05/grai.build/discussions)
- Check [Troubleshooting](troubleshooting.md)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://github.com/asantora05/grai.build/blob/main/CODE_OF_CONDUCT.md). Please be respectful and inclusive.

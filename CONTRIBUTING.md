# Contributing to grai.build

Thank you for your interest in contributing to grai.build! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Neo4j (optional, for integration testing)

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/grai.build.git
cd grai.build
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in editable mode with dev dependencies**

```bash
pip install -e ".[dev]"
```

4. **Verify installation**

```bash
grai --version
pytest
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=grai --cov-report=term-missing

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_parse_entity
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Aim for >80% code coverage
- Use descriptive test names that explain what is being tested

Example:

```python
def test_entity_validation_fails_with_invalid_property_type():
    """Test that entity validation fails when property has invalid type."""
    # Test implementation
```

## 🎨 Code Style

We use automated formatters and linters to maintain code quality:

### Formatting

```bash
# Format code with Black
black grai/

# Check formatting without changes
black --check grai/
```

### Linting

```bash
# Lint with Ruff
ruff check grai/

# Auto-fix issues
ruff check --fix grai/
```

### Type Checking

```bash
# Type check with mypy
mypy grai/
```

### Pre-commit Checks

Before committing, ensure:

```bash
# All tests pass
pytest

# Code is formatted
black --check grai/

# No lint errors
ruff check grai/

# Type hints are correct
mypy grai/
```

## 📝 Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(compiler): Add support for relationship properties
fix(validator): Correct circular dependency detection
docs(readme): Update installation instructions
test(parser): Add tests for YAML error handling
```

## 🔄 Pull Request Process

1. **Create a feature branch**

```bash
git checkout -b feat/your-feature-name
```

2. **Make your changes**

   - Write code
   - Add tests
   - Update documentation

3. **Ensure quality**

```bash
pytest
black grai/
ruff check grai/
```

4. **Commit your changes**

```bash
git add .
git commit -m "feat(scope): description"
```

5. **Push to your fork**

```bash
git push origin feat/your-feature-name
```

6. **Open a Pull Request**
   - Use the PR template
   - Link related issues
   - Describe your changes clearly
   - Request review

### PR Checklist

- [ ] Tests pass locally
- [ ] Code is formatted (Black)
- [ ] Code is linted (Ruff)
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] PR description is complete

## 🏗️ Project Structure

```
grai.build/
├── grai/                   # Main package
│   ├── cli/                # CLI commands
│   │   └── main.py         # Typer app
│   ├── core/               # Core modules
│   │   ├── models.py       # Pydantic models
│   │   ├── parser/         # YAML parsing
│   │   ├── validator/      # Schema validation
│   │   ├── compiler/       # Cypher generation
│   │   ├── loader/         # Neo4j execution
│   │   ├── cache/          # Build caching
│   │   ├── lineage/        # Lineage tracking
│   │   ├── visualizer/     # Graph visualization
│   │   └── exporter/       # IR export
│   └── templates/          # Project templates
├── tests/                  # Test suite
├── docs/                   # Documentation
├── templates/              # Example projects
└── pyproject.toml          # Package config
```

## 📚 Documentation

### Docstrings

Use Google-style docstrings:

```python
def compile_entity(entity: Entity, schema_only: bool = False) -> str:
    """
    Compile an entity into Cypher statements.

    Args:
        entity: The entity to compile.
        schema_only: If True, only generate constraints/indexes.

    Returns:
        str: Generated Cypher statements.

    Raises:
        CompilerError: If entity cannot be compiled.

    Example:
        >>> entity = Entity(name="User", keys=["id"])
        >>> cypher = compile_entity(entity, schema_only=True)
    """
```

### Type Hints

Always include type hints:

```python
from typing import Optional, List

def parse_entities(directory: Path) -> List[Entity]:
    """Parse all entity YAML files in directory."""
    ...
```

## 🐛 Reporting Bugs

When reporting bugs, include:

1. **Description** - Clear description of the issue
2. **Steps to Reproduce** - Minimal steps to reproduce
3. **Expected Behavior** - What should happen
4. **Actual Behavior** - What actually happens
5. **Environment** - OS, Python version, grai version
6. **Logs/Screenshots** - Any relevant output

## 💡 Feature Requests

When requesting features:

1. **Use Case** - Describe the problem you're solving
2. **Proposed Solution** - How you think it should work
3. **Alternatives** - Other solutions you've considered
4. **Examples** - Show how it would be used

## 🎯 Areas for Contribution

### Good First Issues

- Documentation improvements
- Adding examples
- Writing tests for existing code
- Fixing typos or formatting

### Intermediate

- Adding new CLI commands
- Improving error messages
- Adding validation rules
- Performance optimizations

### Advanced

- Supporting new graph databases (Gremlin, etc.)
- Schema versioning/migrations
- Advanced lineage features
- Query optimization

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/asantora05/grai.build/issues)
- **Discussions**: [GitHub Discussions](https://github.com/asantora05/grai.build/discussions)
- **Email**: andrew@grai.build (for sensitive issues)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:

- GitHub contributors page
- Release notes
- Project README

Thank you for making grai.build better! 🎉

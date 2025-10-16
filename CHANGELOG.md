# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub issue templates (bug report, feature request, documentation, question)
- Community health files (CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md)
- Documentation index page (docs/index.md)

### Changed
- Reorganized documentation structure (moved internal docs to `.github/internal-docs/`)
- Renamed all user-facing docs to lowercase with hyphens (MkDocs convention)
- Improved version management (removed hardcoded fallback version)

### Removed
- Duplicate documentation files (CLI.md, SOURCE_CONFIG.md)

## [0.3.2] - 2025-10-15

### Changed
- Improved dynamic version management in `grai/__init__.py`
- Removed hardcoded version fallback for cleaner version handling
- Version now only defined in `pyproject.toml` (single source of truth)

### Fixed
- Version test is now version-agnostic (no hardcoded version checks)

## [0.3.1] - 2025-10-15

### Changed
- Updated package metadata: author changed from personal name to "grai.build"
- Updated LICENSE copyright to "grai.build"
- Replaced personal file paths with generic placeholders in documentation

### Fixed
- Removed personal information from all public package metadata

## [0.3.0] - 2025-10-15

### Added
- Interactive graph visualization with D3.js and Cytoscape.js
- `grai visualize` command for generating HTML visualizations
- Lineage tracking and dependency analysis
- `grai lineage` command for analyzing data flow
- Impact analysis with scoring (none/low/medium/high)
- Build cache for incremental builds (50x faster)
- `grai cache` command for cache management
- Graph IR export to JSON format
- `grai export` command
- Enhanced source configuration support (database, CSV, API, stream, etc.)
- Mermaid and Graphviz visualization export
- Documentation generation for all major features

### Changed
- Improved CLI output with rich formatting and tables
- Enhanced validator with circular dependency detection
- Optimized compiler for better performance
- Codecov configuration (disabled patch coverage requirement)

### Fixed
- GitHub Actions release workflow permissions
- Neo4j loader connection handling
- Parser error messages with better context

## [0.2.0] - 2025-10-14

### Added
- Neo4j loader for executing Cypher scripts
- `grai run` command with dry-run mode
- Connection management with retry logic
- Database metadata queries
- Transaction support with commit/rollback
- Execution result tracking with metrics

### Changed
- Improved CLI with verbose and quiet modes
- Enhanced error messages with file paths
- Better validation error reporting

## [0.1.0] - 2025-10-13

### Added
- Core Pydantic models (Entity, Relation, Property, Project)
- YAML parser for entity and relation definitions
- Schema validator with reference checking
- Cypher compiler for Neo4j
- CLI commands: `init`, `validate`, `build`, `compile`, `info`
- Project scaffolding with example files
- Comprehensive test suite (200+ tests)
- Documentation (README, guides, examples)
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks (Black, Ruff, YAML validation)
- MIT License

### Features
- Declarative YAML-based graph modeling
- Type-safe validation with Pydantic
- Automatic Cypher generation
- Project templates and examples
- Command-line interface with Typer
- Rich terminal output

---

## Release Process

1. Update CHANGELOG.md with changes in `[Unreleased]`
2. Move `[Unreleased]` items to new version section with date
3. Update version in `pyproject.toml`
4. Commit: `git commit -m "chore: bump version to X.Y.Z"`
5. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. Push: `git push && git push origin vX.Y.Z`
7. GitHub Actions automatically publishes to PyPI

## Version Scheme

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

Current status: **Pre-1.0** (API may change)

## Links

- [PyPI Package](https://pypi.org/project/grai-build/)
- [GitHub Repository](https://github.com/asantora05/grai.build)
- [Documentation](https://github.com/asantora05/grai.build/tree/main/docs)
- [Issue Tracker](https://github.com/asantora05/grai.build/issues)

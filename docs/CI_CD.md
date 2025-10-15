# CI/CD Pipeline Documentation

This document describes the CI/CD infrastructure for grai.build.

## 📋 Overview

grai.build uses GitHub Actions for continuous integration and deployment. Our pipeline includes:

- ✅ **Continuous Integration** - Automated testing and validation
- 🔒 **Security Scanning** - Dependency and code security checks
- 📦 **Release Automation** - Automated PyPI publishing
- 📚 **Documentation Building** - Example docs generation

## 🔄 Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:** Push to `main`/`develop`, Pull Requests

**Jobs:**

#### Test

- Runs on Python 3.11 and 3.12
- Executes full test suite with pytest
- Generates coverage report
- Uploads coverage to Codecov

#### Lint

- Checks code formatting with Black
- Lints code with Ruff
- Type checks with mypy (non-blocking)

#### Validate

- Builds the package
- Validates with twine
- Tests CLI installation and availability

#### Integration

- Spins up Neo4j 5.15 container
- Tests full workflow:
  - `grai init`
  - `grai validate`
  - `grai build`
  - `grai run` (with Neo4j)
  - `grai docs`
- Verifies generated documentation files

**Status Badge:**

```markdown
![CI](https://github.com/asantora05/grai.build/workflows/CI/badge.svg)
```

### 2. Release Workflow (`.github/workflows/release.yml`)

**Triggers:**

- Git tags matching `v*.*.*` (e.g., `v0.3.0`)
- Manual workflow dispatch

**Jobs:**

#### Test

- Runs full test suite before release

#### Build

- Builds source and wheel distributions
- Validates with twine
- Uploads artifacts

#### Publish to Test PyPI

- Publishes to test.pypi.org first
- Allows verification before production
- Uses `TEST_PYPI_API_TOKEN` secret

#### Publish to PyPI

- Publishes to pypi.org
- Only runs after Test PyPI succeeds
- Uses `PYPI_API_TOKEN` secret

#### Create GitHub Release

- Creates GitHub release with notes
- Attaches distribution files
- Auto-generates release notes

**Creating a Release:**

```bash
# Update version in pyproject.toml
vim pyproject.toml

# Commit version bump
git add pyproject.toml
git commit -m "chore: bump version to 0.3.0"
git push

# Create and push tag
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0
```

### 3. Security Workflow (`.github/workflows/security.yml`)

**Triggers:**

- Push to `main`
- Pull Requests
- Weekly schedule (Mondays at 00:00 UTC)

**Jobs:**

#### Dependency Scan

- Runs `safety` check on dependencies
- Runs `pip-audit` for known vulnerabilities
- Continues on error (informational)

#### Code Scan

- Runs Bandit security scanner
- Checks for common security issues
- Uploads scan report as artifact

#### CodeQL Analysis

- GitHub's semantic code analysis
- Scans for security vulnerabilities
- Checks code quality issues

### 4. Documentation Workflow (`.github/workflows/docs.yml`)

**Triggers:**

- Push to `main` (when docs/ or grai/ changes)
- Manual workflow dispatch

**Jobs:**

#### Build Example Docs

- Creates example project with `grai init`
- Generates documentation with `grai docs`
- Uploads as artifact

_Note: GitHub Pages deployment is commented out - can be enabled when needed._

## 🔐 Required Secrets

To enable full CI/CD, configure these secrets in GitHub Settings → Secrets and variables → Actions:

### PyPI Publishing

1. **`PYPI_API_TOKEN`**

   - Go to https://pypi.org/manage/account/token/
   - Create new API token
   - Scope: Project (grai-build)
   - Add to GitHub secrets

2. **`TEST_PYPI_API_TOKEN`**
   - Go to https://test.pypi.org/manage/account/token/
   - Create new API token
   - Scope: Project (grai-build)
   - Add to GitHub secrets

### Codecov (Optional)

3. **`CODECOV_TOKEN`**
   - Go to https://codecov.io/
   - Add repository
   - Copy upload token
   - Add to GitHub secrets

## 📊 Status Badges

Add these to your README:

```markdown
[![CI](https://github.com/asantora05/grai.build/workflows/CI/badge.svg)](https://github.com/asantora05/grai.build/actions/workflows/ci.yml)
[![Release](https://github.com/asantora05/grai.build/workflows/Release/badge.svg)](https://github.com/asantora05/grai.build/actions/workflows/release.yml)
[![Security](https://github.com/asantora05/grai.build/workflows/Security/badge.svg)](https://github.com/asantora05/grai.build/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/asantora05/grai.build/branch/main/graph/badge.svg)](https://codecov.io/gh/asantora05/grai.build)
[![PyPI version](https://badge.fury.io/py/grai-build.svg)](https://badge.fury.io/py/grai-build)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
```

## 🤖 Dependabot

Dependabot is configured in `.github/dependabot.yml` to automatically:

- Check Python dependencies weekly
- Check GitHub Actions weekly
- Create PRs for updates
- Automatically label and commit with conventional format

**Reviewing Dependabot PRs:**

1. Check CI passes
2. Review changelog/release notes
3. Test locally if breaking changes
4. Merge when safe

## 🚀 Deployment Process

### Releasing a New Version

1. **Prepare Release**

   ```bash
   # Update version
   vim pyproject.toml  # Change version = "0.3.0"

   # Update CHANGELOG (if you maintain one)
   vim CHANGELOG.md

   # Commit
   git add pyproject.toml
   git commit -m "chore: bump version to 0.3.0"
   ```

2. **Tag Release**

   ```bash
   git tag -a v0.3.0 -m "Release v0.3.0

   Features:
   - Added documentation generation
   - Improved lineage tracking

   Fixes:
   - Fixed schema-only mode
   "
   ```

3. **Push Tag**

   ```bash
   git push origin main
   git push origin v0.3.0
   ```

4. **Monitor Workflow**

   - Go to Actions tab
   - Watch Release workflow
   - Verify Test PyPI upload
   - Verify PyPI upload
   - Check GitHub Release created

5. **Verify Release**
   ```bash
   # Test installation from PyPI
   pip install --upgrade grai-build
   grai --version
   ```

### Hotfix Process

For urgent fixes:

```bash
# Create hotfix branch
git checkout -b hotfix/critical-bug main

# Make fix
vim grai/core/validator/validator.py
git add .
git commit -m "fix: resolve critical validation bug"

# Update version (patch bump)
vim pyproject.toml  # 0.3.0 → 0.3.1
git add pyproject.toml
git commit -m "chore: bump version to 0.3.1"

# Merge to main
git checkout main
git merge hotfix/critical-bug

# Tag and push
git tag -a v0.3.1 -m "Hotfix v0.3.1"
git push origin main --tags
```

## 🧪 Testing CI Locally

### Using Act

Test GitHub Actions locally with [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow
act push

# Run specific job
act -j test

# Run with secrets
act --secret-file .secrets
```

### Manual Testing

Before pushing:

```bash
# Run all checks locally
pytest --cov=grai --cov-report=term-missing
black --check grai/
ruff check grai/
mypy grai/

# Build package
python -m build
twine check dist/*

# Test installation
pip install dist/*.whl
grai --version
```

## 📈 Monitoring

### Check Workflow Status

```bash
# Using GitHub CLI
gh run list
gh run view [run-id]
gh run watch
```

### View Logs

```bash
# Download logs
gh run download [run-id]

# View specific job
gh run view [run-id] --log
```

## 🔧 Troubleshooting

### CI Failures

**Tests Fail:**

- Check test logs in Actions tab
- Run tests locally: `pytest -v`
- Check for environment differences

**Linting Fails:**

- Run locally: `black grai/ && ruff check grai/`
- Fix issues and commit

**Integration Tests Fail:**

- Check Neo4j container logs
- Verify connection strings
- Test locally with Docker

### Release Failures

**PyPI Upload Fails:**

- Check API token is valid
- Verify version doesn't already exist
- Check package metadata with `twine check`

**Tag Already Exists:**

```bash
# Delete local tag
git tag -d v0.3.0

# Delete remote tag
git push origin :refs/tags/v0.3.0

# Recreate and push
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0
```

## 📝 Best Practices

1. **Always run tests locally before pushing**
2. **Keep workflows DRY** - Use reusable workflows when possible
3. **Use caching** - Cache pip dependencies for faster builds
4. **Fail fast** - Run quick jobs (lint) before slow jobs (integration tests)
5. **Monitor secrets** - Rotate API tokens regularly
6. **Review Dependabot PRs** - Don't blindly merge
7. **Tag semantically** - Follow semantic versioning

## 🔮 Future Improvements

- [ ] Add performance benchmarking
- [ ] Set up GitHub Pages for docs
- [ ] Add Docker image builds
- [ ] Add pre-commit hooks
- [ ] Add changelog generation
- [ ] Add release notes automation
- [ ] Add matrix testing for Neo4j versions
- [ ] Add nightly builds
- [ ] Add canary releases

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

"""
Tests for the CLI module.

This module tests the Typer-based command-line interface.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from grai.cli.main import app

runner = CliRunner()


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_help_command(self):
        """Test that --help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "grai" in result.stdout.lower()
        assert "Declarative knowledge graph" in result.stdout

    def test_version_command(self):
        """Test that --version works."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    def test_commands_registered(self):
        """Test that all commands are registered."""
        result = runner.invoke(app, ["--help"])
        assert "init" in result.stdout
        assert "validate" in result.stdout
        assert "build" in result.stdout
        assert "compile" in result.stdout
        assert "run" in result.stdout
        assert "info" in result.stdout


class TestInitCommand:
    """Test the init command."""

    def test_init_creates_project(self, tmp_path):
        """Test that init creates a project structure."""
        project_dir = tmp_path / "test-project"
        result = runner.invoke(app, ["init", str(project_dir), "--name", "test-graph"])
        
        assert result.exit_code == 0
        assert project_dir.exists()
        assert (project_dir / "grai.yml").exists()
        assert (project_dir / "entities").exists()
        assert (project_dir / "relations").exists()
        assert (project_dir / "README.md").exists()

    def test_init_creates_example_files(self, tmp_path):
        """Test that init creates example entity and relation files."""
        project_dir = tmp_path / "test-project"
        result = runner.invoke(app, ["init", str(project_dir)])
        
        assert (project_dir / "entities" / "customer.yml").exists()
        assert (project_dir / "entities" / "product.yml").exists()
        assert (project_dir / "relations" / "purchased.yml").exists()

    def test_init_project_name_in_config(self, tmp_path):
        """Test that project name is set in grai.yml."""
        project_dir = tmp_path / "test-project"
        result = runner.invoke(app, ["init", str(project_dir), "--name", "my-custom-name"])
        
        grai_yml = (project_dir / "grai.yml").read_text()
        assert "my-custom-name" in grai_yml

    def test_init_fails_if_exists(self, tmp_path):
        """Test that init fails if directory exists without --force."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        
        result = runner.invoke(app, ["init", str(project_dir)])
        assert result.exit_code == 1
        assert "already exists" in result.stdout.lower()

    def test_init_with_force_overwrites(self, tmp_path):
        """Test that init with --force overwrites existing files."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / "grai.yml").write_text("old content")
        
        result = runner.invoke(app, ["init", str(project_dir), "--force"])
        assert result.exit_code == 0
        
        grai_yml = (project_dir / "grai.yml").read_text()
        assert "old content" not in grai_yml


class TestValidateCommand:
    """Test the validate command."""

    def test_validate_valid_project(self, tmp_path):
        """Test validating a valid project."""
        # Create a valid project
        runner.invoke(app, ["init", str(tmp_path / "valid-project")])
        
        result = runner.invoke(app, ["validate", str(tmp_path / "valid-project")])
        assert result.exit_code == 0
        assert "✓" in result.stdout or "passed" in result.stdout.lower()

    def test_validate_missing_project(self, tmp_path):
        """Test validating a non-existent project."""
        result = runner.invoke(app, ["validate", str(tmp_path / "nonexistent")])
        assert result.exit_code == 1

    def test_validate_verbose_output(self, tmp_path):
        """Test validate with --verbose flag."""
        runner.invoke(app, ["init", str(tmp_path / "test-project")])
        
        result = runner.invoke(app, ["validate", str(tmp_path / "test-project"), "--verbose"])
        assert result.exit_code == 0


class TestBuildCommand:
    """Test the build command."""

    def test_build_creates_output(self, tmp_path):
        """Test that build creates compiled output."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["build", str(project_dir)])
        assert result.exit_code == 0
        
        output_file = project_dir / "target" / "neo4j" / "compiled.cypher"
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "MERGE" in content
        assert "customer" in content

    def test_build_custom_output_dir(self, tmp_path):
        """Test build with custom output directory."""
        project_dir = tmp_path / "test-project"
        output_dir = tmp_path / "custom-output"
        
        runner.invoke(app, ["init", str(project_dir)])
        result = runner.invoke(app, ["build", str(project_dir), "--output", str(output_dir)])
        
        assert result.exit_code == 0
        assert (output_dir / "compiled.cypher").exists()

    def test_build_custom_filename(self, tmp_path):
        """Test build with custom filename."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["build", str(project_dir), "--filename", "my-graph.cypher"])
        assert result.exit_code == 0
        assert (project_dir / "target" / "neo4j" / "my-graph.cypher").exists()

    def test_build_schema_only(self, tmp_path):
        """Test build with --schema-only flag."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["build", str(project_dir), "--schema-only"])
        assert result.exit_code == 0
        
        output = (project_dir / "target" / "neo4j" / "compiled.cypher").read_text()
        assert "CREATE CONSTRAINT" in output or "CREATE INDEX" in output

    def test_build_skip_validation(self, tmp_path):
        """Test build with --skip-validation."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["build", str(project_dir), "--skip-validation"])
        assert result.exit_code == 0

    def test_build_verbose(self, tmp_path):
        """Test build with --verbose flag."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["build", str(project_dir), "--verbose"])
        assert result.exit_code == 0
        assert "Build Summary" in result.stdout or "Entities" in result.stdout


class TestCompileCommand:
    """Test the compile command."""

    def test_compile_is_alias_for_build(self, tmp_path):
        """Test that compile works as an alias."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["compile", str(project_dir)])
        assert result.exit_code == 0
        
        output_file = project_dir / "target" / "neo4j" / "compiled.cypher"
        assert output_file.exists()


class TestInfoCommand:
    """Test the info command."""

    def test_info_shows_project_details(self, tmp_path):
        """Test that info shows project information."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir), "--name", "my-test-graph"])
        
        result = runner.invoke(app, ["info", str(project_dir)])
        assert result.exit_code == 0
        assert "my-test-graph" in result.stdout
        assert "Entities" in result.stdout
        assert "Relations" in result.stdout

    def test_info_shows_entity_table(self, tmp_path):
        """Test that info shows entity table."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["info", str(project_dir)])
        assert "customer" in result.stdout
        assert "product" in result.stdout

    def test_info_shows_relation_table(self, tmp_path):
        """Test that info shows relation table."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(app, ["info", str(project_dir)])
        assert "PURCHASED" in result.stdout

    def test_info_missing_project(self, tmp_path):
        """Test info on non-existent project."""
        result = runner.invoke(app, ["info", str(tmp_path / "nonexistent")])
        assert result.exit_code == 1


class TestCLIIntegration:
    """Test full CLI workflows."""

    def test_full_workflow(self, tmp_path):
        """Test complete workflow: init -> validate -> build -> info."""
        project_dir = tmp_path / "workflow-test"
        
        # Init
        result = runner.invoke(app, ["init", str(project_dir), "--name", "workflow-graph"])
        assert result.exit_code == 0
        
        # Validate
        result = runner.invoke(app, ["validate", str(project_dir)])
        assert result.exit_code == 0
        
        # Build
        result = runner.invoke(app, ["build", str(project_dir)])
        assert result.exit_code == 0
        
        # Info
        result = runner.invoke(app, ["info", str(project_dir)])
        assert result.exit_code == 0
        assert "workflow-graph" in result.stdout

    def test_validate_then_build(self, tmp_path):
        """Test that validate followed by build works."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        # Validate first
        result1 = runner.invoke(app, ["validate", str(project_dir)])
        assert result1.exit_code == 0
        
        # Then build
        result2 = runner.invoke(app, ["build", str(project_dir)])
        assert result2.exit_code == 0


class TestRunCommand:
    """Test the run command."""

    def test_run_dry_run_mode(self, tmp_path):
        """Test that dry-run mode shows what would be executed."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        runner.invoke(app, ["build", str(project_dir)])
        
        result = runner.invoke(
            app,
            [
                "run",
                str(project_dir),
                "--dry-run",
                "--password", "test",
                "--skip-build",
            ]
        )
        
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert "bolt://localhost:7687" in result.stdout
        assert "compiled.cypher" in result.stdout

    def test_run_missing_cypher_file(self, tmp_path):
        """Test run fails when Cypher file doesn't exist."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        
        result = runner.invoke(
            app,
            [
                "run",
                str(project_dir),
                "--skip-build",
                "--password", "test",
            ]
        )
        
        assert result.exit_code == 1
        assert "Cypher file not found" in result.stdout

    def test_run_skip_build(self, tmp_path):
        """Test run with --skip-build flag."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        runner.invoke(app, ["build", str(project_dir)])
        
        # Mock the loader functions
        from unittest.mock import patch, MagicMock
        
        mock_driver = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.statements_executed = 5
        mock_result.records_affected = 10
        mock_result.execution_time = 1.23
        mock_result.errors = []
        
        with patch('grai.core.loader.connect_neo4j', return_value=mock_driver), \
             patch('grai.core.loader.verify_connection', return_value=True), \
             patch('grai.core.loader.execute_cypher_file', return_value=mock_result), \
             patch('grai.core.loader.close_connection'), \
             patch('grai.core.loader.get_database_info', return_value={}):
            
            result = runner.invoke(
                app,
                [
                    "run",
                    str(project_dir),
                    "--skip-build",
                    "--password", "test",
                ]
            )
        
        assert result.exit_code == 0
        assert "Successfully loaded data into Neo4j" in result.stdout

    def test_run_with_custom_connection(self, tmp_path):
        """Test run with custom connection parameters."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        runner.invoke(app, ["build", str(project_dir)])
        
        from unittest.mock import patch, MagicMock
        
        mock_driver = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.statements_executed = 3
        mock_result.records_affected = 6
        mock_result.execution_time = 0.5
        mock_result.errors = []
        
        with patch('grai.core.loader.connect_neo4j', return_value=mock_driver) as mock_connect, \
             patch('grai.core.loader.verify_connection', return_value=True), \
             patch('grai.core.loader.execute_cypher_file', return_value=mock_result), \
             patch('grai.core.loader.close_connection'), \
             patch('grai.core.loader.get_database_info', return_value={}):
            
            result = runner.invoke(
                app,
                [
                    "run",
                    str(project_dir),
                    "--skip-build",
                    "--uri", "bolt://custom:7687",
                    "--user", "admin",
                    "--password", "secret",
                    "--database", "testdb",
                ]
            )
            
            # Verify connection was called with correct parameters
            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args[1]
            assert call_kwargs['uri'] == "bolt://custom:7687"
            assert call_kwargs['user'] == "admin"
            assert call_kwargs['password'] == "secret"
            assert call_kwargs['database'] == "testdb"
        
        assert result.exit_code == 0

    def test_run_execution_failure(self, tmp_path):
        """Test run handles execution failures."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        runner.invoke(app, ["build", str(project_dir)])
        
        from unittest.mock import patch, MagicMock
        
        mock_driver = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.errors = ["Syntax error in Cypher", "Connection lost"]
        
        with patch('grai.core.loader.connect_neo4j', return_value=mock_driver), \
             patch('grai.core.loader.verify_connection', return_value=True), \
             patch('grai.core.loader.execute_cypher_file', return_value=mock_result), \
             patch('grai.core.loader.close_connection'), \
             patch('grai.core.loader.get_database_info', return_value={}):
            
            result = runner.invoke(
                app,
                [
                    "run",
                    str(project_dir),
                    "--skip-build",
                    "--password", "test",
                ]
            )
        
        assert result.exit_code == 1
        assert "Execution failed" in result.stdout
        assert "Syntax error in Cypher" in result.stdout

    def test_run_connection_failure(self, tmp_path):
        """Test run handles connection failures."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        runner.invoke(app, ["build", str(project_dir)])
        
        from unittest.mock import patch
        
        with patch('grai.core.loader.connect_neo4j', side_effect=Exception("Connection refused")):
            result = runner.invoke(
                app,
                [
                    "run",
                    str(project_dir),
                    "--skip-build",
                    "--password", "test",
                ]
            )
        
        assert result.exit_code == 1
        assert "Connection failed" in result.stdout
        assert "Troubleshooting tips" in result.stdout

    def test_run_verbose_mode(self, tmp_path):
        """Test run with verbose output."""
        project_dir = tmp_path / "test-project"
        runner.invoke(app, ["init", str(project_dir)])
        runner.invoke(app, ["build", str(project_dir)])
        
        from unittest.mock import patch, MagicMock
        
        mock_driver = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.statements_executed = 2
        mock_result.records_affected = 4
        mock_result.execution_time = 0.8
        mock_result.errors = []
        
        mock_db_info = {
            'node_count': 100,
            'relationship_count': 50,
            'labels': ['Customer', 'Product'],
        }
        
        with patch('grai.core.loader.connect_neo4j', return_value=mock_driver), \
             patch('grai.core.loader.verify_connection', return_value=True), \
             patch('grai.core.loader.execute_cypher_file', return_value=mock_result), \
             patch('grai.core.loader.close_connection'), \
             patch('grai.core.loader.get_database_info', return_value=mock_db_info):
            
            result = runner.invoke(
                app,
                [
                    "run",
                    str(project_dir),
                    "--skip-build",
                    "--password", "test",
                    "--verbose",
                ]
            )
        
        assert result.exit_code == 0
        assert "Database info" in result.stdout
        assert "Nodes:" in result.stdout

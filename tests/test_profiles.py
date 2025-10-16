"""Tests for profile management."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from grai.core.profiles import (
    BigQueryProfile,
    Neo4jProfile,
    SnowflakeProfile,
    create_default_profiles_file,
    get_connection_info,
    get_profile,
    get_profile_path,
    get_profiles_dir,
    get_target_config,
    load_profiles,
    parse_graph_profile,
    parse_warehouse_profile,
    resolve_env_vars,
)


@pytest.fixture
def temp_profiles_dir(monkeypatch, tmp_path):
    """Create a temporary profiles directory."""
    profiles_dir = tmp_path / ".grai"
    profiles_dir.mkdir()
    monkeypatch.setenv("GRAI_PROFILES_DIR", str(profiles_dir))
    return profiles_dir


@pytest.fixture
def sample_profiles(temp_profiles_dir):
    """Create a sample profiles.yml file."""
    profiles_content = {
        "default": {
            "target": "dev",
            "outputs": {
                "dev": {
                    "warehouse": {
                        "type": "bigquery",
                        "method": "oauth",
                        "project": "test-project",
                        "dataset": "analytics",
                        "location": "US",
                    },
                    "graph": {
                        "type": "neo4j",
                        "uri": "bolt://localhost:7687",
                        "user": "neo4j",
                        "password": "testpass",
                    },
                },
                "prod": {
                    "warehouse": {
                        "type": "bigquery",
                        "method": "service-account",
                        "project": "prod-project",
                        "dataset": "analytics_prod",
                        "location": "US",
                        "keyfile": "/path/to/keyfile.json",
                    },
                    "graph": {
                        "type": "neo4j",
                        "uri": "bolt://prod:7687",
                        "user": "neo4j",
                        "password": "prodpass",
                    },
                },
            },
        },
    }

    profile_path = temp_profiles_dir / "profiles.yml"
    with open(profile_path, "w") as f:
        yaml.dump(profiles_content, f)

    return profile_path


def test_get_profiles_dir_default():
    """Test getting default profiles directory."""
    profiles_dir = get_profiles_dir()
    assert profiles_dir == Path.home() / ".grai"


def test_get_profiles_dir_env_var(temp_profiles_dir):
    """Test getting profiles directory from environment variable."""
    profiles_dir = get_profiles_dir()
    assert profiles_dir == temp_profiles_dir


def test_get_profile_path(temp_profiles_dir):
    """Test getting profile path."""
    profile_path = get_profile_path()
    assert profile_path == temp_profiles_dir / "profiles.yml"


def test_create_default_profiles_file(temp_profiles_dir):
    """Test creating default profiles file."""
    profile_path = create_default_profiles_file()
    assert profile_path.exists()
    assert profile_path == temp_profiles_dir / "profiles.yml"

    # Verify it's valid YAML
    with open(profile_path) as f:
        profiles = yaml.safe_load(f)
    assert "default" in profiles
    assert "target" in profiles["default"]
    assert "outputs" in profiles["default"]


def test_load_profiles(sample_profiles):
    """Test loading profiles from file."""
    profiles = load_profiles()
    assert "default" in profiles
    assert profiles["default"]["target"] == "dev"


def test_load_profiles_missing():
    """Test loading profiles when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["GRAI_PROFILES_DIR"] = tmpdir
        with pytest.raises(FileNotFoundError, match="Profile file not found"):
            load_profiles()


def test_get_profile(sample_profiles):
    """Test getting a specific profile."""
    profile = get_profile("default")
    assert profile["target"] == "dev"
    assert "outputs" in profile


def test_get_profile_missing(sample_profiles):
    """Test getting a profile that doesn't exist."""
    with pytest.raises(KeyError, match="Profile 'missing' not found"):
        get_profile("missing")


def test_get_target_config(sample_profiles):
    """Test getting target configuration."""
    config = get_target_config("default", "dev")
    assert "warehouse" in config
    assert "graph" in config
    assert config["warehouse"]["type"] == "bigquery"
    assert config["graph"]["type"] == "neo4j"


def test_get_target_config_default_target(sample_profiles):
    """Test getting target configuration with default target."""
    config = get_target_config("default")  # Should use 'dev' as default
    assert config["warehouse"]["project"] == "test-project"


def test_get_target_config_missing(sample_profiles):
    """Test getting target that doesn't exist."""
    with pytest.raises(KeyError, match="Target 'missing' not found"):
        get_target_config("default", "missing")


def test_parse_bigquery_profile():
    """Test parsing BigQuery profile."""
    config = {
        "type": "bigquery",
        "method": "oauth",
        "project": "test-project",
        "dataset": "analytics",
        "location": "US",
    }
    profile = parse_warehouse_profile(config)
    assert isinstance(profile, BigQueryProfile)
    assert profile.project == "test-project"
    assert profile.method == "oauth"


def test_parse_snowflake_profile():
    """Test parsing Snowflake profile."""
    config = {
        "type": "snowflake",
        "account": "abc123.us-east-1",
        "user": "testuser",
        "password": "testpass",
        "database": "ANALYTICS",
    }
    profile = parse_warehouse_profile(config)
    assert isinstance(profile, SnowflakeProfile)
    assert profile.account == "abc123.us-east-1"


def test_parse_warehouse_profile_unsupported():
    """Test parsing unsupported warehouse type."""
    config = {"type": "redshift"}
    with pytest.raises(ValueError, match="Unsupported warehouse type"):
        parse_warehouse_profile(config)


def test_parse_neo4j_profile():
    """Test parsing Neo4j profile."""
    config = {
        "type": "neo4j",
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "testpass",
    }
    profile = parse_graph_profile(config)
    assert isinstance(profile, Neo4jProfile)
    assert profile.uri == "bolt://localhost:7687"


def test_resolve_env_vars():
    """Test resolving environment variables in config."""
    os.environ["TEST_PROJECT"] = "my-test-project"
    os.environ["TEST_PASSWORD"] = "secret123"

    config = {
        "project": "{{ env_var('TEST_PROJECT') }}",
        "password": "{{ env_var('TEST_PASSWORD') }}",
        "nested": {"key": "{{ env_var('TEST_PROJECT') }}"},
    }

    resolved = resolve_env_vars(config)
    assert resolved["project"] == "my-test-project"
    assert resolved["password"] == "secret123"
    assert resolved["nested"]["key"] == "my-test-project"


def test_resolve_env_vars_missing():
    """Test resolving missing environment variable."""
    config = {"password": "{{ env_var('MISSING_VAR') }}"}

    with pytest.raises(ValueError, match="Environment variable 'MISSING_VAR' is not set"):
        resolve_env_vars(config)


def test_get_connection_info(sample_profiles):
    """Test getting connection info for warehouse and graph."""
    warehouse_profile, graph_profile = get_connection_info("default", "dev")

    assert isinstance(warehouse_profile, BigQueryProfile)
    assert warehouse_profile.project == "test-project"

    assert isinstance(graph_profile, Neo4jProfile)
    assert graph_profile.uri == "bolt://localhost:7687"


def test_get_connection_info_prod(sample_profiles):
    """Test getting connection info for production target."""
    warehouse_profile, graph_profile = get_connection_info("default", "prod")

    assert warehouse_profile.project == "prod-project"
    assert warehouse_profile.keyfile == "/path/to/keyfile.json"
    assert graph_profile.uri == "bolt://prod:7687"


def test_bigquery_profile_validation():
    """Test BigQuery profile validation."""
    # Valid method
    profile = BigQueryProfile(method="oauth", project="test")
    assert profile.method == "oauth"

    # Invalid method
    with pytest.raises(ValueError, match="Invalid method"):
        BigQueryProfile(method="invalid")


def test_profile_with_env_vars(sample_profiles):
    """Test profile with environment variable references."""
    # Add profile with env vars
    profiles = load_profiles()
    profiles["default"]["outputs"]["staging"] = {
        "warehouse": {
            "type": "bigquery",
            "method": "oauth",
            "project": "{{ env_var('GCP_PROJECT') }}",
            "dataset": "analytics",
        },
        "graph": {
            "type": "neo4j",
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "{{ env_var('NEO4J_PASSWORD') }}",
        },
    }

    # Save updated profiles
    profile_path = get_profile_path()
    with open(profile_path, "w") as f:
        yaml.dump(profiles, f)

    # Set environment variables
    os.environ["GCP_PROJECT"] = "staging-project"
    os.environ["NEO4J_PASSWORD"] = "staging-pass"

    # Get connection info
    warehouse_profile, graph_profile = get_connection_info("default", "staging")

    assert warehouse_profile.project == "staging-project"
    assert graph_profile.password == "staging-pass"

"""
Profile management for grai.build connections.

Inspired by dbt's profiles.yml, this module handles connection configurations
for data warehouses (BigQuery, Snowflake, etc.) and graph databases (Neo4j).
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class BigQueryProfile(BaseModel):
    """BigQuery connection profile."""

    type: str = Field(default="bigquery", frozen=True)
    method: str = Field(
        default="oauth",
        description="Authentication method: 'oauth', 'service-account', or 'service-account-json'",
    )
    project: Optional[str] = Field(
        None, description="BigQuery project ID (defaults to gcloud default)"
    )
    dataset: Optional[str] = Field(None, description="Default dataset name")
    location: Optional[str] = Field("US", description="BigQuery location (e.g., 'US', 'EU')")
    keyfile: Optional[str] = Field(None, description="Path to service account JSON keyfile")
    keyfile_json: Optional[Dict[str, Any]] = Field(
        None, description="Service account JSON credentials as dict"
    )
    timeout_seconds: int = Field(300, description="Query timeout in seconds")
    maximum_bytes_billed: Optional[int] = Field(None, description="Maximum bytes billed per query")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate authentication method."""
        valid_methods = ["oauth", "service-account", "service-account-json"]
        if v not in valid_methods:
            raise ValueError(f"Invalid method '{v}'. Must be one of: {', '.join(valid_methods)}")
        return v


class SnowflakeProfile(BaseModel):
    """Snowflake connection profile."""

    type: str = Field(default="snowflake", frozen=True)
    account: str = Field(..., description="Snowflake account identifier")
    user: str = Field(..., description="Snowflake username")
    password: Optional[str] = Field(None, description="Snowflake password")
    role: Optional[str] = Field(None, description="Snowflake role")
    database: Optional[str] = Field(None, description="Default database")
    warehouse: Optional[str] = Field(None, description="Snowflake warehouse")
    schema: Optional[str] = Field(None, description="Default schema")
    authenticator: Optional[str] = Field(
        None, description="Authentication method (e.g., 'externalbrowser')"
    )


class Neo4jProfile(BaseModel):
    """Neo4j connection profile."""

    type: str = Field(default="neo4j", frozen=True)
    uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: Optional[str] = Field(None, description="Neo4j password")
    database: Optional[str] = Field(None, description="Neo4j database name")
    encrypted: bool = Field(True, description="Use encrypted connection")
    trust: str = Field(
        "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
        description="Certificate trust level",
    )


class TargetConfig(BaseModel):
    """Configuration for a specific target (environment)."""

    outputs: Dict[str, Any] = Field(..., description="Output configurations (warehouse + graph)")
    target: str = Field(..., description="Default output to use")


class Profile(BaseModel):
    """Complete profile configuration."""

    config: TargetConfig


def get_profiles_dir() -> Path:
    """
    Get the profiles directory path.

    Checks in order:
    1. GRAI_PROFILES_DIR environment variable
    2. ~/.grai/ directory

    Returns:
        Path to profiles directory
    """
    profiles_dir_env = os.getenv("GRAI_PROFILES_DIR")
    if profiles_dir_env:
        return Path(profiles_dir_env)

    return Path.home() / ".grai"


def get_profile_path() -> Path:
    """
    Get the path to profiles.yml.

    Returns:
        Path to profiles.yml file
    """
    return get_profiles_dir() / "profiles.yml"


def load_profiles() -> Dict[str, Any]:
    """
    Load profiles from profiles.yml.

    Returns:
        Dictionary of profile configurations

    Raises:
        FileNotFoundError: If profiles.yml doesn't exist
        yaml.YAMLError: If profiles.yml is invalid
    """
    profile_path = get_profile_path()

    if not profile_path.exists():
        raise FileNotFoundError(
            f"Profile file not found at {profile_path}. "
            f"Run 'grai init' to create one, or set GRAI_PROFILES_DIR."
        )

    with open(profile_path) as f:
        profiles = yaml.safe_load(f)

    if not profiles:
        raise ValueError(f"Profile file {profile_path} is empty")

    return profiles


def get_profile(profile_name: str) -> Dict[str, Any]:
    """
    Get a specific profile by name.

    Args:
        profile_name: Name of the profile to retrieve

    Returns:
        Profile configuration dictionary

    Raises:
        KeyError: If profile doesn't exist
    """
    profiles = load_profiles()

    if profile_name not in profiles:
        available = ", ".join(profiles.keys())
        raise KeyError(f"Profile '{profile_name}' not found. Available profiles: {available}")

    return profiles[profile_name]


def get_target_config(profile_name: str, target_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get target configuration from a profile.

    Args:
        profile_name: Name of the profile
        target_name: Name of the target (defaults to profile's default target)

    Returns:
        Target configuration dictionary with 'warehouse' and 'graph' outputs

    Raises:
        KeyError: If profile or target doesn't exist
    """
    profile = get_profile(profile_name)

    # Get target name (from arg, env var, or profile default)
    if target_name is None:
        target_name = os.getenv("GRAI_TARGET")

    if target_name is None:
        target_name = profile.get("target")

    if target_name is None:
        raise ValueError(
            f"No target specified for profile '{profile_name}'. "
            f"Set target in profiles.yml or use GRAI_TARGET env var."
        )

    # Get outputs
    outputs = profile.get("outputs", {})
    if target_name not in outputs:
        available = ", ".join(outputs.keys())
        raise KeyError(
            f"Target '{target_name}' not found in profile '{profile_name}'. "
            f"Available targets: {available}"
        )

    return outputs[target_name]


def parse_warehouse_profile(config: Dict[str, Any]) -> Any:
    """
    Parse warehouse configuration into appropriate profile model.

    Args:
        config: Warehouse configuration dictionary

    Returns:
        Profile model (BigQueryProfile, SnowflakeProfile, etc.)

    Raises:
        ValueError: If warehouse type is unsupported
    """
    warehouse_type = config.get("type")

    if warehouse_type == "bigquery":
        return BigQueryProfile(**config)
    elif warehouse_type == "snowflake":
        return SnowflakeProfile(**config)
    else:
        raise ValueError(
            f"Unsupported warehouse type: {warehouse_type}. "
            f"Supported types: bigquery, snowflake"
        )


def parse_graph_profile(config: Dict[str, Any]) -> Neo4jProfile:
    """
    Parse graph database configuration into profile model.

    Args:
        config: Graph database configuration dictionary

    Returns:
        Neo4jProfile model

    Raises:
        ValueError: If graph type is unsupported
    """
    graph_type = config.get("type", "neo4j")

    if graph_type == "neo4j":
        return Neo4jProfile(**config)
    else:
        raise ValueError(
            f"Unsupported graph type: {graph_type}. Currently only 'neo4j' is supported."
        )


def resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve environment variable references in configuration.

    Replaces strings like "{{ env_var('MY_VAR') }}" with environment variable values.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with environment variables resolved
    """
    import re

    def replace_env_var(match: re.Match) -> str:
        var_name = match.group(1)
        value = os.getenv(var_name)
        if value is None:
            raise ValueError(f"Environment variable '{var_name}' is not set")
        return value

    result = {}
    env_var_pattern = re.compile(r"{{\s*env_var\(['\"]([^'\"]+)['\"]\)\s*}}")

    for key, value in config.items():
        if isinstance(value, str):
            result[key] = env_var_pattern.sub(replace_env_var, value)
        elif isinstance(value, dict):
            result[key] = resolve_env_vars(value)
        else:
            result[key] = value

    return result


def create_default_profiles_file() -> Path:
    """
    Create a default profiles.yml file.

    Returns:
        Path to created profiles file
    """
    profiles_dir = get_profiles_dir()
    profiles_dir.mkdir(parents=True, exist_ok=True)

    profile_path = profiles_dir / "profiles.yml"

    default_content = """# grai.build profiles configuration
# Similar to dbt profiles.yml, this file manages connections to data warehouses and graph databases
#
# Environment variables can be referenced using: {{ env_var('VAR_NAME') }}
# Set GRAI_TARGET environment variable to override the default target

default:
  target: dev
  outputs:
    dev:
      # Data warehouse configuration
      warehouse:
        type: bigquery
        method: oauth  # or 'service-account'
        project: "{{ env_var('GCP_PROJECT') }}"
        dataset: analytics
        location: US
        # keyfile: /path/to/service-account.json  # for service-account method
        timeout_seconds: 300

      # Graph database configuration
      graph:
        type: neo4j
        uri: bolt://localhost:7687
        user: neo4j
        password: "{{ env_var('NEO4J_PASSWORD') }}"
        database: neo4j
        encrypted: true

    prod:
      warehouse:
        type: bigquery
        method: service-account
        project: my-prod-project
        dataset: analytics_prod
        location: US
        keyfile: "{{ env_var('GCP_KEYFILE_PATH') }}"
        timeout_seconds: 600

      graph:
        type: neo4j
        uri: "{{ env_var('NEO4J_URI') }}"
        user: neo4j
        password: "{{ env_var('NEO4J_PASSWORD') }}"
        database: neo4j
        encrypted: true

# Example with Snowflake
# snowflake_project:
#   target: dev
#   outputs:
#     dev:
#       warehouse:
#         type: snowflake
#         account: abc12345.us-east-1
#         user: "{{ env_var('SNOWFLAKE_USER') }}"
#         password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
#         role: ANALYST
#         database: ANALYTICS
#         warehouse: COMPUTE_WH
#         schema: PUBLIC
#
#       graph:
#         type: neo4j
#         uri: bolt://localhost:7687
#         user: neo4j
#         password: "{{ env_var('NEO4J_PASSWORD') }}"
"""

    with open(profile_path, "w") as f:
        f.write(default_content)

    return profile_path


def get_connection_info(
    profile_name: str = "default", target_name: Optional[str] = None
) -> tuple[Any, Neo4jProfile]:
    """
    Get warehouse and graph connection info from profiles.

    Args:
        profile_name: Name of the profile to use (defaults to 'default')
        target_name: Name of the target (defaults to profile's default or GRAI_TARGET)

    Returns:
        Tuple of (warehouse_profile, graph_profile)

    Raises:
        FileNotFoundError: If profiles.yml doesn't exist
        KeyError: If profile or target doesn't exist
    """
    target_config = get_target_config(profile_name, target_name)

    # Resolve environment variables
    target_config = resolve_env_vars(target_config)

    # Parse warehouse config
    warehouse_config = target_config.get("warehouse")
    if not warehouse_config:
        raise ValueError(
            f"No warehouse configuration found in target '{target_name}' "
            f"of profile '{profile_name}'"
        )
    warehouse_profile = parse_warehouse_profile(warehouse_config)

    # Parse graph config
    graph_config = target_config.get("graph")
    if not graph_config:
        raise ValueError(
            f"No graph configuration found in target '{target_name}' "
            f"of profile '{profile_name}'"
        )
    graph_profile = parse_graph_profile(graph_config)

    return warehouse_profile, graph_profile

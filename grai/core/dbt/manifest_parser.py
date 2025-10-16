"""
dbt manifest parser for grai.build.

Parses dbt manifest.json files and generates grai.build entity definitions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from grai.core.models import (
    Entity,
    Property,
    PropertyType,
    Relation,
    RelationMapping,
    SourceConfig,
    SourceType,
)


class DbtManifestParser:
    """
    Parser for dbt manifest.json files.

    Converts dbt models into grai.build entity definitions, preserving
    column information, descriptions, and metadata.
    """

    # Map dbt data types to grai.build PropertyType
    TYPE_MAPPING = {
        # Numeric types
        "integer": PropertyType.INTEGER,
        "int": PropertyType.INTEGER,
        "bigint": PropertyType.INTEGER,
        "smallint": PropertyType.INTEGER,
        "tinyint": PropertyType.INTEGER,
        "number": PropertyType.FLOAT,
        "numeric": PropertyType.FLOAT,
        "decimal": PropertyType.FLOAT,
        "float": PropertyType.FLOAT,
        "double": PropertyType.FLOAT,
        "real": PropertyType.FLOAT,
        # String types
        "string": PropertyType.STRING,
        "varchar": PropertyType.STRING,
        "char": PropertyType.STRING,
        "text": PropertyType.STRING,
        # Boolean
        "boolean": PropertyType.BOOLEAN,
        "bool": PropertyType.BOOLEAN,
        # Date/Time
        "date": PropertyType.DATE,
        "datetime": PropertyType.DATETIME,
        "timestamp": PropertyType.DATETIME,
        "time": PropertyType.DATETIME,
        # Complex types
        "json": PropertyType.JSON,
        "jsonb": PropertyType.JSON,
        "array": PropertyType.JSON,
        "struct": PropertyType.JSON,
        "object": PropertyType.JSON,
        "variant": PropertyType.JSON,
    }

    def __init__(self, manifest_data: Dict[str, Any]):
        """
        Initialize parser with manifest data.

        Args:
            manifest_data: Parsed dbt manifest.json dictionary.
        """
        self.manifest = manifest_data
        self.models = {}
        self.sources = {}
        self._extract_nodes()

    def _extract_nodes(self):
        """Extract and categorize nodes from manifest."""
        nodes = self.manifest.get("nodes", {})

        for node_id, node in nodes.items():
            resource_type = node.get("resource_type")

            if resource_type == "model":
                self.models[node_id] = node
            elif resource_type == "source":
                self.sources[node_id] = node

    def parse_models(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> tuple[List[Entity], List[Relation]]:
        """
        Parse dbt models into grai.build entities and relations.

        Models can be marked as relations using the meta field:

        models:
          - name: orders
            meta:
              grai:
                type: relation
                relation_name: PURCHASED
                from_entity: customer
                from_key: customer_id
                to_entity: product
                to_key: product_id

        If not explicitly marked, models with 2+ foreign key tests are treated as relations.
        Other models are treated as entities.

        Args:
            include_patterns: Optional list of model name patterns to include.
            exclude_patterns: Optional list of model name patterns to exclude.

        Returns:
            Tuple of (entities, relations) parsed from dbt models.
        """
        entities = []
        relations = []

        for node_id, model in self.models.items():
            model_name = model.get("name")

            # Apply filters if provided
            if include_patterns and not any(pattern in model_name for pattern in include_patterns):
                continue
            if exclude_patterns and any(pattern in model_name for pattern in exclude_patterns):
                continue

            # Check if model is explicitly marked as a relation in meta
            meta = model.get("meta", {})
            grai_meta = meta.get("grai", {})

            if grai_meta.get("type") == "relation":
                # Explicitly marked as relation - use meta config
                relation = self._model_to_relation_from_meta(model, grai_meta)
                if relation:
                    relations.append(relation)
            else:
                # Check if this model is a relationship table (has 2+ foreign keys)
                foreign_keys = self._extract_foreign_keys(model)

                if len(foreign_keys) >= 2:
                    # This is a relationship table - convert to Relation
                    relation = self._model_to_relation(model, foreign_keys)
                    if relation:
                        relations.append(relation)
                else:
                    # Regular entity
                    entity = self._model_to_entity(model)
                    if entity:
                        entities.append(entity)

        return entities, relations

    def _model_to_entity(self, model: Dict[str, Any]) -> Optional[Entity]:
        """
        Convert a dbt model to a grai.build Entity.

        Args:
            model: dbt model node from manifest.

        Returns:
            Entity object or None if conversion fails.
        """
        try:
            # Extract basic model info
            model_name = model.get("name")
            database = model.get("database", "")
            schema = model.get("schema", "")
            alias = model.get("alias", model_name)
            description = model.get("description", "")

            # Build source configuration
            source_name = f"{schema}.{alias}" if schema else alias
            source = SourceConfig(
                name=source_name,
                type=SourceType.TABLE,
                database=database,
                db_schema=schema,
                metadata={
                    "dbt_model": model_name,
                    "dbt_unique_id": model.get("unique_id"),
                    "dbt_package": model.get("package_name"),
                    "dbt_path": model.get("original_file_path"),
                    "materialization": model.get("config", {}).get("materialized"),
                },
            )

            # Parse columns into properties
            properties = self._parse_columns(model.get("columns", {}))

            # Try to infer keys from tests (unique/primary key tests)
            keys = self._infer_keys(model)

            # Create entity
            entity = Entity(
                entity=model_name,
                source=source,
                keys=keys,
                properties=properties,
                description=description or None,
            )

            return entity

        except Exception as e:
            print(f"Warning: Failed to parse model {model.get('name')}: {e}")
            return None

    def _parse_columns(self, columns: Dict[str, Any]) -> List[Property]:
        """
        Parse dbt columns into grai.build properties.

        Args:
            columns: Dictionary of column definitions from dbt model.

        Returns:
            List of Property objects.
        """
        properties = []

        for col_name, col_data in columns.items():
            # Map dbt data type to grai.build PropertyType
            # Handle None data_type gracefully
            dbt_type = col_data.get("data_type")
            if dbt_type is None:
                dbt_type = "string"  # Default to string if no type specified
            else:
                dbt_type = dbt_type.lower()

            property_type = self._map_type(dbt_type)

            # Create property
            prop = Property(
                name=col_name,
                type=property_type,
                description=col_data.get("description") or None,
            )

            properties.append(prop)

        return properties

    def _map_type(self, dbt_type: str) -> PropertyType:
        """
        Map dbt data type to grai.build PropertyType.

        Args:
            dbt_type: dbt data type string (lowercase).

        Returns:
            Corresponding PropertyType enum value.
        """
        # Try exact match first
        if dbt_type in self.TYPE_MAPPING:
            return self.TYPE_MAPPING[dbt_type]

        # Try partial matches
        for key, value in self.TYPE_MAPPING.items():
            if key in dbt_type:
                return value

        # Default to string
        return PropertyType.STRING

    def _extract_foreign_keys(self, model: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract foreign key relationships from dbt model tests.

        Looks for 'relationships' tests that indicate foreign keys to other models.

        Args:
            model: dbt model node.

        Returns:
            Dictionary mapping column names to referenced model names.
            Example: {"customer_id": "customers", "product_id": "products"}
        """
        foreign_keys = {}
        columns = model.get("columns", {})

        for col_name, col_data in columns.items():
            tests = col_data.get("tests", [])

            for test in tests:
                # Handle dict-style test with 'relationships' key
                if isinstance(test, dict) and "relationships" in test:
                    rel_config = test["relationships"]
                    # Extract the referenced model name
                    to_model = rel_config.get("to") or rel_config.get("model")
                    if to_model:
                        # Clean up model reference (remove 'ref()' wrapper if present)
                        to_model = to_model.replace("ref('", "").replace("')", "").strip()
                        foreign_keys[col_name] = to_model

        return foreign_keys

    def _model_to_relation_from_meta(
        self, model: Dict[str, Any], grai_meta: Dict[str, Any]
    ) -> Optional[Relation]:
        """
        Convert a dbt model to a grai.build Relation using meta configuration.

        Expected meta format:
        meta:
          grai:
            type: relation
            relation_name: PURCHASED
            from_entity: customer
            from_key: customer_id
            to_entity: product
            to_key: product_id

        Args:
            model: dbt model node from manifest.
            grai_meta: grai configuration from model's meta field.

        Returns:
            Relation object or None if conversion fails.
        """
        try:
            # Extract basic model info
            model_name = model.get("name")
            database = model.get("database", "")
            schema = model.get("schema", "")
            alias = model.get("alias", model_name)
            description = model.get("description", "")

            # Extract relation config from meta
            relation_name = grai_meta.get("relation_name", model_name.upper())
            from_entity = grai_meta.get("from_entity")
            from_key = grai_meta.get("from_key")
            to_entity = grai_meta.get("to_entity")
            to_key = grai_meta.get("to_key")

            # Validate required fields
            if not all([from_entity, from_key, to_entity, to_key]):
                print(
                    f"Warning: Model {model_name} marked as relation but missing required meta fields "
                    f"(from_entity, from_key, to_entity, to_key)"
                )
                return None

            # Build source configuration
            source_name = f"{schema}.{alias}" if schema else alias
            source = SourceConfig(
                name=source_name,
                type=SourceType.TABLE,
                database=database,
                db_schema=schema,
                metadata={
                    "dbt_model": model_name,
                    "dbt_unique_id": model.get("unique_id"),
                    "dbt_package": model.get("package_name"),
                    "dbt_path": model.get("original_file_path"),
                    "materialization": model.get("config", {}).get("materialized"),
                    "is_relationship_table": True,
                    "relation_source": "meta",
                },
            )

            # Parse all columns except foreign keys as relation properties
            all_columns = model.get("columns", {})
            property_columns = {
                name: data for name, data in all_columns.items() if name not in [from_key, to_key]
            }
            properties = self._parse_columns(property_columns)

            # Create relation mapping
            mappings = RelationMapping(
                from_key=from_key,
                to_key=to_key,
            )

            # Create relation
            relation = Relation(
                relation=relation_name,
                **{"from": from_entity},  # Use dict unpacking to handle 'from' keyword
                to=to_entity,
                source=source,
                mappings=mappings,
                properties=properties,
                description=description or None,
            )

            return relation

        except Exception as e:
            print(f"Warning: Failed to parse relationship {model.get('name')} from meta: {e}")
            return None

    def _model_to_relation(
        self, model: Dict[str, Any], foreign_keys: Dict[str, str]
    ) -> Optional[Relation]:
        """
        Convert a dbt relationship table model to a grai.build Relation.

        Args:
            model: dbt model node from manifest.
            foreign_keys: Dictionary of foreign key column names to model names.

        Returns:
            Relation object or None if conversion fails.
        """
        try:
            # Extract basic model info
            model_name = model.get("name")
            database = model.get("database", "")
            schema = model.get("schema", "")
            alias = model.get("alias", model_name)
            description = model.get("description", "")

            # Use first two foreign keys for from/to mapping
            fk_items = list(foreign_keys.items())
            from_col, from_entity = fk_items[0]
            to_col, to_entity = fk_items[1]

            # Build source configuration
            source_name = f"{schema}.{alias}" if schema else alias
            source = SourceConfig(
                name=source_name,
                type=SourceType.TABLE,
                database=database,
                db_schema=schema,
                metadata={
                    "dbt_model": model_name,
                    "dbt_unique_id": model.get("unique_id"),
                    "dbt_package": model.get("package_name"),
                    "dbt_path": model.get("original_file_path"),
                    "materialization": model.get("config", {}).get("materialized"),
                    "is_relationship_table": True,
                },
            )

            # Parse all columns except foreign keys as relation properties
            all_columns = model.get("columns", {})
            property_columns = {
                name: data for name, data in all_columns.items() if name not in foreign_keys
            }
            properties = self._parse_columns(property_columns)

            # Create relation name from model name (convert to uppercase)
            relation_name = model_name.upper()

            # Create relation mapping
            mappings = RelationMapping(
                from_key=(
                    from_col.replace(f"_{from_entity.rstrip('s')}_id", "_id")
                    if from_col.endswith("_id")
                    else from_col
                ),
                to_key=(
                    to_col.replace(f"_{to_entity.rstrip('s')}_id", "_id")
                    if to_col.endswith("_id")
                    else to_col
                ),
            )

            # Create relation
            relation = Relation(
                relation=relation_name,
                **{"from": from_entity},  # Use dict unpacking to handle 'from' keyword
                to=to_entity,
                source=source,
                mappings=mappings,
                properties=properties,
                description=description or None,
            )

            return relation

        except Exception as e:
            print(f"Warning: Failed to parse relationship {model.get('name')}: {e}")
            return None

    def _infer_keys(self, model: Dict[str, Any]) -> List[str]:
        """
        Infer entity keys from dbt tests.

        Looks for unique, not_null, and primary key tests to determine
        which columns should be keys. If no unique tests are found,
        uses the first column as a fallback key.

        Args:
            model: dbt model node.

        Returns:
            List of column names that are likely keys (at least 1).
        """
        keys = []
        columns = model.get("columns", {})

        # Check each column for tests
        for col_name, col_data in columns.items():
            tests = col_data.get("tests", [])

            # Look for unique or primary key indicators
            has_unique = False

            for test in tests:
                if isinstance(test, str):
                    test_name = test.lower()
                elif isinstance(test, dict):
                    test_name = list(test.keys())[0].lower() if test else ""
                else:
                    continue

                if "unique" in test_name or "primary_key" in test_name:
                    has_unique = True
                    break  # Found unique test, no need to continue

            # If column is unique, add as key
            if has_unique:
                keys.append(col_name)

        # Fallback: If no keys found, use first column as key
        # This ensures Entity validation passes (requires min 1 key)
        if not keys and columns:
            first_column = next(iter(columns.keys()))
            keys.append(first_column)

        return keys


def parse_dbt_manifest(manifest_data: Dict[str, Any]) -> tuple[List[Entity], List[Relation]]:
    """
    Parse dbt manifest data into grai.build entities and relations.

    Models with 2+ foreign key relationships are treated as relation tables.

    Args:
        manifest_data: Parsed dbt manifest.json dictionary.

    Returns:
        Tuple of (entities, relations).

    Example:
        >>> with open("target/manifest.json") as f:
        ...     manifest = json.load(f)
        >>> entities, relations = parse_dbt_manifest(manifest)
        >>> print(f"Parsed {len(entities)} entities and {len(relations)} relations")
    """
    parser = DbtManifestParser(manifest_data)
    return parser.parse_models()


def parse_dbt_manifest_file(
    manifest_path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> tuple[List[Entity], List[Relation]]:
    """
    Parse a dbt manifest.json file into grai.build entities and relations.

    Models with 2+ foreign key relationships are treated as relation tables.

    Args:
        manifest_path: Path to dbt manifest.json file.
        include_patterns: Optional patterns to filter models (inclusive).
        exclude_patterns: Optional patterns to filter models (exclusive).

    Returns:
        Tuple of (entities, relations).

    Raises:
        FileNotFoundError: If manifest file doesn't exist.
        json.JSONDecodeError: If manifest file is invalid JSON.

    Example:
        >>> entities, relations = parse_dbt_manifest_file(
        ...     Path("dbt_project/target/manifest.json"),
        ...     include_patterns=["fct_", "dim_"]
        ... )
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path) as f:
        manifest_data = json.load(f)

    parser = DbtManifestParser(manifest_data)
    return parser.parse_models(
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )


def write_entities_to_yaml(
    entities: List[Entity],
    output_dir: Path,
    overwrite: bool = False,
) -> List[Path]:
    """
    Write entities to YAML files in the specified directory.

    Args:
        entities: List of Entity objects to write.
        output_dir: Directory to write YAML files to.
        overwrite: Whether to overwrite existing files.

    Returns:
        List of paths to created YAML files.

    Raises:
        FileExistsError: If file exists and overwrite=False.

    Example:
        >>> entities = parse_dbt_manifest_file(Path("target/manifest.json"))
        >>> paths = write_entities_to_yaml(entities, Path("entities"))
        >>> print(f"Created {len(paths)} entity files")
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    for entity in entities:
        # Create filename from entity name
        filename = f"{entity.entity}.yml"
        filepath = output_dir / filename

        # Check if file exists
        if filepath.exists() and not overwrite:
            raise FileExistsError(
                f"Entity file already exists: {filepath}. " f"Use --force to overwrite."
            )

        # Convert entity to dict for YAML
        if isinstance(entity.source, SourceConfig):
            # Convert SourceConfig to dict and ensure type is serialized as string
            source_dict = entity.source.model_dump(exclude_none=True)
            # Convert SourceType enum to string value
            if "type" in source_dict:
                source_dict["type"] = (
                    source_dict["type"].value
                    if hasattr(source_dict["type"], "value")
                    else str(source_dict["type"])
                )
            source_data = source_dict
        else:
            source_data = entity.source

        entity_dict = {
            "entity": entity.entity,
            "source": source_data,
            "keys": entity.keys,
            "properties": [
                {
                    "name": prop.name,
                    "type": prop.type.value,
                    **({"description": prop.description} if prop.description else {}),
                }
                for prop in entity.properties
            ],
        }

        # Add description if present
        if entity.description:
            entity_dict["description"] = entity.description

        # Write to YAML with proper indentation
        # Use a custom Dumper to control list indentation
        class IndentedDumper(yaml.Dumper):
            def increase_indent(self, flow=False, indentless=False):
                return super().increase_indent(flow, False)

        with open(filepath, "w") as f:
            yaml.dump(
                entity_dict,
                f,
                Dumper=IndentedDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,  # Use 2-space indentation for consistency
                width=120,  # Prevent line wrapping for long descriptions
            )

        created_files.append(filepath)

    return created_files


def write_relations_to_yaml(
    relations: List[Relation],
    output_dir: Path,
    overwrite: bool = False,
) -> List[Path]:
    """
    Write relations to YAML files in the specified directory.

    Args:
        relations: List of Relation objects to write.
        output_dir: Directory to write YAML files to.
        overwrite: Whether to overwrite existing files.

    Returns:
        List of paths to created YAML files.

    Raises:
        FileExistsError: If file exists and overwrite=False.

    Example:
        >>> _, relations = parse_dbt_manifest_file(Path("target/manifest.json"))
        >>> paths = write_relations_to_yaml(relations, Path("relations"))
        >>> print(f"Created {len(paths)} relation files")
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    for relation in relations:
        # Create filename from relation name (lowercase)
        filename = f"{relation.relation.lower()}.yml"
        filepath = output_dir / filename

        # Check if file exists
        if filepath.exists() and not overwrite:
            raise FileExistsError(
                f"Relation file already exists: {filepath}. " f"Use --force to overwrite."
            )

        # Convert relation to dict for YAML
        if isinstance(relation.source, SourceConfig):
            # Convert SourceConfig to dict and ensure type is serialized as string
            source_dict = relation.source.model_dump(exclude_none=True)
            # Convert SourceType enum to string value
            if "type" in source_dict:
                source_dict["type"] = (
                    source_dict["type"].value
                    if hasattr(source_dict["type"], "value")
                    else str(source_dict["type"])
                )
            source_data = source_dict
        else:
            source_data = relation.source

        relation_dict = {
            "relation": relation.relation,
            "from": relation.from_entity,
            "to": relation.to_entity,
            "source": source_data,
            "mappings": {
                "from_key": relation.mappings.from_key,
                "to_key": relation.mappings.to_key,
            },
            "properties": [
                {
                    "name": prop.name,
                    "type": prop.type.value,
                    **({"description": prop.description} if prop.description else {}),
                }
                for prop in relation.properties
            ],
        }

        # Add description if present
        if relation.description:
            relation_dict["description"] = relation.description

        # Write to YAML with proper indentation
        # Use a custom Dumper to control list indentation
        class IndentedDumper(yaml.Dumper):
            def increase_indent(self, flow=False, indentless=False):
                return super().increase_indent(flow, False)

        with open(filepath, "w") as f:
            yaml.dump(
                relation_dict,
                f,
                Dumper=IndentedDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,  # Use 2-space indentation for consistency
                width=120,  # Prevent line wrapping for long descriptions
            )

        created_files.append(filepath)

    return created_files

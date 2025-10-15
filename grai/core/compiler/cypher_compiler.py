"""
Cypher compiler for grai.build.

This module generates Neo4j Cypher statements from Entity and Relation models.
"""

from pathlib import Path
from typing import Dict, List, Union

from grai.core.models import Entity, Project, Property, Relation


class CompilerError(Exception):
    """Base exception for compiler errors."""

    pass


def escape_cypher_string(value: str) -> str:
    """
    Escape a string for use in Cypher queries.

    Args:
        value: String to escape.

    Returns:
        Escaped string safe for Cypher.
    """
    # Escape single quotes and backslashes
    return value.replace("\\", "\\\\").replace("'", "\\'")


def get_cypher_property_placeholder(prop_name: str, use_row: bool = True) -> str:
    """
    Get the Cypher placeholder for a property value.

    Args:
        prop_name: Property name.
        use_row: If True, use row.property format; else use $property format.

    Returns:
        Cypher placeholder string.
    """
    if use_row:
        return f"row.{prop_name}"
    else:
        return f"${prop_name}"


def compile_property_set(
    properties: List[Property], node_var: str = "n", indent: str = "    "
) -> str:
    """
    Compile property SET clause for Cypher.

    Args:
        properties: List of properties to set.
        node_var: Variable name for the node/relationship (default: "n").
        indent: Indentation string for formatting.

    Returns:
        Cypher SET clause string.
    """
    if not properties:
        return ""

    set_clauses = []
    for prop in properties:
        placeholder = get_cypher_property_placeholder(prop.name)
        set_clauses.append(f"{node_var}.{prop.name} = {placeholder}")

    if len(set_clauses) == 1:
        return f"SET {set_clauses[0]}"
    else:
        # Multi-line format for multiple properties
        lines = [f"SET {set_clauses[0]}"]
        for clause in set_clauses[1:]:
            lines.append(f"{indent}{clause}")
        return ",\n".join(lines)


def compile_entity(entity: Entity) -> str:
    """
    Compile an entity into a Cypher MERGE statement.

    Args:
        entity: Entity model to compile.

    Returns:
        Cypher MERGE statement for creating/updating nodes.

    Example:
        ```cypher
        // Create customer nodes
        MERGE (n:customer {customer_id: row.customer_id})
        SET n.name = row.name,
            n.email = row.email;
        ```
    """
    # Build the MERGE clause with key properties
    key_conditions = []
    for key in entity.keys:
        placeholder = get_cypher_property_placeholder(key)
        key_conditions.append(f"{key}: {placeholder}")

    merge_clause = f"MERGE (n:{entity.entity} {{{', '.join(key_conditions)}}})"

    # Build the SET clause for non-key properties
    non_key_properties = [p for p in entity.properties if p.name not in entity.keys]

    if non_key_properties:
        set_clause = compile_property_set(non_key_properties)
        cypher = f"{merge_clause}\n{set_clause};"
    else:
        cypher = f"{merge_clause};"

    # Add comment header
    header = f"// Create {entity.entity} nodes"
    return f"{header}\n{cypher}"


def compile_relation(relation: Relation) -> str:
    """
    Compile a relation into Cypher MATCH...MERGE statements.

    Args:
        relation: Relation model to compile.

    Returns:
        Cypher statements for creating relationships.

    Example:
        ```cypher
        // Create PURCHASED relationships
        MATCH (from:customer {customer_id: row.customer_id})
        MATCH (to:product {product_id: row.product_id})
        MERGE (from)-[r:PURCHASED]->(to)
        SET r.order_id = row.order_id,
            r.order_date = row.order_date;
        ```
    """
    # Build MATCH clause for source node
    from_key = relation.mappings.from_key
    from_placeholder = get_cypher_property_placeholder(from_key)
    match_from = f"MATCH (from:{relation.from_entity} {{{from_key}: {from_placeholder}}})"

    # Build MATCH clause for target node
    to_key = relation.mappings.to_key
    to_placeholder = get_cypher_property_placeholder(to_key)
    match_to = f"MATCH (to:{relation.to_entity} {{{to_key}: {to_placeholder}}})"

    # Build MERGE clause for relationship
    merge_rel = f"MERGE (from)-[r:{relation.relation}]->(to)"

    # Build SET clause for relationship properties
    if relation.properties:
        set_clause = compile_property_set(relation.properties, node_var="r")
        cypher = f"{match_from}\n{match_to}\n{merge_rel}\n{set_clause};"
    else:
        cypher = f"{match_from}\n{match_to}\n{merge_rel};"

    # Add comment header
    header = f"// Create {relation.relation} relationships"
    return f"{header}\n{cypher}"


def compile_project(
    project: Project,
    include_header: bool = True,
    include_constraints: bool = True,
) -> str:
    """
    Compile a complete project into a Cypher script.

    Args:
        project: Project model to compile.
        include_header: If True, include script header with project info.
        include_constraints: If True, include constraint creation statements.

    Returns:
        Complete Cypher script as a string.
    """
    lines = []

    # Add header
    if include_header:
        lines.append(f"// Generated Cypher script for project: {project.name}")
        lines.append(f"// Version: {project.version}")
        lines.append("// Generated by grai.build")
        lines.append("")

    # Add constraints (unique constraints on entity keys)
    if include_constraints and project.entities:
        lines.append(
            "// ============================================================================="
        )
        lines.append("// CONSTRAINTS")
        lines.append(
            "// ============================================================================="
        )
        lines.append("")

        for entity in project.entities:
            for key in entity.keys:
                constraint_name = f"constraint_{entity.entity}_{key}"
                constraint = (
                    f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                    f"FOR (n:{entity.entity}) REQUIRE n.{key} IS UNIQUE;"
                )
                lines.append(constraint)

        lines.append("")

    # Add entities
    if project.entities:
        lines.append(
            "// ============================================================================="
        )
        lines.append("// ENTITIES (NODES)")
        lines.append(
            "// ============================================================================="
        )
        lines.append("")

        for entity in project.entities:
            lines.append(compile_entity(entity))
            lines.append("")

    # Add relations
    if project.relations:
        lines.append(
            "// ============================================================================="
        )
        lines.append("// RELATIONS (EDGES)")
        lines.append(
            "// ============================================================================="
        )
        lines.append("")

        for relation in project.relations:
            lines.append(compile_relation(relation))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_cypher_file(
    cypher: str,
    output_path: Union[str, Path],
    create_dirs: bool = True,
) -> Path:
    """
    Write Cypher script to a file.

    Args:
        cypher: Cypher script content.
        output_path: Path to write the file.
        create_dirs: If True, create parent directories if they don't exist.

    Returns:
        Path to the written file.

    Raises:
        CompilerError: If file cannot be written.
    """
    path = Path(output_path)

    try:
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(cypher)

        return path

    except Exception as e:
        raise CompilerError(f"Failed to write Cypher file to {path}: {e}")


def compile_and_write(
    project: Project,
    output_dir: Union[str, Path] = "target/neo4j",
    filename: str = "compiled.cypher",
    include_header: bool = True,
    include_constraints: bool = True,
) -> Path:
    """
    Compile a project and write the Cypher script to a file.

    Args:
        project: Project to compile.
        output_dir: Directory to write the output file.
        filename: Name of the output file.
        include_header: If True, include script header.
        include_constraints: If True, include constraint statements.

    Returns:
        Path to the written file.

    Raises:
        CompilerError: If compilation or writing fails.
    """
    # Compile the project
    cypher = compile_project(
        project,
        include_header=include_header,
        include_constraints=include_constraints,
    )

    # Write to file
    output_path = Path(output_dir) / filename
    return write_cypher_file(cypher, output_path)


def generate_load_csv_statements(
    project: Project,
    data_dir: str = "data",
) -> Dict[str, str]:
    """
    Generate LOAD CSV statements for entities and relations.

    Args:
        project: Project to generate load statements for.
        data_dir: Directory containing CSV files.

    Returns:
        Dictionary mapping entity/relation names to LOAD CSV statements.
    """
    statements = {}

    # Generate entity load statements
    for entity in project.entities:
        source_name = entity.get_source_name()
        csv_file = f"{data_dir}/{source_name.replace('.', '_')}.csv"

        # Build LOAD CSV statement
        merge_keys = {key: f"row.{key}" for key in entity.keys}
        key_clause = ", ".join([f"{k}: {v}" for k, v in merge_keys.items()])

        lines = [
            f"// Load {entity.entity} from CSV",
            f"LOAD CSV WITH HEADERS FROM 'file:///{csv_file}' AS row",
            f"MERGE (n:{entity.entity} {{{key_clause}}})",
        ]

        # Add SET clause for other properties
        non_key_props = [p for p in entity.properties if p.name not in entity.keys]
        if non_key_props:
            set_clauses = [f"n.{p.name} = row.{p.name}" for p in non_key_props]
            lines.append("SET " + ",\n    ".join(set_clauses))

        lines.append(";")
        statements[entity.entity] = "\n".join(lines)

    # Generate relation load statements
    for relation in project.relations:
        source_name = relation.get_source_name()
        csv_file = f"{data_dir}/{source_name.replace('.', '_')}.csv"

        lines = [
            f"// Load {relation.relation} from CSV",
            f"LOAD CSV WITH HEADERS FROM 'file:///{csv_file}' AS row",
            f"MATCH (from:{relation.from_entity} {{{relation.mappings.from_key}: row.{relation.mappings.from_key}}})",
            f"MATCH (to:{relation.to_entity} {{{relation.mappings.to_key}: row.{relation.mappings.to_key}}})",
            f"MERGE (from)-[r:{relation.relation}]->(to)",
        ]

        # Add SET clause for relationship properties
        if relation.properties:
            set_clauses = [f"r.{p.name} = row.{p.name}" for p in relation.properties]
            lines.append("SET " + ",\n    ".join(set_clauses))

        lines.append(";")
        statements[relation.relation] = "\n".join(lines)

    return statements


def compile_schema_only(project: Project) -> str:
    """
    Compile only the schema (constraints and indexes) without data loading.

    Args:
        project: Project to compile schema for.

    Returns:
        Cypher script with only schema definitions.
    """
    lines = [
        f"// Schema definition for project: {project.name}",
        f"// Version: {project.version}",
        "",
        "// =============================================================================",
        "// CONSTRAINTS",
        "// =============================================================================",
        "",
    ]

    for entity in project.entities:
        for key in entity.keys:
            constraint_name = f"constraint_{entity.entity}_{key}"
            constraint = (
                f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                f"FOR (n:{entity.entity}) REQUIRE n.{key} IS UNIQUE;"
            )
            lines.append(constraint)

    lines.append("")
    lines.append("// =============================================================================")
    lines.append("// INDEXES")
    lines.append("// =============================================================================")
    lines.append("")

    # Create indexes on non-key properties that might be used in queries
    for entity in project.entities:
        for prop in entity.properties:
            if prop.name not in entity.keys:
                index_name = f"index_{entity.entity}_{prop.name}"
                index = (
                    f"CREATE INDEX {index_name} IF NOT EXISTS "
                    f"FOR (n:{entity.entity}) ON (n.{prop.name});"
                )
                lines.append(index)

    return "\n".join(lines) + "\n"

"""RST directive parser for C4 model.

Parses RST files containing C4 model directives to extract entity data.
Uses regex-based parsing (not full RST).
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from julee.c4.entities.component import Component
from julee.c4.entities.container import Container, ContainerType
from julee.c4.entities.deployment_node import (
    ContainerInstance,
    DeploymentNode,
    NodeType,
)
from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.entities.software_system import SoftwareSystem, SystemType

logger = logging.getLogger(__name__)


# =============================================================================
# Parsed Data Classes
# =============================================================================


@dataclass
class ParsedSoftwareSystem:
    """Raw parsed data from a software system RST directive."""

    slug: str
    name: str = ""
    description: str = ""
    system_type: str = ""
    owner: str = ""
    technology: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedContainer:
    """Raw parsed data from a container RST directive."""

    slug: str
    name: str = ""
    system_slug: str = ""
    description: str = ""
    container_type: str = ""
    technology: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedComponent:
    """Raw parsed data from a component RST directive."""

    slug: str
    name: str = ""
    container_slug: str = ""
    system_slug: str = ""
    description: str = ""
    technology: str = ""
    interface: str = ""
    code_path: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedRelationship:
    """Raw parsed data from a relationship RST directive."""

    slug: str
    source_type: str = ""
    source_slug: str = ""
    destination_type: str = ""
    destination_slug: str = ""
    description: str = ""
    technology: str = ""
    bidirectional: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedDeploymentNode:
    """Raw parsed data from a deployment node RST directive."""

    slug: str
    name: str = ""
    environment: str = ""
    node_type: str = ""
    description: str = ""
    technology: str = ""
    instances: int = 1
    parent_slug: str = ""
    container_instances: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedDynamicStep:
    """Raw parsed data from a dynamic step RST directive."""

    slug: str
    sequence_name: str = ""
    step_number: int = 0
    source_type: str = ""
    source_slug: str = ""
    destination_type: str = ""
    destination_slug: str = ""
    description: str = ""
    technology: str = ""
    return_value: str = ""
    is_async: bool = False


# =============================================================================
# Regex Patterns
# =============================================================================

DEFINE_SOFTWARE_SYSTEM_PATTERN = re.compile(
    r"^\.\.\s+define-software-system::\s*(\S+)", re.MULTILINE
)
DEFINE_CONTAINER_PATTERN = re.compile(
    r"^\.\.\s+define-container::\s*(\S+)", re.MULTILINE
)
DEFINE_COMPONENT_PATTERN = re.compile(
    r"^\.\.\s+define-component::\s*(\S+)", re.MULTILINE
)
DEFINE_RELATIONSHIP_PATTERN = re.compile(
    r"^\.\.\s+define-relationship::\s*(\S+)", re.MULTILINE
)
DEFINE_DEPLOYMENT_NODE_PATTERN = re.compile(
    r"^\.\.\s+define-deployment-node::\s*(\S+)", re.MULTILINE
)
DEFINE_DYNAMIC_STEP_PATTERN = re.compile(
    r"^\.\.\s+define-dynamic-step::\s*(\S+)", re.MULTILINE
)
DEPLOY_CONTAINER_PATTERN = re.compile(
    r"^\.\.\s+deploy-container::\s*(\S+)", re.MULTILINE
)


# =============================================================================
# Parsing Helpers
# =============================================================================


def _extract_options(content: str) -> dict[str, str]:
    """Extract RST directive options from content.

    Options are lines like:
        :name: My Name
        :type: internal

    Args:
        content: RST content after the directive line

    Returns:
        Dict of option name to value
    """
    options: dict[str, str] = {}
    lines = content.split("\n")
    current_key: str | None = None
    current_value: list[str] = []
    found_any_option = False

    for line in lines:
        # Check for new option
        match = re.match(r"^\s{3}:([a-z-]+):\s*(.*)$", line)
        if match:
            # Save previous option if any
            if current_key:
                options[current_key] = "\n".join(current_value).strip()
            current_key = match.group(1)
            current_value = [match.group(2)] if match.group(2) else []
            found_any_option = True
        elif current_key and line.startswith("       ") and line.strip():
            # Continuation line for multi-line option (7 spaces)
            current_value.append(line.strip())
        elif line.strip() == "":
            # Empty line - only break if we've found options (end of options block)
            if found_any_option:
                if current_key:
                    options[current_key] = "\n".join(current_value).strip()
                break
            # Otherwise skip leading empty lines
        elif not line.startswith("   "):
            # Non-indented content - end of directive
            if current_key:
                options[current_key] = "\n".join(current_value).strip()
            break
        elif line.startswith("   ") and not line.startswith("   :"):
            # Content line (not option) - end options parsing
            if current_key:
                options[current_key] = "\n".join(current_value).strip()
            break

    # Handle final option
    if current_key and current_key not in options:
        options[current_key] = "\n".join(current_value).strip()

    return options


def _extract_content(content: str, after_options: bool = True) -> str:
    """Extract directive body content (indented text after options).

    Args:
        content: RST content after the directive line
        after_options: Whether to skip option lines first

    Returns:
        Extracted content text
    """
    lines = content.split("\n")
    content_lines: list[str] = []
    in_options = after_options
    found_option = False
    found_content = False

    for line in lines:
        # Skip option lines
        if in_options:
            if re.match(r"^\s{3}:[a-z-]+:", line):
                found_option = True
                continue
            elif line.startswith("       ") and found_option and not found_content:
                # Continuation of option (7 spaces)
                continue
            elif line.strip() == "":
                # Empty line - only exit options mode if we've seen options
                if found_option:
                    in_options = False
                continue
            elif line.startswith("   ") and not line.startswith("   :"):
                # Content line (not option) - exit options mode
                in_options = False
                found_content = True

        # Check for end of content (new directive)
        if line.startswith(".. ") and not line.startswith("   "):
            break

        # Extract content (remove 3-space indent)
        if line.startswith("   "):
            content_lines.append(line[3:])
        elif line.strip() == "":
            content_lines.append("")
        elif found_content:
            break

    # Strip trailing empty lines
    while content_lines and content_lines[-1].strip() == "":
        content_lines.pop()

    return "\n".join(content_lines)


def _parse_comma_list(value: str) -> list[str]:
    """Parse a comma-separated list of values."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _parse_bool(value: str) -> bool:
    """Parse a boolean string."""
    return value.lower() in ("true", "yes", "1")


# =============================================================================
# SoftwareSystem Parsing
# =============================================================================


def parse_software_system_content(content: str) -> ParsedSoftwareSystem | None:
    """Parse RST content containing a define-software-system directive.

    Args:
        content: Full RST file content

    Returns:
        ParsedSoftwareSystem or None if no directive found
    """
    match = DEFINE_SOFTWARE_SYSTEM_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()
    remaining = content[match.end() :]
    options = _extract_options(remaining)
    description = _extract_content(remaining)

    return ParsedSoftwareSystem(
        slug=slug,
        name=options.get("name", ""),
        description=description,
        system_type=options.get("type", ""),
        owner=options.get("owner", ""),
        technology=options.get("technology", ""),
        url=options.get("url", ""),
        tags=_parse_comma_list(options.get("tags", "")),
    )


def parse_software_system_file(file_path: Path) -> SoftwareSystem | None:
    """Parse an RST file containing a software system directive.

    Args:
        file_path: Path to the RST file

    Returns:
        SoftwareSystem entity or None if parsing fails
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_software_system_content(content)
    if not parsed:
        logger.debug(f"No define-software-system directive found in {file_path}")
        return None

    # Map string to enum
    system_type = SystemType.INTERNAL
    if parsed.system_type:
        try:
            system_type = SystemType(parsed.system_type)
        except ValueError:
            logger.warning(
                f"Unknown system_type '{parsed.system_type}', using INTERNAL"
            )

    return SoftwareSystem(
        slug=parsed.slug,
        name=parsed.name or parsed.slug,
        description=parsed.description,
        system_type=system_type,
        owner=parsed.owner,
        technology=parsed.technology,
        url=parsed.url,
        tags=parsed.tags,
    )


def scan_software_system_directory(directory: Path) -> list[SoftwareSystem]:
    """Scan a directory for RST files containing software system directives.

    Args:
        directory: Directory to scan

    Returns:
        List of parsed SoftwareSystem entities
    """
    systems = []

    if not directory.exists():
        logger.debug(f"Software systems directory not found: {directory}")
        return systems

    for rst_file in directory.glob("*.rst"):
        system = parse_software_system_file(rst_file)
        if system:
            systems.append(system)

    logger.info(f"Parsed {len(systems)} software systems from {directory}")
    return systems


# =============================================================================
# Container Parsing
# =============================================================================


def parse_container_content(content: str) -> ParsedContainer | None:
    """Parse RST content containing a define-container directive."""
    match = DEFINE_CONTAINER_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()
    remaining = content[match.end() :]
    options = _extract_options(remaining)
    description = _extract_content(remaining)

    return ParsedContainer(
        slug=slug,
        name=options.get("name", ""),
        system_slug=options.get("system", ""),
        description=description,
        container_type=options.get("type", ""),
        technology=options.get("technology", ""),
        url=options.get("url", ""),
        tags=_parse_comma_list(options.get("tags", "")),
    )


def parse_container_file(file_path: Path) -> Container | None:
    """Parse an RST file containing a container directive."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_container_content(content)
    if not parsed:
        logger.debug(f"No define-container directive found in {file_path}")
        return None

    container_type = ContainerType.OTHER
    if parsed.container_type:
        try:
            container_type = ContainerType(parsed.container_type)
        except ValueError:
            logger.warning(
                f"Unknown container_type '{parsed.container_type}', using OTHER"
            )

    return Container(
        slug=parsed.slug,
        name=parsed.name or parsed.slug,
        system_slug=parsed.system_slug,
        description=parsed.description,
        container_type=container_type,
        technology=parsed.technology,
        url=parsed.url,
        tags=parsed.tags,
    )


def scan_container_directory(directory: Path) -> list[Container]:
    """Scan a directory for RST files containing container directives."""
    containers = []

    if not directory.exists():
        logger.debug(f"Containers directory not found: {directory}")
        return containers

    for rst_file in directory.glob("*.rst"):
        container = parse_container_file(rst_file)
        if container:
            containers.append(container)

    logger.info(f"Parsed {len(containers)} containers from {directory}")
    return containers


# =============================================================================
# Component Parsing
# =============================================================================


def parse_component_content(content: str) -> ParsedComponent | None:
    """Parse RST content containing a define-component directive."""
    match = DEFINE_COMPONENT_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()
    remaining = content[match.end() :]
    options = _extract_options(remaining)
    description = _extract_content(remaining)

    return ParsedComponent(
        slug=slug,
        name=options.get("name", ""),
        container_slug=options.get("container", ""),
        system_slug=options.get("system", ""),
        description=description,
        technology=options.get("technology", ""),
        interface=options.get("interface", ""),
        code_path=options.get("code-path", ""),
        tags=_parse_comma_list(options.get("tags", "")),
    )


def parse_component_file(file_path: Path) -> Component | None:
    """Parse an RST file containing a component directive."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_component_content(content)
    if not parsed:
        logger.debug(f"No define-component directive found in {file_path}")
        return None

    return Component(
        slug=parsed.slug,
        name=parsed.name or parsed.slug,
        container_slug=parsed.container_slug,
        system_slug=parsed.system_slug,
        description=parsed.description,
        technology=parsed.technology,
        interface=parsed.interface,
        code_path=parsed.code_path,
        tags=parsed.tags,
    )


def scan_component_directory(directory: Path) -> list[Component]:
    """Scan a directory for RST files containing component directives."""
    components = []

    if not directory.exists():
        logger.debug(f"Components directory not found: {directory}")
        return components

    for rst_file in directory.glob("*.rst"):
        component = parse_component_file(rst_file)
        if component:
            components.append(component)

    logger.info(f"Parsed {len(components)} components from {directory}")
    return components


# =============================================================================
# Relationship Parsing
# =============================================================================


def parse_relationship_content(content: str) -> ParsedRelationship | None:
    """Parse RST content containing a define-relationship directive."""
    match = DEFINE_RELATIONSHIP_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()
    remaining = content[match.end() :]
    options = _extract_options(remaining)
    description = _extract_content(remaining)

    return ParsedRelationship(
        slug=slug,
        source_type=options.get("source-type", ""),
        source_slug=options.get("source", ""),
        destination_type=options.get("destination-type", ""),
        destination_slug=options.get("destination", ""),
        description=description,
        technology=options.get("technology", ""),
        bidirectional=_parse_bool(options.get("bidirectional", "")),
        tags=_parse_comma_list(options.get("tags", "")),
    )


def parse_relationship_file(file_path: Path) -> Relationship | None:
    """Parse an RST file containing a relationship directive."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_relationship_content(content)
    if not parsed:
        logger.debug(f"No define-relationship directive found in {file_path}")
        return None

    # Map string to enums
    try:
        source_type = ElementType(parsed.source_type)
    except ValueError:
        logger.warning(f"Unknown source_type '{parsed.source_type}'")
        return None

    try:
        destination_type = ElementType(parsed.destination_type)
    except ValueError:
        logger.warning(f"Unknown destination_type '{parsed.destination_type}'")
        return None

    return Relationship(
        slug=parsed.slug,
        source_type=source_type,
        source_slug=parsed.source_slug,
        destination_type=destination_type,
        destination_slug=parsed.destination_slug,
        description=parsed.description or "Uses",
        technology=parsed.technology,
        bidirectional=parsed.bidirectional,
        tags=parsed.tags,
    )


def scan_relationship_directory(directory: Path) -> list[Relationship]:
    """Scan a directory for RST files containing relationship directives."""
    relationships = []

    if not directory.exists():
        logger.debug(f"Relationships directory not found: {directory}")
        return relationships

    for rst_file in directory.glob("*.rst"):
        relationship = parse_relationship_file(rst_file)
        if relationship:
            relationships.append(relationship)

    logger.info(f"Parsed {len(relationships)} relationships from {directory}")
    return relationships


# =============================================================================
# DeploymentNode Parsing
# =============================================================================


def parse_deployment_node_content(content: str) -> ParsedDeploymentNode | None:
    """Parse RST content containing a define-deployment-node directive."""
    match = DEFINE_DEPLOYMENT_NODE_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()
    remaining = content[match.end() :]
    options = _extract_options(remaining)
    description = _extract_content(remaining)

    # Parse container instances
    container_instances = []
    for ci_match in DEPLOY_CONTAINER_PATTERN.finditer(content):
        ci_slug = ci_match.group(1).strip()
        ci_remaining = content[ci_match.end() :]
        ci_options = _extract_options(ci_remaining)
        instances = int(ci_options.get("instances", "1"))
        container_instances.append(
            {"container_slug": ci_slug, "instance_count": instances}
        )

    # Parse instances count
    instances = 1
    if options.get("instances"):
        try:
            instances = int(options["instances"])
        except ValueError:
            pass

    return ParsedDeploymentNode(
        slug=slug,
        name=options.get("name", ""),
        environment=options.get("environment", ""),
        node_type=options.get("type", ""),
        description=description,
        technology=options.get("technology", ""),
        instances=instances,
        parent_slug=options.get("parent", ""),
        container_instances=container_instances,
        tags=_parse_comma_list(options.get("tags", "")),
    )


def parse_deployment_node_file(file_path: Path) -> DeploymentNode | None:
    """Parse an RST file containing a deployment node directive."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_deployment_node_content(content)
    if not parsed:
        logger.debug(f"No define-deployment-node directive found in {file_path}")
        return None

    node_type = NodeType.OTHER
    if parsed.node_type:
        try:
            node_type = NodeType(parsed.node_type)
        except ValueError:
            logger.warning(f"Unknown node_type '{parsed.node_type}', using OTHER")

    container_instances = [
        ContainerInstance(
            container_slug=ci["container_slug"],
            instance_count=ci["instance_count"],
        )
        for ci in parsed.container_instances
    ]

    return DeploymentNode(
        slug=parsed.slug,
        name=parsed.name or parsed.slug,
        environment=parsed.environment or "production",
        node_type=node_type,
        description=parsed.description,
        technology=parsed.technology,
        instances=parsed.instances,
        parent_slug=parsed.parent_slug or None,
        container_instances=container_instances,
        tags=parsed.tags,
    )


def scan_deployment_node_directory(directory: Path) -> list[DeploymentNode]:
    """Scan a directory for RST files containing deployment node directives."""
    nodes = []

    if not directory.exists():
        logger.debug(f"Deployment nodes directory not found: {directory}")
        return nodes

    for rst_file in directory.glob("*.rst"):
        node = parse_deployment_node_file(rst_file)
        if node:
            nodes.append(node)

    logger.info(f"Parsed {len(nodes)} deployment nodes from {directory}")
    return nodes


# =============================================================================
# DynamicStep Parsing
# =============================================================================


def parse_dynamic_step_content(content: str) -> ParsedDynamicStep | None:
    """Parse RST content containing a define-dynamic-step directive."""
    match = DEFINE_DYNAMIC_STEP_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()
    remaining = content[match.end() :]
    options = _extract_options(remaining)
    description = _extract_content(remaining)

    # Parse step number
    step_number = 0
    if options.get("step"):
        try:
            step_number = int(options["step"])
        except ValueError:
            pass

    return ParsedDynamicStep(
        slug=slug,
        sequence_name=options.get("sequence", ""),
        step_number=step_number,
        source_type=options.get("source-type", ""),
        source_slug=options.get("source", ""),
        destination_type=options.get("destination-type", ""),
        destination_slug=options.get("destination", ""),
        description=description,
        technology=options.get("technology", ""),
        return_value=options.get("return", ""),
        is_async=_parse_bool(options.get("async", "")),
    )


def parse_dynamic_step_file(file_path: Path) -> DynamicStep | None:
    """Parse an RST file containing a dynamic step directive."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_dynamic_step_content(content)
    if not parsed:
        logger.debug(f"No define-dynamic-step directive found in {file_path}")
        return None

    # Map string to enums
    try:
        source_type = ElementType(parsed.source_type)
    except ValueError:
        logger.warning(f"Unknown source_type '{parsed.source_type}'")
        return None

    try:
        destination_type = ElementType(parsed.destination_type)
    except ValueError:
        logger.warning(f"Unknown destination_type '{parsed.destination_type}'")
        return None

    return DynamicStep(
        slug=parsed.slug,
        sequence_name=parsed.sequence_name,
        step_number=parsed.step_number,
        source_type=source_type,
        source_slug=parsed.source_slug,
        destination_type=destination_type,
        destination_slug=parsed.destination_slug,
        description=parsed.description,
        technology=parsed.technology,
        return_value=parsed.return_value,
        is_async=parsed.is_async,
    )


def scan_dynamic_step_directory(directory: Path) -> list[DynamicStep]:
    """Scan a directory for RST files containing dynamic step directives."""
    steps = []

    if not directory.exists():
        logger.debug(f"Dynamic steps directory not found: {directory}")
        return steps

    for rst_file in directory.glob("*.rst"):
        step = parse_dynamic_step_file(rst_file)
        if step:
            steps.append(step)

    logger.info(f"Parsed {len(steps)} dynamic steps from {directory}")
    return steps

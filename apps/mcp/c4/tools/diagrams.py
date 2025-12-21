"""MCP tools for C4 diagram generation."""

from ..context import (
    get_component_diagram_use_case,
    get_container_diagram_use_case,
    get_deployment_diagram_use_case,
    get_dynamic_diagram_use_case,
    get_system_context_diagram_use_case,
    get_system_landscape_diagram_use_case,
)


async def get_system_context_diagram(system_slug: str) -> dict:
    """Generate a system context diagram for a software system.

    Args:
        system_slug: Slug of the software system to show context for

    Returns:
        Diagram data including the system, external systems, persons, and relationships
    """
    use_case = get_system_context_diagram_use_case()
    result = await use_case.execute(system_slug)
    if not result:
        return {"found": False, "data": None}
    return {
        "found": True,
        "data": {
            "system": result.system.model_dump(),
            "external_systems": [s.model_dump() for s in result.external_systems],
            "person_slugs": result.person_slugs,
            "relationships": [r.model_dump() for r in result.relationships],
        },
    }


async def get_container_diagram(system_slug: str) -> dict:
    """Generate a container diagram for a software system.

    Args:
        system_slug: Slug of the software system to show containers for

    Returns:
        Diagram data including containers, external systems, persons, and relationships
    """
    use_case = get_container_diagram_use_case()
    result = await use_case.execute(system_slug)
    if not result:
        return {"found": False, "data": None}
    return {
        "found": True,
        "data": {
            "system": result.system.model_dump(),
            "containers": [c.model_dump() for c in result.containers],
            "external_systems": [s.model_dump() for s in result.external_systems],
            "person_slugs": result.person_slugs,
            "relationships": [r.model_dump() for r in result.relationships],
        },
    }


async def get_component_diagram(container_slug: str) -> dict:
    """Generate a component diagram for a container.

    Args:
        container_slug: Slug of the container to show components for

    Returns:
        Diagram data including components, external elements, and relationships
    """
    use_case = get_component_diagram_use_case()
    result = await use_case.execute(container_slug)
    if not result:
        return {"found": False, "data": None}
    return {
        "found": True,
        "data": {
            "system": result.system.model_dump(),
            "container": result.container.model_dump(),
            "components": [c.model_dump() for c in result.components],
            "external_containers": [c.model_dump() for c in result.external_containers],
            "external_systems": [s.model_dump() for s in result.external_systems],
            "person_slugs": result.person_slugs,
            "relationships": [r.model_dump() for r in result.relationships],
        },
    }


async def get_system_landscape_diagram() -> dict:
    """Generate a system landscape diagram showing all systems and their relationships.

    Returns:
        Diagram data including all systems, persons, and their relationships
    """
    use_case = get_system_landscape_diagram_use_case()
    result = await use_case.execute()
    return {
        "found": True,
        "data": {
            "systems": [s.model_dump() for s in result.systems],
            "person_slugs": result.person_slugs,
            "relationships": [r.model_dump() for r in result.relationships],
        },
    }


async def get_deployment_diagram(environment: str) -> dict:
    """Generate a deployment diagram for a specific environment.

    Args:
        environment: Name of the deployment environment (e.g., "production", "staging")

    Returns:
        Diagram data including nodes, containers, and relationships
    """
    use_case = get_deployment_diagram_use_case()
    result = await use_case.execute(environment)
    return {
        "found": True,
        "data": {
            "environment": result.environment,
            "nodes": [n.model_dump() for n in result.nodes],
            "containers": [c.model_dump() for c in result.containers],
            "relationships": [r.model_dump() for r in result.relationships],
        },
    }


async def get_dynamic_diagram(sequence_name: str) -> dict:
    """Generate a dynamic diagram for a specific sequence.

    Args:
        sequence_name: Name of the dynamic sequence to visualize

    Returns:
        Diagram data including steps and participating elements
    """
    use_case = get_dynamic_diagram_use_case()
    result = await use_case.execute(sequence_name)
    if not result:
        return {"found": False, "data": None}
    return {
        "found": True,
        "data": {
            "sequence_name": result.sequence_name,
            "steps": [s.model_dump() for s in result.steps],
            "systems": [s.model_dump() for s in result.systems],
            "containers": [c.model_dump() for c in result.containers],
            "components": [c.model_dump() for c in result.components],
            "person_slugs": result.person_slugs,
        },
    }

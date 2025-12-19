"""C4 MCP Server.

FastMCP server for managing C4 architecture model via Model Context Protocol.
"""

from typing import Any

from fastmcp import FastMCP

from ..mcp_shared import (
    create_annotation,
    delete_annotation,
    diagram_annotation,
    read_only_annotation,
    update_annotation,
)
from .tools import (
    # Components
    create_component,
    # Containers
    create_container,
    # Deployment Nodes
    create_deployment_node,
    # Dynamic Steps
    create_dynamic_step,
    # Relationships
    create_relationship,
    # Software Systems
    create_software_system,
    delete_component,
    delete_container,
    delete_deployment_node,
    delete_dynamic_step,
    delete_relationship,
    delete_software_system,
    get_component,
    # Diagrams
    get_component_diagram,
    get_container,
    get_container_diagram,
    get_deployment_diagram,
    get_deployment_node,
    get_dynamic_diagram,
    get_dynamic_step,
    get_relationship,
    get_software_system,
    get_system_context_diagram,
    get_system_landscape_diagram,
    list_components,
    list_containers,
    list_deployment_nodes,
    list_dynamic_steps,
    list_relationships,
    list_software_systems,
    update_component,
    update_container,
    update_deployment_node,
    update_dynamic_step,
    update_relationship,
    update_software_system,
)

# Create the FastMCP server
mcp = FastMCP(
    "C4 Architecture Server",
    instructions="MCP server for C4 software architecture model",
)


# ============================================================================
# Software System tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Software System"))
async def mcp_create_software_system(
    slug: str,
    name: str,
    description: str = "",
    system_type: str = "internal",
    owner: str = "",
    technology: str = "",
    url: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Create a software system in the C4 model.

    Software systems are the highest level of abstraction in C4, representing
    the overall boundaries of what you're building or describing.

    System types:
    - internal: Systems you are building/own
    - external: Systems outside your organization
    - existing: Legacy systems being replaced/integrated

    Args:
        slug: Unique identifier (e.g., "banking-system", "email-service")
        name: Human-readable name (e.g., "Internet Banking System")
        description: What this system does and its purpose
        system_type: Classification - "internal", "external", "existing"
        owner: Team or organization responsible
        technology: High-level technology description
        url: Link to documentation
        tags: Classification tags for filtering
    """
    return await create_software_system(
        slug=slug,
        name=name,
        description=description,
        system_type=system_type,
        owner=owner,
        technology=technology,
        url=url,
        tags=tags,
    )


@mcp.tool(annotations=read_only_annotation("Get Software System"))
async def mcp_get_software_system(slug: str) -> dict:
    """Get a software system by slug.

    Args:
        slug: Software system identifier
    """
    return await get_software_system(slug)


@mcp.tool(annotations=read_only_annotation("List Software Systems"))
async def mcp_list_software_systems() -> dict:
    """List all software systems in the C4 model."""
    return await list_software_systems()


@mcp.tool(annotations=update_annotation("Update Software System"))
async def mcp_update_software_system(
    slug: str,
    name: str | None = None,
    description: str | None = None,
    system_type: str | None = None,
    owner: str | None = None,
    technology: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update a software system. Only provided fields are changed.

    Args:
        slug: Software system identifier to update
        name: New display name (optional)
        description: New description (optional)
        system_type: New type - "internal", "external", "existing" (optional)
        owner: New owner (optional)
        technology: New technology description (optional)
        url: New documentation URL (optional)
        tags: New tags - replaces existing (optional)
    """
    return await update_software_system(
        slug=slug,
        name=name,
        description=description,
        system_type=system_type,
        owner=owner,
        technology=technology,
        url=url,
        tags=tags,
    )


@mcp.tool(annotations=delete_annotation("Delete Software System"))
async def mcp_delete_software_system(slug: str) -> dict:
    """Delete a software system by slug.

    Warning: This does not delete associated containers or relationships.

    Args:
        slug: Software system identifier to delete
    """
    return await delete_software_system(slug)


# ============================================================================
# Container tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Container"))
async def mcp_create_container(
    slug: str,
    name: str,
    system_slug: str,
    description: str = "",
    container_type: str = "other",
    technology: str = "",
    url: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Create a container within a software system.

    Containers are separately deployable/runnable units: applications, data stores,
    services, etc. They represent the major building blocks of a system.

    Container types: web_application, mobile_app, desktop_app, single_page_app,
    api, microservice, serverless, database, file_system, message_queue, other

    Args:
        slug: Unique identifier (e.g., "api-app", "web-app", "database")
        name: Human-readable name (e.g., "API Application")
        system_slug: Parent software system slug
        description: What this container does
        container_type: Type classification
        technology: Specific tech stack (e.g., "FastAPI, Python 3.11")
        url: Link to documentation
        tags: Classification tags
    """
    return await create_container(
        slug=slug,
        name=name,
        system_slug=system_slug,
        description=description,
        container_type=container_type,
        technology=technology,
        url=url,
        tags=tags,
    )


@mcp.tool(annotations=read_only_annotation("Get Container"))
async def mcp_get_container(slug: str) -> dict:
    """Get a container by slug.

    Args:
        slug: Container identifier
    """
    return await get_container(slug)


@mcp.tool(annotations=read_only_annotation("List Containers"))
async def mcp_list_containers() -> dict:
    """List all containers in the C4 model."""
    return await list_containers()


@mcp.tool(annotations=update_annotation("Update Container"))
async def mcp_update_container(
    slug: str,
    name: str | None = None,
    system_slug: str | None = None,
    description: str | None = None,
    container_type: str | None = None,
    technology: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update a container. Only provided fields are changed.

    Args:
        slug: Container identifier to update
        name: New display name (optional)
        system_slug: New parent system (optional)
        description: New description (optional)
        container_type: New type (optional)
        technology: New technology description (optional)
        url: New documentation URL (optional)
        tags: New tags - replaces existing (optional)
    """
    return await update_container(
        slug=slug,
        name=name,
        system_slug=system_slug,
        description=description,
        container_type=container_type,
        technology=technology,
        url=url,
        tags=tags,
    )


@mcp.tool(annotations=delete_annotation("Delete Container"))
async def mcp_delete_container(slug: str) -> dict:
    """Delete a container by slug.

    Warning: This does not delete associated components or relationships.

    Args:
        slug: Container identifier to delete
    """
    return await delete_container(slug)


# ============================================================================
# Component tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Component"))
async def mcp_create_component(
    slug: str,
    name: str,
    container_slug: str,
    system_slug: str,
    description: str = "",
    technology: str = "",
    interface: str = "",
    code_path: str = "",
    url: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Create a component within a container.

    Components are the implementation units within containers: classes, modules,
    services, controllers, etc. They represent the internal building blocks.

    Args:
        slug: Unique identifier (e.g., "auth-controller", "user-service")
        name: Human-readable name (e.g., "Authentication Controller")
        container_slug: Parent container slug
        system_slug: Grandparent system slug (denormalized for queries)
        description: What this component does
        technology: Implementation technology
        interface: Interface description (e.g., "REST API", "gRPC")
        code_path: Path to source code
        url: Link to documentation
        tags: Classification tags
    """
    return await create_component(
        slug=slug,
        name=name,
        container_slug=container_slug,
        system_slug=system_slug,
        description=description,
        technology=technology,
        interface=interface,
        code_path=code_path,
        url=url,
        tags=tags,
    )


@mcp.tool(annotations=read_only_annotation("Get Component"))
async def mcp_get_component(slug: str) -> dict:
    """Get a component by slug.

    Args:
        slug: Component identifier
    """
    return await get_component(slug)


@mcp.tool(annotations=read_only_annotation("List Components"))
async def mcp_list_components() -> dict:
    """List all components in the C4 model."""
    return await list_components()


@mcp.tool(annotations=update_annotation("Update Component"))
async def mcp_update_component(
    slug: str,
    name: str | None = None,
    container_slug: str | None = None,
    system_slug: str | None = None,
    description: str | None = None,
    technology: str | None = None,
    interface: str | None = None,
    code_path: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update a component. Only provided fields are changed.

    Args:
        slug: Component identifier to update
        name: New display name (optional)
        container_slug: New parent container (optional)
        system_slug: New grandparent system (optional)
        description: New description (optional)
        technology: New technology (optional)
        interface: New interface description (optional)
        code_path: New code path (optional)
        url: New documentation URL (optional)
        tags: New tags - replaces existing (optional)
    """
    return await update_component(
        slug=slug,
        name=name,
        container_slug=container_slug,
        system_slug=system_slug,
        description=description,
        technology=technology,
        interface=interface,
        code_path=code_path,
        url=url,
        tags=tags,
    )


@mcp.tool(annotations=delete_annotation("Delete Component"))
async def mcp_delete_component(slug: str) -> dict:
    """Delete a component by slug.

    Warning: This does not delete associated relationships.

    Args:
        slug: Component identifier to delete
    """
    return await delete_component(slug)


# ============================================================================
# Relationship tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Relationship"))
async def mcp_create_relationship(
    source_type: str,
    source_slug: str,
    destination_type: str,
    destination_slug: str,
    slug: str = "",
    description: str = "Uses",
    technology: str = "",
    bidirectional: bool = False,
    tags: list[str] | None = None,
) -> dict:
    """Create a relationship between C4 elements.

    Relationships show how elements interact. Source and destination can be:
    - person: References HCD personas by normalized name
    - software_system: References a software system
    - container: References a container
    - component: References a component

    Args:
        source_type: Type of source element (person, software_system, container, component)
        source_slug: Slug of source element
        destination_type: Type of destination element
        destination_slug: Slug of destination element
        slug: Optional identifier (auto-generated if empty)
        description: What the relationship means (e.g., "Sends emails via")
        technology: Protocol/technology used (e.g., "HTTPS/JSON", "gRPC")
        bidirectional: Whether the relationship goes both ways
        tags: Classification tags
    """
    return await create_relationship(
        source_type=source_type,
        source_slug=source_slug,
        destination_type=destination_type,
        destination_slug=destination_slug,
        slug=slug,
        description=description,
        technology=technology,
        bidirectional=bidirectional,
        tags=tags,
    )


@mcp.tool(annotations=read_only_annotation("Get Relationship"))
async def mcp_get_relationship(slug: str) -> dict:
    """Get a relationship by slug.

    Args:
        slug: Relationship identifier
    """
    return await get_relationship(slug)


@mcp.tool(annotations=read_only_annotation("List Relationships"))
async def mcp_list_relationships() -> dict:
    """List all relationships in the C4 model."""
    return await list_relationships()


@mcp.tool(annotations=update_annotation("Update Relationship"))
async def mcp_update_relationship(
    slug: str,
    description: str | None = None,
    technology: str | None = None,
    bidirectional: bool | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update a relationship. Only provided fields are changed.

    Note: Source and destination cannot be changed - create a new relationship instead.

    Args:
        slug: Relationship identifier to update
        description: New description (optional)
        technology: New technology (optional)
        bidirectional: New bidirectional flag (optional)
        tags: New tags - replaces existing (optional)
    """
    return await update_relationship(
        slug=slug,
        description=description,
        technology=technology,
        bidirectional=bidirectional,
        tags=tags,
    )


@mcp.tool(annotations=delete_annotation("Delete Relationship"))
async def mcp_delete_relationship(slug: str) -> dict:
    """Delete a relationship by slug.

    Args:
        slug: Relationship identifier to delete
    """
    return await delete_relationship(slug)


# ============================================================================
# Deployment Node tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Deployment Node"))
async def mcp_create_deployment_node(
    slug: str,
    name: str,
    environment: str = "production",
    node_type: str = "other",
    technology: str = "",
    description: str = "",
    parent_slug: str | None = None,
    container_instances: list[dict[str, Any]] | None = None,
    properties: dict[str, str] | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Create a deployment node representing infrastructure.

    Deployment nodes represent the physical/virtual infrastructure where
    containers are deployed: servers, VMs, containers, cloud services, etc.

    Node types: server, vm, container_runtime, kubernetes_cluster, cloud_service,
    database_server, load_balancer, firewall, cdn, region, zone, other

    Args:
        slug: Unique identifier (e.g., "prod-web-server", "k8s-cluster")
        name: Human-readable name (e.g., "Production Web Server")
        environment: Deployment environment (e.g., "production", "staging")
        node_type: Infrastructure type
        technology: Infrastructure technology (e.g., "Ubuntu 22.04", "AWS ECS")
        description: What this node provides
        parent_slug: Parent node for nested hierarchy
        container_instances: List of deployed containers with instance_id
        properties: Additional node properties
        tags: Classification tags
    """
    return await create_deployment_node(
        slug=slug,
        name=name,
        environment=environment,
        node_type=node_type,
        technology=technology,
        description=description,
        parent_slug=parent_slug,
        container_instances=container_instances,
        properties=properties,
        tags=tags,
    )


@mcp.tool(annotations=read_only_annotation("Get Deployment Node"))
async def mcp_get_deployment_node(slug: str) -> dict:
    """Get a deployment node by slug.

    Args:
        slug: Deployment node identifier
    """
    return await get_deployment_node(slug)


@mcp.tool(annotations=read_only_annotation("List Deployment Nodes"))
async def mcp_list_deployment_nodes() -> dict:
    """List all deployment nodes in the C4 model."""
    return await list_deployment_nodes()


@mcp.tool(annotations=update_annotation("Update Deployment Node"))
async def mcp_update_deployment_node(
    slug: str,
    name: str | None = None,
    environment: str | None = None,
    node_type: str | None = None,
    technology: str | None = None,
    description: str | None = None,
    parent_slug: str | None = None,
    container_instances: list[dict[str, Any]] | None = None,
    properties: dict[str, str] | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update a deployment node. Only provided fields are changed.

    Args:
        slug: Deployment node identifier to update
        name: New display name (optional)
        environment: New environment (optional)
        node_type: New type (optional)
        technology: New technology (optional)
        description: New description (optional)
        parent_slug: New parent node (optional)
        container_instances: New container instances - replaces existing (optional)
        properties: New properties - replaces existing (optional)
        tags: New tags - replaces existing (optional)
    """
    return await update_deployment_node(
        slug=slug,
        name=name,
        environment=environment,
        node_type=node_type,
        technology=technology,
        description=description,
        parent_slug=parent_slug,
        container_instances=container_instances,
        properties=properties,
        tags=tags,
    )


@mcp.tool(annotations=delete_annotation("Delete Deployment Node"))
async def mcp_delete_deployment_node(slug: str) -> dict:
    """Delete a deployment node by slug.

    Warning: This does not update child nodes or container references.

    Args:
        slug: Deployment node identifier to delete
    """
    return await delete_deployment_node(slug)


# ============================================================================
# Dynamic Step tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Dynamic Step"))
async def mcp_create_dynamic_step(
    sequence_name: str,
    step_number: int,
    source_type: str,
    source_slug: str,
    destination_type: str,
    destination_slug: str,
    slug: str = "",
    description: str = "",
    technology: str = "",
    return_description: str = "",
    is_return: bool = False,
) -> dict:
    """Create a step in a dynamic (sequence) diagram.

    Dynamic steps show runtime behavior - how elements collaborate to
    accomplish a specific use case. Steps are numbered and ordered.

    Args:
        sequence_name: Name of the dynamic sequence (e.g., "login-flow")
        step_number: Order within sequence (1-based)
        source_type: Type of calling element
        source_slug: Slug of calling element
        destination_type: Type of called element
        destination_slug: Slug of called element
        slug: Optional identifier (auto-generated if empty)
        description: What this step does (e.g., "Validates credentials")
        technology: Protocol/technology (e.g., "HTTPS POST")
        return_description: Description of return value/response
        is_return: Whether this represents a return/response step
    """
    return await create_dynamic_step(
        sequence_name=sequence_name,
        step_number=step_number,
        source_type=source_type,
        source_slug=source_slug,
        destination_type=destination_type,
        destination_slug=destination_slug,
        slug=slug,
        description=description,
        technology=technology,
        return_description=return_description,
        is_return=is_return,
    )


@mcp.tool(annotations=read_only_annotation("Get Dynamic Step"))
async def mcp_get_dynamic_step(slug: str) -> dict:
    """Get a dynamic step by slug.

    Args:
        slug: Dynamic step identifier
    """
    return await get_dynamic_step(slug)


@mcp.tool(annotations=read_only_annotation("List Dynamic Steps"))
async def mcp_list_dynamic_steps() -> dict:
    """List all dynamic steps in the C4 model."""
    return await list_dynamic_steps()


@mcp.tool(annotations=update_annotation("Update Dynamic Step"))
async def mcp_update_dynamic_step(
    slug: str,
    step_number: int | None = None,
    description: str | None = None,
    technology: str | None = None,
    return_description: str | None = None,
    is_return: bool | None = None,
) -> dict:
    """Update a dynamic step. Only provided fields are changed.

    Note: sequence_name and element references cannot be changed.

    Args:
        slug: Dynamic step identifier to update
        step_number: New step number (optional)
        description: New description (optional)
        technology: New technology (optional)
        return_description: New return description (optional)
        is_return: New return flag (optional)
    """
    return await update_dynamic_step(
        slug=slug,
        step_number=step_number,
        description=description,
        technology=technology,
        return_description=return_description,
        is_return=is_return,
    )


@mcp.tool(annotations=delete_annotation("Delete Dynamic Step"))
async def mcp_delete_dynamic_step(slug: str) -> dict:
    """Delete a dynamic step by slug.

    Args:
        slug: Dynamic step identifier to delete
    """
    return await delete_dynamic_step(slug)


# ============================================================================
# Diagram tools
# ============================================================================


@mcp.tool(annotations=diagram_annotation("System Context Diagram"))
async def mcp_get_system_context_diagram(system_slug: str) -> dict:
    """Generate a system context diagram.

    Shows a software system in its environment: users (persons) and other
    systems it interacts with. The highest level of C4 diagrams.

    Args:
        system_slug: Software system to show context for
    """
    return await get_system_context_diagram(system_slug)


@mcp.tool(annotations=diagram_annotation("Container Diagram"))
async def mcp_get_container_diagram(system_slug: str) -> dict:
    """Generate a container diagram.

    Shows the containers that make up a software system and their
    relationships. Zooms into a system context diagram.

    Args:
        system_slug: Software system to show containers for
    """
    return await get_container_diagram(system_slug)


@mcp.tool(annotations=diagram_annotation("Component Diagram"))
async def mcp_get_component_diagram(container_slug: str) -> dict:
    """Generate a component diagram.

    Shows the components within a container and their relationships.
    Zooms into a container diagram.

    Args:
        container_slug: Container to show components for
    """
    return await get_component_diagram(container_slug)


@mcp.tool(annotations=diagram_annotation("System Landscape Diagram"))
async def mcp_get_system_landscape_diagram() -> dict:
    """Generate a system landscape diagram.

    Shows all software systems and how they relate to each other and users.
    An enterprise-level view of the architecture.
    """
    return await get_system_landscape_diagram()


@mcp.tool(annotations=diagram_annotation("Deployment Diagram"))
async def mcp_get_deployment_diagram(environment: str) -> dict:
    """Generate a deployment diagram.

    Shows how containers are deployed to infrastructure nodes in a
    specific environment.

    Args:
        environment: Environment name (e.g., "production", "staging")
    """
    return await get_deployment_diagram(environment)


@mcp.tool(annotations=diagram_annotation("Dynamic Diagram"))
async def mcp_get_dynamic_diagram(sequence_name: str) -> dict:
    """Generate a dynamic (sequence) diagram.

    Shows how elements collaborate at runtime to accomplish a specific
    use case, as a numbered sequence of interactions.

    Args:
        sequence_name: Name of the dynamic sequence to visualize
    """
    return await get_dynamic_diagram(sequence_name)


def main():
    """Run the C4 MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

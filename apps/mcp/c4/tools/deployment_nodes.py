"""MCP tools for DeploymentNode CRUD operations."""

from typing import Any

from apps.mcp.shared import ResponseFormat, format_entity, paginate_results
from julee.c4.domain.use_cases.deployment_node import (
    ContainerInstanceItem,
    CreateDeploymentNodeRequest,
    DeleteDeploymentNodeRequest,
    GetDeploymentNodeRequest,
    ListDeploymentNodesRequest,
    UpdateDeploymentNodeRequest,
)
from ..context import (
    get_create_deployment_node_use_case,
    get_delete_deployment_node_use_case,
    get_get_deployment_node_use_case,
    get_list_deployment_nodes_use_case,
    get_update_deployment_node_use_case,
)


async def create_deployment_node(
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
    """Create a new deployment node."""
    use_case = get_create_deployment_node_use_case()
    instances = [ContainerInstanceItem(**ci) for ci in (container_instances or [])]
    request = CreateDeploymentNodeRequest(
        slug=slug,
        name=name,
        environment=environment,
        node_type=node_type,
        technology=technology,
        description=description,
        parent_slug=parent_slug,
        container_instances=instances,
        properties=properties or {},
        tags=tags or [],
    )
    response = await use_case.execute(request)
    return {
        "success": True,
        "entity": response.deployment_node.model_dump(),
    }


async def get_deployment_node(slug: str, format: str = "full") -> dict:
    """Get a deployment node by slug.

    Args:
        slug: Deployment node slug
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with deployment node data
    """
    use_case = get_get_deployment_node_use_case()
    response = await use_case.execute(GetDeploymentNodeRequest(slug=slug))
    if not response.deployment_node:
        return {"entity": None, "found": False}
    return {
        "entity": format_entity(
            response.deployment_node.model_dump(),
            ResponseFormat.from_string(format),
            "deployment_node",
        ),
        "found": True,
    }


async def list_deployment_nodes(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all deployment nodes with pagination.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"

    Returns:
        Response with paginated deployment nodes list
    """
    use_case = get_list_deployment_nodes_use_case()
    response = await use_case.execute(ListDeploymentNodesRequest())

    # Format entities based on requested verbosity
    fmt = ResponseFormat.from_string(format)
    all_entities = [
        format_entity(n.model_dump(), fmt, "deployment_node")
        for n in response.deployment_nodes
    ]

    # Apply pagination
    return paginate_results(all_entities, limit=limit, offset=offset)


async def update_deployment_node(
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
    """Update an existing deployment node."""
    use_case = get_update_deployment_node_use_case()
    instances = None
    if container_instances is not None:
        instances = [ContainerInstanceItem(**ci) for ci in container_instances]
    request = UpdateDeploymentNodeRequest(
        slug=slug,
        name=name,
        environment=environment,
        node_type=node_type,
        technology=technology,
        description=description,
        parent_slug=parent_slug,
        container_instances=instances,
        properties=properties,
        tags=tags,
    )
    response = await use_case.execute(request)
    if not response.found:
        return {"success": False, "entity": None}
    return {
        "success": True,
        "entity": (
            response.deployment_node.model_dump() if response.deployment_node else None
        ),
    }


async def delete_deployment_node(slug: str) -> dict:
    """Delete a deployment node by slug."""
    use_case = get_delete_deployment_node_use_case()
    response = await use_case.execute(DeleteDeploymentNodeRequest(slug=slug))
    return {"success": response.deleted, "entity": None}

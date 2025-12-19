"""MCP tools for DeploymentNode CRUD operations."""

from typing import Any

from ...c4_api.requests import (
    ContainerInstanceInput,
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
    instances = [ContainerInstanceInput(**ci) for ci in (container_instances or [])]
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


async def get_deployment_node(slug: str) -> dict:
    """Get a deployment node by slug."""
    use_case = get_get_deployment_node_use_case()
    response = await use_case.execute(GetDeploymentNodeRequest(slug=slug))
    if not response.deployment_node:
        return {"entity": None, "found": False}
    return {
        "entity": response.deployment_node.model_dump(),
        "found": True,
    }


async def list_deployment_nodes() -> dict:
    """List all deployment nodes."""
    use_case = get_list_deployment_nodes_use_case()
    response = await use_case.execute(ListDeploymentNodesRequest())
    return {
        "entities": [n.model_dump() for n in response.deployment_nodes],
        "count": len(response.deployment_nodes),
    }


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
        instances = [ContainerInstanceInput(**ci) for ci in container_instances]
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
        "entity": response.deployment_node.model_dump() if response.deployment_node else None,
    }


async def delete_deployment_node(slug: str) -> dict:
    """Delete a deployment node by slug."""
    use_case = get_delete_deployment_node_use_case()
    response = await use_case.execute(DeleteDeploymentNodeRequest(slug=slug))
    return {"success": response.deleted, "entity": None}

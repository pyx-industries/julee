"""C4 architecture model routes.

Routes for /c4/* endpoints covering software systems, containers, components,
relationships, deployment nodes, dynamic steps, and diagram generation.
"""

from fastapi import APIRouter, Depends, HTTPException, Path

from julee.c4.use_cases.crud import (
    CreateComponentUseCase,
    CreateContainerUseCase,
    CreateDeploymentNodeUseCase,
    CreateDynamicStepUseCase,
    CreateRelationshipUseCase,
    CreateSoftwareSystemUseCase,
    DeleteComponentUseCase,
    DeleteContainerUseCase,
    DeleteDeploymentNodeUseCase,
    DeleteDynamicStepUseCase,
    DeleteRelationshipUseCase,
    DeleteSoftwareSystemUseCase,
    GetComponentUseCase,
    GetContainerUseCase,
    GetDeploymentNodeUseCase,
    GetDynamicStepUseCase,
    GetRelationshipUseCase,
    GetSoftwareSystemUseCase,
    ListComponentsUseCase,
    ListContainersUseCase,
    ListDeploymentNodesUseCase,
    ListDynamicStepsUseCase,
    ListRelationshipsUseCase,
    ListSoftwareSystemsUseCase,
    UpdateComponentUseCase,
    UpdateContainerUseCase,
    UpdateDeploymentNodeUseCase,
    UpdateDynamicStepUseCase,
    UpdateRelationshipUseCase,
    UpdateSoftwareSystemUseCase,
)
from julee.c4.use_cases.diagrams.component_diagram import GetComponentDiagramUseCase
from julee.c4.use_cases.diagrams.container_diagram import GetContainerDiagramUseCase
from julee.c4.use_cases.diagrams.deployment_diagram import GetDeploymentDiagramUseCase
from julee.c4.use_cases.diagrams.dynamic_diagram import GetDynamicDiagramUseCase
from julee.c4.use_cases.diagrams.system_context import GetSystemContextDiagramUseCase
from julee.c4.use_cases.diagrams.system_landscape import GetSystemLandscapeDiagramUseCase

from ..dependencies import (
    get_component_diagram_use_case,
    get_container_diagram_use_case,
    get_create_component_use_case,
    get_create_container_use_case,
    get_create_deployment_node_use_case,
    get_create_dynamic_step_use_case,
    get_create_relationship_use_case,
    get_create_software_system_use_case,
    get_delete_component_use_case,
    get_delete_container_use_case,
    get_delete_deployment_node_use_case,
    get_delete_dynamic_step_use_case,
    get_delete_relationship_use_case,
    get_delete_software_system_use_case,
    get_deployment_diagram_use_case,
    get_dynamic_diagram_use_case,
    get_get_component_use_case,
    get_get_container_use_case,
    get_get_deployment_node_use_case,
    get_get_dynamic_step_use_case,
    get_get_relationship_use_case,
    get_get_software_system_use_case,
    get_list_components_use_case,
    get_list_containers_use_case,
    get_list_deployment_nodes_use_case,
    get_list_dynamic_steps_use_case,
    get_list_relationships_use_case,
    get_list_software_systems_use_case,
    get_system_context_diagram_use_case,
    get_system_landscape_diagram_use_case,
    get_update_component_use_case,
    get_update_container_use_case,
    get_update_deployment_node_use_case,
    get_update_dynamic_step_use_case,
    get_update_relationship_use_case,
    get_update_software_system_use_case,
)
from ..requests import (
    CreateComponentRequest,
    CreateContainerRequest,
    CreateDeploymentNodeRequest,
    CreateDynamicStepRequest,
    CreateRelationshipRequest,
    CreateSoftwareSystemRequest,
    DeleteComponentRequest,
    DeleteContainerRequest,
    DeleteDeploymentNodeRequest,
    DeleteDynamicStepRequest,
    DeleteRelationshipRequest,
    DeleteSoftwareSystemRequest,
    GetComponentRequest,
    GetContainerRequest,
    GetDeploymentNodeRequest,
    GetDynamicStepRequest,
    GetRelationshipRequest,
    GetSoftwareSystemRequest,
    ListComponentsRequest,
    ListContainersRequest,
    ListDeploymentNodesRequest,
    ListDynamicStepsRequest,
    ListRelationshipsRequest,
    ListSoftwareSystemsRequest,
    UpdateComponentRequest,
    UpdateContainerRequest,
    UpdateDeploymentNodeRequest,
    UpdateDynamicStepRequest,
    UpdateRelationshipRequest,
    UpdateSoftwareSystemRequest,
)
from ..responses import (
    CreateComponentResponse,
    CreateContainerResponse,
    CreateDeploymentNodeResponse,
    CreateDynamicStepResponse,
    CreateRelationshipResponse,
    CreateSoftwareSystemResponse,
    GetComponentResponse,
    GetContainerResponse,
    GetDeploymentNodeResponse,
    GetDynamicStepResponse,
    GetRelationshipResponse,
    GetSoftwareSystemResponse,
    ListComponentsResponse,
    ListContainersResponse,
    ListDeploymentNodesResponse,
    ListDynamicStepsResponse,
    ListRelationshipsResponse,
    ListSoftwareSystemsResponse,
    UpdateComponentResponse,
    UpdateContainerResponse,
    UpdateDeploymentNodeResponse,
    UpdateDynamicStepResponse,
    UpdateRelationshipResponse,
    UpdateSoftwareSystemResponse,
)

router = APIRouter(prefix="/c4", tags=["C4"])


# ============================================================================
# Software Systems
# ============================================================================


@router.get("/systems", response_model=ListSoftwareSystemsResponse)
async def list_software_systems(
    use_case: ListSoftwareSystemsUseCase = Depends(get_list_software_systems_use_case),
) -> ListSoftwareSystemsResponse:
    """List all software systems."""
    return await use_case.execute(ListSoftwareSystemsRequest())


@router.get("/systems/{slug}", response_model=GetSoftwareSystemResponse)
async def get_software_system(
    slug: str = Path(..., description="Software system slug"),
    use_case: GetSoftwareSystemUseCase = Depends(get_get_software_system_use_case),
) -> GetSoftwareSystemResponse:
    """Get a software system by slug."""
    response = await use_case.execute(GetSoftwareSystemRequest(slug=slug))
    if not response.software_system:
        raise HTTPException(
            status_code=404, detail=f"Software system '{slug}' not found"
        )
    return response


@router.post("/systems", response_model=CreateSoftwareSystemResponse, status_code=201)
async def create_software_system(
    request: CreateSoftwareSystemRequest,
    use_case: CreateSoftwareSystemUseCase = Depends(
        get_create_software_system_use_case
    ),
) -> CreateSoftwareSystemResponse:
    """Create a new software system."""
    return await use_case.execute(request)


@router.put("/systems/{slug}", response_model=UpdateSoftwareSystemResponse)
async def update_software_system(
    slug: str,
    request: UpdateSoftwareSystemRequest,
    use_case: UpdateSoftwareSystemUseCase = Depends(
        get_update_software_system_use_case
    ),
) -> UpdateSoftwareSystemResponse:
    """Update an existing software system."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(
            status_code=404, detail=f"Software system '{slug}' not found"
        )
    return response


@router.delete("/systems/{slug}", status_code=204)
async def delete_software_system(
    slug: str,
    use_case: DeleteSoftwareSystemUseCase = Depends(
        get_delete_software_system_use_case
    ),
) -> None:
    """Delete a software system."""
    response = await use_case.execute(DeleteSoftwareSystemRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(
            status_code=404, detail=f"Software system '{slug}' not found"
        )


# ============================================================================
# Containers
# ============================================================================


@router.get("/containers", response_model=ListContainersResponse)
async def list_containers(
    use_case: ListContainersUseCase = Depends(get_list_containers_use_case),
) -> ListContainersResponse:
    """List all containers."""
    return await use_case.execute(ListContainersRequest())


@router.get("/containers/{slug}", response_model=GetContainerResponse)
async def get_container(
    slug: str = Path(..., description="Container slug"),
    use_case: GetContainerUseCase = Depends(get_get_container_use_case),
) -> GetContainerResponse:
    """Get a container by slug."""
    response = await use_case.execute(GetContainerRequest(slug=slug))
    if not response.container:
        raise HTTPException(status_code=404, detail=f"Container '{slug}' not found")
    return response


@router.post("/containers", response_model=CreateContainerResponse, status_code=201)
async def create_container(
    request: CreateContainerRequest,
    use_case: CreateContainerUseCase = Depends(get_create_container_use_case),
) -> CreateContainerResponse:
    """Create a new container."""
    return await use_case.execute(request)


@router.put("/containers/{slug}", response_model=UpdateContainerResponse)
async def update_container(
    slug: str,
    request: UpdateContainerRequest,
    use_case: UpdateContainerUseCase = Depends(get_update_container_use_case),
) -> UpdateContainerResponse:
    """Update an existing container."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Container '{slug}' not found")
    return response


@router.delete("/containers/{slug}", status_code=204)
async def delete_container(
    slug: str,
    use_case: DeleteContainerUseCase = Depends(get_delete_container_use_case),
) -> None:
    """Delete a container."""
    response = await use_case.execute(DeleteContainerRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Container '{slug}' not found")


# ============================================================================
# Components
# ============================================================================


@router.get("/components", response_model=ListComponentsResponse)
async def list_components(
    use_case: ListComponentsUseCase = Depends(get_list_components_use_case),
) -> ListComponentsResponse:
    """List all components."""
    return await use_case.execute(ListComponentsRequest())


@router.get("/components/{slug}", response_model=GetComponentResponse)
async def get_component(
    slug: str = Path(..., description="Component slug"),
    use_case: GetComponentUseCase = Depends(get_get_component_use_case),
) -> GetComponentResponse:
    """Get a component by slug."""
    response = await use_case.execute(GetComponentRequest(slug=slug))
    if not response.component:
        raise HTTPException(status_code=404, detail=f"Component '{slug}' not found")
    return response


@router.post("/components", response_model=CreateComponentResponse, status_code=201)
async def create_component(
    request: CreateComponentRequest,
    use_case: CreateComponentUseCase = Depends(get_create_component_use_case),
) -> CreateComponentResponse:
    """Create a new component."""
    return await use_case.execute(request)


@router.put("/components/{slug}", response_model=UpdateComponentResponse)
async def update_component(
    slug: str,
    request: UpdateComponentRequest,
    use_case: UpdateComponentUseCase = Depends(get_update_component_use_case),
) -> UpdateComponentResponse:
    """Update an existing component."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Component '{slug}' not found")
    return response


@router.delete("/components/{slug}", status_code=204)
async def delete_component(
    slug: str,
    use_case: DeleteComponentUseCase = Depends(get_delete_component_use_case),
) -> None:
    """Delete a component."""
    response = await use_case.execute(DeleteComponentRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Component '{slug}' not found")


# ============================================================================
# Relationships
# ============================================================================


@router.get("/relationships", response_model=ListRelationshipsResponse)
async def list_relationships(
    use_case: ListRelationshipsUseCase = Depends(get_list_relationships_use_case),
) -> ListRelationshipsResponse:
    """List all relationships."""
    return await use_case.execute(ListRelationshipsRequest())


@router.get("/relationships/{slug}", response_model=GetRelationshipResponse)
async def get_relationship(
    slug: str = Path(..., description="Relationship slug"),
    use_case: GetRelationshipUseCase = Depends(get_get_relationship_use_case),
) -> GetRelationshipResponse:
    """Get a relationship by slug."""
    response = await use_case.execute(GetRelationshipRequest(slug=slug))
    if not response.relationship:
        raise HTTPException(status_code=404, detail=f"Relationship '{slug}' not found")
    return response


@router.post(
    "/relationships", response_model=CreateRelationshipResponse, status_code=201
)
async def create_relationship(
    request: CreateRelationshipRequest,
    use_case: CreateRelationshipUseCase = Depends(get_create_relationship_use_case),
) -> CreateRelationshipResponse:
    """Create a new relationship."""
    return await use_case.execute(request)


@router.put("/relationships/{slug}", response_model=UpdateRelationshipResponse)
async def update_relationship(
    slug: str,
    request: UpdateRelationshipRequest,
    use_case: UpdateRelationshipUseCase = Depends(get_update_relationship_use_case),
) -> UpdateRelationshipResponse:
    """Update an existing relationship."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Relationship '{slug}' not found")
    return response


@router.delete("/relationships/{slug}", status_code=204)
async def delete_relationship(
    slug: str,
    use_case: DeleteRelationshipUseCase = Depends(get_delete_relationship_use_case),
) -> None:
    """Delete a relationship."""
    response = await use_case.execute(DeleteRelationshipRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Relationship '{slug}' not found")


# ============================================================================
# Deployment Nodes
# ============================================================================


@router.get("/deployment-nodes", response_model=ListDeploymentNodesResponse)
async def list_deployment_nodes(
    use_case: ListDeploymentNodesUseCase = Depends(get_list_deployment_nodes_use_case),
) -> ListDeploymentNodesResponse:
    """List all deployment nodes."""
    return await use_case.execute(ListDeploymentNodesRequest())


@router.get("/deployment-nodes/{slug}", response_model=GetDeploymentNodeResponse)
async def get_deployment_node(
    slug: str = Path(..., description="Deployment node slug"),
    use_case: GetDeploymentNodeUseCase = Depends(get_get_deployment_node_use_case),
) -> GetDeploymentNodeResponse:
    """Get a deployment node by slug."""
    response = await use_case.execute(GetDeploymentNodeRequest(slug=slug))
    if not response.deployment_node:
        raise HTTPException(
            status_code=404, detail=f"Deployment node '{slug}' not found"
        )
    return response


@router.post(
    "/deployment-nodes", response_model=CreateDeploymentNodeResponse, status_code=201
)
async def create_deployment_node(
    request: CreateDeploymentNodeRequest,
    use_case: CreateDeploymentNodeUseCase = Depends(
        get_create_deployment_node_use_case
    ),
) -> CreateDeploymentNodeResponse:
    """Create a new deployment node."""
    return await use_case.execute(request)


@router.put("/deployment-nodes/{slug}", response_model=UpdateDeploymentNodeResponse)
async def update_deployment_node(
    slug: str,
    request: UpdateDeploymentNodeRequest,
    use_case: UpdateDeploymentNodeUseCase = Depends(
        get_update_deployment_node_use_case
    ),
) -> UpdateDeploymentNodeResponse:
    """Update an existing deployment node."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(
            status_code=404, detail=f"Deployment node '{slug}' not found"
        )
    return response


@router.delete("/deployment-nodes/{slug}", status_code=204)
async def delete_deployment_node(
    slug: str,
    use_case: DeleteDeploymentNodeUseCase = Depends(
        get_delete_deployment_node_use_case
    ),
) -> None:
    """Delete a deployment node."""
    response = await use_case.execute(DeleteDeploymentNodeRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(
            status_code=404, detail=f"Deployment node '{slug}' not found"
        )


# ============================================================================
# Dynamic Steps
# ============================================================================


@router.get("/dynamic-steps", response_model=ListDynamicStepsResponse)
async def list_dynamic_steps(
    use_case: ListDynamicStepsUseCase = Depends(get_list_dynamic_steps_use_case),
) -> ListDynamicStepsResponse:
    """List all dynamic steps."""
    return await use_case.execute(ListDynamicStepsRequest())


@router.get("/dynamic-steps/{slug}", response_model=GetDynamicStepResponse)
async def get_dynamic_step(
    slug: str = Path(..., description="Dynamic step slug"),
    use_case: GetDynamicStepUseCase = Depends(get_get_dynamic_step_use_case),
) -> GetDynamicStepResponse:
    """Get a dynamic step by slug."""
    response = await use_case.execute(GetDynamicStepRequest(slug=slug))
    if not response.dynamic_step:
        raise HTTPException(status_code=404, detail=f"Dynamic step '{slug}' not found")
    return response


@router.post(
    "/dynamic-steps", response_model=CreateDynamicStepResponse, status_code=201
)
async def create_dynamic_step(
    request: CreateDynamicStepRequest,
    use_case: CreateDynamicStepUseCase = Depends(get_create_dynamic_step_use_case),
) -> CreateDynamicStepResponse:
    """Create a new dynamic step."""
    return await use_case.execute(request)


@router.put("/dynamic-steps/{slug}", response_model=UpdateDynamicStepResponse)
async def update_dynamic_step(
    slug: str,
    request: UpdateDynamicStepRequest,
    use_case: UpdateDynamicStepUseCase = Depends(get_update_dynamic_step_use_case),
) -> UpdateDynamicStepResponse:
    """Update an existing dynamic step."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Dynamic step '{slug}' not found")
    return response


@router.delete("/dynamic-steps/{slug}", status_code=204)
async def delete_dynamic_step(
    slug: str,
    use_case: DeleteDynamicStepUseCase = Depends(get_delete_dynamic_step_use_case),
) -> None:
    """Delete a dynamic step."""
    response = await use_case.execute(DeleteDynamicStepRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Dynamic step '{slug}' not found")


# ============================================================================
# Diagrams
# ============================================================================


@router.get("/diagrams/context/{system_slug}")
async def get_system_context_diagram(
    system_slug: str = Path(..., description="Software system slug"),
    use_case: GetSystemContextDiagramUseCase = Depends(
        get_system_context_diagram_use_case
    ),
) -> dict:
    """Generate a system context diagram for a software system."""
    result = await use_case.execute(system_slug)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Software system '{system_slug}' not found"
        )
    return {
        "system": result.system.model_dump(),
        "external_systems": [s.model_dump() for s in result.external_systems],
        "person_slugs": result.person_slugs,
        "relationships": [r.model_dump() for r in result.relationships],
    }


@router.get("/diagrams/containers/{system_slug}")
async def get_container_diagram(
    system_slug: str = Path(..., description="Software system slug"),
    use_case: GetContainerDiagramUseCase = Depends(get_container_diagram_use_case),
) -> dict:
    """Generate a container diagram for a software system."""
    result = await use_case.execute(system_slug)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Software system '{system_slug}' not found"
        )
    return {
        "system": result.system.model_dump(),
        "containers": [c.model_dump() for c in result.containers],
        "external_systems": [s.model_dump() for s in result.external_systems],
        "person_slugs": result.person_slugs,
        "relationships": [r.model_dump() for r in result.relationships],
    }


@router.get("/diagrams/components/{container_slug}")
async def get_component_diagram(
    container_slug: str = Path(..., description="Container slug"),
    use_case: GetComponentDiagramUseCase = Depends(get_component_diagram_use_case),
) -> dict:
    """Generate a component diagram for a container."""
    result = await use_case.execute(container_slug)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Container '{container_slug}' not found"
        )
    return {
        "system": result.system.model_dump(),
        "container": result.container.model_dump(),
        "components": [c.model_dump() for c in result.components],
        "external_containers": [c.model_dump() for c in result.external_containers],
        "external_systems": [s.model_dump() for s in result.external_systems],
        "person_slugs": result.person_slugs,
        "relationships": [r.model_dump() for r in result.relationships],
    }


@router.get("/diagrams/landscape")
async def get_system_landscape_diagram(
    use_case: GetSystemLandscapeDiagramUseCase = Depends(
        get_system_landscape_diagram_use_case
    ),
) -> dict:
    """Generate a system landscape diagram showing all systems."""
    result = await use_case.execute()
    return {
        "systems": [s.model_dump() for s in result.systems],
        "person_slugs": result.person_slugs,
        "relationships": [r.model_dump() for r in result.relationships],
    }


@router.get("/diagrams/deployment/{environment}")
async def get_deployment_diagram(
    environment: str = Path(..., description="Deployment environment"),
    use_case: GetDeploymentDiagramUseCase = Depends(get_deployment_diagram_use_case),
) -> dict:
    """Generate a deployment diagram for an environment."""
    result = await use_case.execute(environment)
    return {
        "environment": result.environment,
        "nodes": [n.model_dump() for n in result.nodes],
        "containers": [c.model_dump() for c in result.containers],
        "relationships": [r.model_dump() for r in result.relationships],
    }


@router.get("/diagrams/dynamic/{sequence_name}")
async def get_dynamic_diagram(
    sequence_name: str = Path(..., description="Dynamic sequence name"),
    use_case: GetDynamicDiagramUseCase = Depends(get_dynamic_diagram_use_case),
) -> dict:
    """Generate a dynamic diagram for a sequence."""
    result = await use_case.execute(sequence_name)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Sequence '{sequence_name}' not found"
        )
    return {
        "sequence_name": result.sequence_name,
        "steps": [s.model_dump() for s in result.steps],
        "systems": [s.model_dump() for s in result.systems],
        "containers": [c.model_dump() for c in result.containers],
        "components": [c.model_dump() for c in result.components],
        "person_slugs": result.person_slugs,
    }

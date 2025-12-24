"""Solution domain routes.

Routes for /solution/* endpoints: accelerators, integrations, apps.
All operations go through use-case classes following clean architecture.
"""

from fastapi import APIRouter, Depends, HTTPException, Path

from julee.hcd.use_cases.accelerator import (
    CreateAcceleratorUseCase,
    DeleteAcceleratorUseCase,
    GetAcceleratorUseCase,
    ListAcceleratorsUseCase,
    UpdateAcceleratorUseCase,
)
from julee.hcd.use_cases.app import (
    CreateAppUseCase,
    DeleteAppUseCase,
    GetAppUseCase,
    ListAppsUseCase,
    UpdateAppUseCase,
)
from julee.hcd.use_cases.integration import (
    CreateIntegrationUseCase,
    DeleteIntegrationUseCase,
    GetIntegrationUseCase,
    ListIntegrationsUseCase,
    UpdateIntegrationUseCase,
)
from ..dependencies import (
    get_create_accelerator_use_case,
    get_create_app_use_case,
    get_create_integration_use_case,
    get_delete_accelerator_use_case,
    get_delete_app_use_case,
    get_delete_integration_use_case,
    get_get_accelerator_use_case,
    get_get_app_use_case,
    get_get_integration_use_case,
    get_list_accelerators_use_case,
    get_list_apps_use_case,
    get_list_integrations_use_case,
    get_update_accelerator_use_case,
    get_update_app_use_case,
    get_update_integration_use_case,
)
from ..requests import (
    CreateAcceleratorRequest,
    CreateAppRequest,
    CreateIntegrationRequest,
    DeleteAcceleratorRequest,
    DeleteAppRequest,
    DeleteIntegrationRequest,
    GetAcceleratorRequest,
    GetAppRequest,
    GetIntegrationRequest,
    ListAcceleratorsRequest,
    ListAppsRequest,
    ListIntegrationsRequest,
    UpdateAcceleratorRequest,
    UpdateAppRequest,
    UpdateIntegrationRequest,
)
from ..responses import (
    CreateAcceleratorResponse,
    CreateAppResponse,
    CreateIntegrationResponse,
    GetAcceleratorResponse,
    GetAppResponse,
    GetIntegrationResponse,
    ListAcceleratorsResponse,
    ListAppsResponse,
    ListIntegrationsResponse,
    UpdateAcceleratorResponse,
    UpdateAppResponse,
    UpdateIntegrationResponse,
)

router = APIRouter(prefix="/solution", tags=["Solution"])


# ============================================================================
# Accelerators
# ============================================================================


@router.get("/accelerators", response_model=ListAcceleratorsResponse)
async def list_accelerators(
    use_case: ListAcceleratorsUseCase = Depends(get_list_accelerators_use_case),
) -> ListAcceleratorsResponse:
    """List all accelerators."""
    return await use_case.execute(ListAcceleratorsRequest())


@router.get("/accelerators/{slug}", response_model=GetAcceleratorResponse)
async def get_accelerator(
    slug: str = Path(..., description="Accelerator slug"),
    use_case: GetAcceleratorUseCase = Depends(get_get_accelerator_use_case),
) -> GetAcceleratorResponse:
    """Get an accelerator by slug."""
    response = await use_case.execute(GetAcceleratorRequest(slug=slug))
    if not response.accelerator:
        raise HTTPException(status_code=404, detail=f"Accelerator '{slug}' not found")
    return response


@router.post("/accelerators", response_model=CreateAcceleratorResponse, status_code=201)
async def create_accelerator(
    request: CreateAcceleratorRequest,
    use_case: CreateAcceleratorUseCase = Depends(get_create_accelerator_use_case),
) -> CreateAcceleratorResponse:
    """Create a new accelerator."""
    return await use_case.execute(request)


@router.put("/accelerators/{slug}", response_model=UpdateAcceleratorResponse)
async def update_accelerator(
    slug: str,
    request: UpdateAcceleratorRequest,
    use_case: UpdateAcceleratorUseCase = Depends(get_update_accelerator_use_case),
) -> UpdateAcceleratorResponse:
    """Update an existing accelerator."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Accelerator '{slug}' not found")
    return response


@router.delete("/accelerators/{slug}", status_code=204)
async def delete_accelerator(
    slug: str,
    use_case: DeleteAcceleratorUseCase = Depends(get_delete_accelerator_use_case),
) -> None:
    """Delete an accelerator."""
    response = await use_case.execute(DeleteAcceleratorRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Accelerator '{slug}' not found")


# ============================================================================
# Integrations
# ============================================================================


@router.get("/integrations", response_model=ListIntegrationsResponse)
async def list_integrations(
    use_case: ListIntegrationsUseCase = Depends(get_list_integrations_use_case),
) -> ListIntegrationsResponse:
    """List all integrations."""
    return await use_case.execute(ListIntegrationsRequest())


@router.get("/integrations/{slug}", response_model=GetIntegrationResponse)
async def get_integration(
    slug: str = Path(..., description="Integration slug"),
    use_case: GetIntegrationUseCase = Depends(get_get_integration_use_case),
) -> GetIntegrationResponse:
    """Get an integration by slug."""
    response = await use_case.execute(GetIntegrationRequest(slug=slug))
    if not response.integration:
        raise HTTPException(status_code=404, detail=f"Integration '{slug}' not found")
    return response


@router.post("/integrations", response_model=CreateIntegrationResponse, status_code=201)
async def create_integration(
    request: CreateIntegrationRequest,
    use_case: CreateIntegrationUseCase = Depends(get_create_integration_use_case),
) -> CreateIntegrationResponse:
    """Create a new integration."""
    return await use_case.execute(request)


@router.put("/integrations/{slug}", response_model=UpdateIntegrationResponse)
async def update_integration(
    slug: str,
    request: UpdateIntegrationRequest,
    use_case: UpdateIntegrationUseCase = Depends(get_update_integration_use_case),
) -> UpdateIntegrationResponse:
    """Update an existing integration."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Integration '{slug}' not found")
    return response


@router.delete("/integrations/{slug}", status_code=204)
async def delete_integration(
    slug: str,
    use_case: DeleteIntegrationUseCase = Depends(get_delete_integration_use_case),
) -> None:
    """Delete an integration."""
    response = await use_case.execute(DeleteIntegrationRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Integration '{slug}' not found")


# ============================================================================
# Apps
# ============================================================================


@router.get("/apps", response_model=ListAppsResponse)
async def list_apps(
    use_case: ListAppsUseCase = Depends(get_list_apps_use_case),
) -> ListAppsResponse:
    """List all apps."""
    return await use_case.execute(ListAppsRequest())


@router.get("/apps/{slug}", response_model=GetAppResponse)
async def get_app(
    slug: str = Path(..., description="App slug"),
    use_case: GetAppUseCase = Depends(get_get_app_use_case),
) -> GetAppResponse:
    """Get an app by slug."""
    response = await use_case.execute(GetAppRequest(slug=slug))
    if not response.app:
        raise HTTPException(status_code=404, detail=f"App '{slug}' not found")
    return response


@router.post("/apps", response_model=CreateAppResponse, status_code=201)
async def create_app(
    request: CreateAppRequest,
    use_case: CreateAppUseCase = Depends(get_create_app_use_case),
) -> CreateAppResponse:
    """Create a new app."""
    return await use_case.execute(request)


@router.put("/apps/{slug}", response_model=UpdateAppResponse)
async def update_app(
    slug: str,
    request: UpdateAppRequest,
    use_case: UpdateAppUseCase = Depends(get_update_app_use_case),
) -> UpdateAppResponse:
    """Update an existing app."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"App '{slug}' not found")
    return response


@router.delete("/apps/{slug}", status_code=204)
async def delete_app(
    slug: str,
    use_case: DeleteAppUseCase = Depends(get_delete_app_use_case),
) -> None:
    """Delete an app."""
    response = await use_case.execute(DeleteAppRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"App '{slug}' not found")

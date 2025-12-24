"""HCD domain routes.

Routes for /hcd/* endpoints: stories, epics, journeys, personas.
All operations go through use-case classes following clean architecture.
"""

from fastapi import APIRouter, Depends, HTTPException, Path

from julee.hcd.use_cases import (
    CreateEpicUseCase,
    CreateJourneyUseCase,
    CreateStoryUseCase,
    DeleteEpicUseCase,
    DeleteJourneyUseCase,
    DeleteStoryUseCase,
    DerivePersonasUseCase,
    GetEpicUseCase,
    GetJourneyUseCase,
    GetPersonaUseCase,
    GetStoryUseCase,
    ListEpicsUseCase,
    ListJourneysUseCase,
    ListStoriesUseCase,
    UpdateEpicUseCase,
    UpdateJourneyUseCase,
    UpdateStoryUseCase,
)
from ..dependencies import (
    get_create_epic_use_case,
    get_create_journey_use_case,
    get_create_story_use_case,
    get_delete_epic_use_case,
    get_delete_journey_use_case,
    get_delete_story_use_case,
    get_derive_personas_use_case,
    get_get_epic_use_case,
    get_get_journey_use_case,
    get_get_persona_use_case,
    get_get_story_use_case,
    get_list_epics_use_case,
    get_list_journeys_use_case,
    get_list_stories_use_case,
    get_update_epic_use_case,
    get_update_journey_use_case,
    get_update_story_use_case,
)
from ..requests import (
    CreateEpicRequest,
    CreateJourneyRequest,
    CreateStoryRequest,
    DeleteEpicRequest,
    DeleteJourneyRequest,
    DeleteStoryRequest,
    DerivePersonasRequest,
    GetEpicRequest,
    GetJourneyRequest,
    GetPersonaRequest,
    GetStoryRequest,
    ListEpicsRequest,
    ListJourneysRequest,
    ListStoriesRequest,
    UpdateEpicRequest,
    UpdateJourneyRequest,
    UpdateStoryRequest,
)
from ..responses import (
    CreateEpicResponse,
    CreateJourneyResponse,
    CreateStoryResponse,
    DerivePersonasResponse,
    GetEpicResponse,
    GetJourneyResponse,
    GetPersonaResponse,
    GetStoryResponse,
    ListEpicsResponse,
    ListJourneysResponse,
    ListStoriesResponse,
    UpdateEpicResponse,
    UpdateJourneyResponse,
    UpdateStoryResponse,
)

router = APIRouter(prefix="/hcd", tags=["HCD"])


# ============================================================================
# Stories
# ============================================================================


@router.get("/stories", response_model=ListStoriesResponse)
async def list_stories(
    use_case: ListStoriesUseCase = Depends(get_list_stories_use_case),
) -> ListStoriesResponse:
    """List all stories."""
    return await use_case.execute(ListStoriesRequest())


@router.get("/stories/{slug}", response_model=GetStoryResponse)
async def get_story(
    slug: str = Path(..., description="Story slug"),
    use_case: GetStoryUseCase = Depends(get_get_story_use_case),
) -> GetStoryResponse:
    """Get a story by slug."""
    response = await use_case.execute(GetStoryRequest(slug=slug))
    if not response.story:
        raise HTTPException(status_code=404, detail=f"Story '{slug}' not found")
    return response


@router.post("/stories", response_model=CreateStoryResponse, status_code=201)
async def create_story(
    request: CreateStoryRequest,
    use_case: CreateStoryUseCase = Depends(get_create_story_use_case),
) -> CreateStoryResponse:
    """Create a new story."""
    return await use_case.execute(request)


@router.put("/stories/{slug}", response_model=UpdateStoryResponse)
async def update_story(
    slug: str,
    request: UpdateStoryRequest,
    use_case: UpdateStoryUseCase = Depends(get_update_story_use_case),
) -> UpdateStoryResponse:
    """Update an existing story."""
    # Ensure slug from path is used
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Story '{slug}' not found")
    return response


@router.delete("/stories/{slug}", status_code=204)
async def delete_story(
    slug: str,
    use_case: DeleteStoryUseCase = Depends(get_delete_story_use_case),
) -> None:
    """Delete a story."""
    response = await use_case.execute(DeleteStoryRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Story '{slug}' not found")


# ============================================================================
# Epics
# ============================================================================


@router.get("/epics", response_model=ListEpicsResponse)
async def list_epics(
    use_case: ListEpicsUseCase = Depends(get_list_epics_use_case),
) -> ListEpicsResponse:
    """List all epics."""
    return await use_case.execute(ListEpicsRequest())


@router.get("/epics/{slug}", response_model=GetEpicResponse)
async def get_epic(
    slug: str = Path(..., description="Epic slug"),
    use_case: GetEpicUseCase = Depends(get_get_epic_use_case),
) -> GetEpicResponse:
    """Get an epic by slug."""
    response = await use_case.execute(GetEpicRequest(slug=slug))
    if not response.epic:
        raise HTTPException(status_code=404, detail=f"Epic '{slug}' not found")
    return response


@router.post("/epics", response_model=CreateEpicResponse, status_code=201)
async def create_epic(
    request: CreateEpicRequest,
    use_case: CreateEpicUseCase = Depends(get_create_epic_use_case),
) -> CreateEpicResponse:
    """Create a new epic."""
    return await use_case.execute(request)


@router.put("/epics/{slug}", response_model=UpdateEpicResponse)
async def update_epic(
    slug: str,
    request: UpdateEpicRequest,
    use_case: UpdateEpicUseCase = Depends(get_update_epic_use_case),
) -> UpdateEpicResponse:
    """Update an existing epic."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Epic '{slug}' not found")
    return response


@router.delete("/epics/{slug}", status_code=204)
async def delete_epic(
    slug: str,
    use_case: DeleteEpicUseCase = Depends(get_delete_epic_use_case),
) -> None:
    """Delete an epic."""
    response = await use_case.execute(DeleteEpicRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Epic '{slug}' not found")


# ============================================================================
# Journeys
# ============================================================================


@router.get("/journeys", response_model=ListJourneysResponse)
async def list_journeys(
    use_case: ListJourneysUseCase = Depends(get_list_journeys_use_case),
) -> ListJourneysResponse:
    """List all journeys."""
    return await use_case.execute(ListJourneysRequest())


@router.get("/journeys/{slug}", response_model=GetJourneyResponse)
async def get_journey(
    slug: str = Path(..., description="Journey slug"),
    use_case: GetJourneyUseCase = Depends(get_get_journey_use_case),
) -> GetJourneyResponse:
    """Get a journey by slug."""
    response = await use_case.execute(GetJourneyRequest(slug=slug))
    if not response.journey:
        raise HTTPException(status_code=404, detail=f"Journey '{slug}' not found")
    return response


@router.post("/journeys", response_model=CreateJourneyResponse, status_code=201)
async def create_journey(
    request: CreateJourneyRequest,
    use_case: CreateJourneyUseCase = Depends(get_create_journey_use_case),
) -> CreateJourneyResponse:
    """Create a new journey."""
    return await use_case.execute(request)


@router.put("/journeys/{slug}", response_model=UpdateJourneyResponse)
async def update_journey(
    slug: str,
    request: UpdateJourneyRequest,
    use_case: UpdateJourneyUseCase = Depends(get_update_journey_use_case),
) -> UpdateJourneyResponse:
    """Update an existing journey."""
    request.slug = slug
    response = await use_case.execute(request)
    if not response.found:
        raise HTTPException(status_code=404, detail=f"Journey '{slug}' not found")
    return response


@router.delete("/journeys/{slug}", status_code=204)
async def delete_journey(
    slug: str,
    use_case: DeleteJourneyUseCase = Depends(get_delete_journey_use_case),
) -> None:
    """Delete a journey."""
    response = await use_case.execute(DeleteJourneyRequest(slug=slug))
    if not response.deleted:
        raise HTTPException(status_code=404, detail=f"Journey '{slug}' not found")


# ============================================================================
# Personas (read-only, derived from stories)
# ============================================================================


@router.get("/personas", response_model=DerivePersonasResponse)
async def list_personas(
    use_case: DerivePersonasUseCase = Depends(get_derive_personas_use_case),
) -> DerivePersonasResponse:
    """List all personas (derived from stories and epics)."""
    return await use_case.execute(DerivePersonasRequest())


@router.get("/personas/{name}", response_model=GetPersonaResponse)
async def get_persona(
    name: str = Path(..., description="Persona name"),
    use_case: GetPersonaUseCase = Depends(get_get_persona_use_case),
) -> GetPersonaResponse:
    """Get a persona by name (derived from stories and epics)."""
    response = await use_case.execute(GetPersonaRequest(name=name))
    if not response.persona:
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")
    return response

"""List journeys use case using FilterableListUseCase."""

from pydantic import BaseModel, Field

from julee.core.use_cases.generic_crud import (
    FilterableListUseCase,
    make_list_request,
)
from julee.hcd.entities.journey import Journey
from julee.hcd.repositories.journey import JourneyRepository

# Dynamic request from repository's list_filtered signature
ListJourneysRequest = make_list_request("ListJourneysRequest", JourneyRepository)


class ListJourneysResponse(BaseModel):
    """Response from listing journeys.

    Uses validation_alias to accept 'entities' from generic CRUD infrastructure
    while serializing as 'journeys' for API consumers.
    """

    journeys: list[Journey] = Field(default=[], validation_alias="entities")

    @property
    def entities(self) -> list[Journey]:
        """Alias for generic list operations."""
        return self.journeys

    @property
    def count(self) -> int:
        """Number of journeys returned."""
        return len(self.journeys)


class ListJourneysUseCase(FilterableListUseCase[Journey, JourneyRepository]):
    """List journeys with optional filtering.

    Filters are derived from JourneyRepository.list_filtered() signature:
    - persona: Filter to journeys for this persona
    - contains_story: Filter to journeys containing this story title

    Examples:
        # All journeys
        response = use_case.execute(ListJourneysRequest())

        # Journeys for a persona
        response = use_case.execute(ListJourneysRequest(persona="Admin"))

        # Journeys containing a specific story
        response = use_case.execute(ListJourneysRequest(
            contains_story="Upload Scheme Documentation"
        ))
    """

    response_cls = ListJourneysResponse

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency."""
        super().__init__(journey_repo)

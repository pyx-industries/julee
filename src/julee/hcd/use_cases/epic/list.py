"""List epics use case using FilterableListUseCase."""

from pydantic import BaseModel, Field

from julee.core.use_cases.generic_crud import (
    FilterableListUseCase,
    make_list_request,
)
from julee.hcd.entities.epic import Epic
from julee.hcd.repositories.epic import EpicRepository

# Dynamic request from repository's list_filtered signature
ListEpicsRequest = make_list_request("ListEpicsRequest", EpicRepository)


class ListEpicsResponse(BaseModel):
    """Response from listing epics.

    Uses validation_alias to accept 'entities' from generic CRUD infrastructure
    while serializing as 'epics' for API consumers.
    """

    epics: list[Epic] = Field(default=[], validation_alias="entities")

    @property
    def entities(self) -> list[Epic]:
        """Alias for generic list operations."""
        return self.epics

    @property
    def count(self) -> int:
        """Number of epics returned."""
        return len(self.epics)

    @property
    def total_stories(self) -> int:
        """Total stories across all epics."""
        return sum(len(e.story_refs) for e in self.epics)


class ListEpicsUseCase(FilterableListUseCase[Epic, EpicRepository]):
    """List epics with optional filtering.

    Filters are derived from EpicRepository.list_filtered() signature:
    - contains_story: Filter to epics containing this story title

    Examples:
        # All epics
        response = use_case.execute(ListEpicsRequest())

        # Epics containing a specific story
        response = use_case.execute(ListEpicsRequest(
            contains_story="Upload Scheme Documentation"
        ))
    """

    response_cls = ListEpicsResponse

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency."""
        super().__init__(epic_repo)

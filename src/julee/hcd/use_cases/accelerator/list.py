"""List accelerators use case using FilterableListUseCase."""

from pydantic import BaseModel, Field

from julee.core.use_cases.generic_crud import (
    FilterableListUseCase,
    make_list_request,
)
from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.repositories.accelerator import AcceleratorRepository

# Dynamic request from repository's list_filtered signature
ListAcceleratorsRequest = make_list_request(
    "ListAcceleratorsRequest", AcceleratorRepository
)


class ListAcceleratorsResponse(BaseModel):
    """Response from listing accelerators.

    Uses validation_alias to accept 'entities' from generic CRUD infrastructure
    while serializing as 'accelerators' for API consumers.
    """

    accelerators: list[Accelerator] = Field(default=[], validation_alias="entities")

    @property
    def entities(self) -> list[Accelerator]:
        """Alias for generic list operations."""
        return self.accelerators

    @property
    def count(self) -> int:
        """Number of accelerators returned."""
        return len(self.accelerators)


class ListAcceleratorsUseCase(FilterableListUseCase[Accelerator, AcceleratorRepository]):
    """List accelerators with optional filtering.

    Filters are derived from AcceleratorRepository.list_filtered() signature:
    - status: Filter to accelerators with this status

    Examples:
        # All accelerators
        response = use_case.execute(ListAcceleratorsRequest())

        # Active accelerators only
        response = use_case.execute(ListAcceleratorsRequest(status="active"))
    """

    response_cls = ListAcceleratorsResponse

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency."""
        super().__init__(accelerator_repo)

"""List accelerators use case with co-located request/response."""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.repositories.accelerator import AcceleratorRepository


class ListAcceleratorsRequest(BaseModel):
    """Request for listing accelerators with optional filters.

    All filters are optional. When multiple filters are specified,
    they are combined with AND logic.
    """

    status: str | None = Field(
        default=None, description="Filter to accelerators with this status"
    )
    integration_slug: str | None = Field(
        default=None,
        description="Filter to accelerators that source from or publish to this integration",
    )
    app_slug: str | None = Field(
        default=None,
        description="Filter to accelerators exposed by this app (requires app_repo)",
    )


class ListAcceleratorsResponse(BaseModel):
    """Response from listing accelerators."""

    accelerators: list[Accelerator]

    @property
    def count(self) -> int:
        """Number of accelerators returned."""
        return len(self.accelerators)

    def grouped_by_status(self) -> dict[str, list[Accelerator]]:
        """Group accelerators by status."""
        result: dict[str, list[Accelerator]] = {}
        for accel in self.accelerators:
            status = accel.status or "unknown"
            result.setdefault(status, []).append(accel)
        return result


@use_case
class ListAcceleratorsUseCase:
    """List accelerators with optional filtering.

    Supports filtering by status and/or integration dependency.
    When no filters are provided, returns all accelerators.

    Examples:
        # All accelerators
        response = use_case.execute(ListAcceleratorsRequest())

        # Active accelerators only
        response = use_case.execute(ListAcceleratorsRequest(status="active"))

        # Accelerators using Kafka
        response = use_case.execute(ListAcceleratorsRequest(integration_slug="kafka"))
    """

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(
        self, request: ListAcceleratorsRequest
    ) -> ListAcceleratorsResponse:
        """List accelerators with optional filtering.

        Args:
            request: List request with optional status and integration filters

        Returns:
            Response containing filtered list of accelerators
        """
        accelerators = await self.accelerator_repo.list_all()

        # Apply status filter
        if request.status:
            status_lower = request.status.lower()
            accelerators = [
                a for a in accelerators if a.status_normalized == status_lower
            ]

        # Apply integration filter
        if request.integration_slug:
            accelerators = [
                a
                for a in accelerators
                if a.has_integration_dependency(request.integration_slug)
            ]

        return ListAcceleratorsResponse(accelerators=accelerators)

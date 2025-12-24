"""ListSoftwareSystemsUseCase with co-located request/response.

Use case for listing all software systems.
"""

from pydantic import BaseModel

from julee.c4.entities.software_system import SoftwareSystem
from julee.c4.repositories.software_system import SoftwareSystemRepository


class ListSoftwareSystemsRequest(BaseModel):
    """Request for listing software systems."""

    pass


class ListSoftwareSystemsResponse(BaseModel):
    """Response from listing software systems."""

    software_systems: list[SoftwareSystem]


class ListSoftwareSystemsUseCase:
    """Use case for listing all software systems.

    .. usecase-documentation:: julee.c4.domain.use_cases.software_system.list:ListSoftwareSystemsUseCase
    """

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(
        self, request: ListSoftwareSystemsRequest
    ) -> ListSoftwareSystemsResponse:
        """List all software systems.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all software systems
        """
        software_systems = await self.software_system_repo.list_all()
        return ListSoftwareSystemsResponse(software_systems=software_systems)

"""ListSoftwareSystemsUseCase.

Use case for listing all software systems.
"""

from .....c4_api.requests import ListSoftwareSystemsRequest
from .....c4_api.responses import ListSoftwareSystemsResponse
from ...repositories.software_system import SoftwareSystemRepository


class ListSoftwareSystemsUseCase:
    """Use case for listing all software systems."""

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(self, request: ListSoftwareSystemsRequest) -> ListSoftwareSystemsResponse:
        """List all software systems.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all software systems
        """
        software_systems = await self.software_system_repo.list_all()
        return ListSoftwareSystemsResponse(software_systems=software_systems)

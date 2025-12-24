"""ListSoftwareSystemsUseCase.

Use case for listing all software systems.
"""

from ...repositories.software_system import SoftwareSystemRepository
from ..requests import ListSoftwareSystemsRequest
from ..responses import ListSoftwareSystemsResponse


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

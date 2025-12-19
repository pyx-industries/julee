"""GetSoftwareSystemUseCase.

Use case for getting a software system by slug.
"""

from .....c4_api.requests import GetSoftwareSystemRequest
from .....c4_api.responses import GetSoftwareSystemResponse
from ...repositories.software_system import SoftwareSystemRepository


class GetSoftwareSystemUseCase:
    """Use case for getting a software system by slug."""

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(
        self, request: GetSoftwareSystemRequest
    ) -> GetSoftwareSystemResponse:
        """Get a software system by slug.

        Args:
            request: Request containing the software system slug

        Returns:
            Response containing the software system if found, or None
        """
        software_system = await self.software_system_repo.get(request.slug)
        return GetSoftwareSystemResponse(software_system=software_system)

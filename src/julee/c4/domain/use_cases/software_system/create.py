"""CreateSoftwareSystemUseCase.

Use case for creating a new software system.
"""

from ...repositories.software_system import SoftwareSystemRepository
from ..requests import CreateSoftwareSystemRequest
from ..responses import CreateSoftwareSystemResponse


class CreateSoftwareSystemUseCase:
    """Use case for creating a software system."""

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(
        self, request: CreateSoftwareSystemRequest
    ) -> CreateSoftwareSystemResponse:
        """Create a new software system.

        Args:
            request: Software system creation request with data

        Returns:
            Response containing the created software system
        """
        software_system = request.to_domain_model()
        await self.software_system_repo.save(software_system)
        return CreateSoftwareSystemResponse(software_system=software_system)

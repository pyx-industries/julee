"""GetSoftwareSystemUseCase with co-located request/response.

Use case for getting a software system by slug.
"""

from pydantic import BaseModel

from ...models.software_system import SoftwareSystem
from ...repositories.software_system import SoftwareSystemRepository


class GetSoftwareSystemRequest(BaseModel):
    """Request for getting a software system by slug."""

    slug: str


class GetSoftwareSystemResponse(BaseModel):
    """Response from getting a software system."""

    software_system: SoftwareSystem | None


class GetSoftwareSystemUseCase:
    """Use case for getting a software system by slug.

    .. usecase-documentation:: julee.c4.domain.use_cases.software_system.get:GetSoftwareSystemUseCase
    """

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

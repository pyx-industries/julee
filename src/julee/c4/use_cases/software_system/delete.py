"""DeleteSoftwareSystemUseCase with co-located request/response.

Use case for deleting a software system.
"""

from pydantic import BaseModel

from julee.c4.repositories.software_system import SoftwareSystemRepository


class DeleteSoftwareSystemRequest(BaseModel):
    """Request for deleting a software system by slug."""

    slug: str


class DeleteSoftwareSystemResponse(BaseModel):
    """Response from deleting a software system."""

    deleted: bool


class DeleteSoftwareSystemUseCase:
    """Use case for deleting a software system.

    .. usecase-documentation:: julee.c4.domain.use_cases.software_system.delete:DeleteSoftwareSystemUseCase
    """

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(
        self, request: DeleteSoftwareSystemRequest
    ) -> DeleteSoftwareSystemResponse:
        """Delete a software system by slug.

        Args:
            request: Delete request containing the software system slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.software_system_repo.delete(request.slug)
        return DeleteSoftwareSystemResponse(deleted=deleted)

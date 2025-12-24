"""DeleteSoftwareSystemUseCase.

Use case for deleting a software system.
"""

from ...repositories.software_system import SoftwareSystemRepository
from ..requests import DeleteSoftwareSystemRequest
from ..responses import DeleteSoftwareSystemResponse


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

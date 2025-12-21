"""UpdateSoftwareSystemUseCase.

Use case for updating an existing software system.
"""

from ..requests import UpdateSoftwareSystemRequest
from ..responses import UpdateSoftwareSystemResponse
from ...repositories.software_system import SoftwareSystemRepository


class UpdateSoftwareSystemUseCase:
    """Use case for updating a software system."""

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(
        self, request: UpdateSoftwareSystemRequest
    ) -> UpdateSoftwareSystemResponse:
        """Update an existing software system.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated software system if found
        """
        existing = await self.software_system_repo.get(request.slug)
        if not existing:
            return UpdateSoftwareSystemResponse(software_system=None, found=False)

        updated = request.apply_to(existing)
        await self.software_system_repo.save(updated)
        return UpdateSoftwareSystemResponse(software_system=updated, found=True)

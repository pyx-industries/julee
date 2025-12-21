"""UpdateEpicUseCase.

Use case for updating an existing epic.
"""

from ..requests import UpdateEpicRequest
from ..responses import UpdateEpicResponse
from ...repositories.epic import EpicRepository


class UpdateEpicUseCase:
    """Use case for updating an epic."""

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: UpdateEpicRequest) -> UpdateEpicResponse:
        """Update an existing epic.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated epic if found
        """
        existing = await self.epic_repo.get(request.slug)
        if not existing:
            return UpdateEpicResponse(epic=None, found=False)

        updated = request.apply_to(existing)
        await self.epic_repo.save(updated)
        return UpdateEpicResponse(epic=updated, found=True)

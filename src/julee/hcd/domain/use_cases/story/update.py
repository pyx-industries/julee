"""UpdateStoryUseCase.

Use case for updating an existing story.
"""

from ..requests import UpdateStoryRequest
from ..responses import UpdateStoryResponse
from ...repositories.story import StoryRepository


class UpdateStoryUseCase:
    """Use case for updating a story."""

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency.

        Args:
            story_repo: Story repository instance
        """
        self.story_repo = story_repo

    async def execute(self, request: UpdateStoryRequest) -> UpdateStoryResponse:
        """Update an existing story.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated story if found
        """
        existing = await self.story_repo.get(request.slug)
        if not existing:
            return UpdateStoryResponse(story=None, found=False)

        updated = request.apply_to(existing)
        await self.story_repo.save(updated)
        return UpdateStoryResponse(story=updated, found=True)

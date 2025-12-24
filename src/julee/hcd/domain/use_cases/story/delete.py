"""DeleteStoryUseCase.

Use case for deleting a story.
"""

from ...repositories.story import StoryRepository
from ..requests import DeleteStoryRequest
from ..responses import DeleteStoryResponse


class DeleteStoryUseCase:
    """Use case for deleting a story.

    .. usecase-documentation:: julee.hcd.domain.use_cases.story.delete:DeleteStoryUseCase
    """

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency.

        Args:
            story_repo: Story repository instance
        """
        self.story_repo = story_repo

    async def execute(self, request: DeleteStoryRequest) -> DeleteStoryResponse:
        """Delete a story by slug.

        Args:
            request: Delete request containing the story slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.story_repo.delete(request.slug)
        return DeleteStoryResponse(deleted=deleted)

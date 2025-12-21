"""ListStoriesUseCase.

Use case for listing all stories.
"""

from ..requests import ListStoriesRequest
from ..responses import ListStoriesResponse
from ...repositories.story import StoryRepository


class ListStoriesUseCase:
    """Use case for listing all stories."""

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency.

        Args:
            story_repo: Story repository instance
        """
        self.story_repo = story_repo

    async def execute(self, request: ListStoriesRequest) -> ListStoriesResponse:
        """List all stories.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all stories
        """
        stories = await self.story_repo.list_all()
        return ListStoriesResponse(stories=stories)

"""CreateStoryUseCase.

Use case for creating a new story.
"""

from ..requests import CreateStoryRequest
from ..responses import CreateStoryResponse
from ...repositories.story import StoryRepository


class CreateStoryUseCase:
    """Use case for creating a story."""

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency.

        Args:
            story_repo: Story repository instance
        """
        self.story_repo = story_repo

    async def execute(self, request: CreateStoryRequest) -> CreateStoryResponse:
        """Create a new story.

        Args:
            request: Story creation request with story data

        Returns:
            Response containing the created story
        """
        story = request.to_domain_model()
        await self.story_repo.save(story)
        return CreateStoryResponse(story=story)

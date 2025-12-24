"""List stories use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.story import Story
from julee.hcd.repositories.story import StoryRepository


class ListStoriesRequest(BaseModel):
    """Request for listing stories (extensible for filtering/pagination)."""

    pass


class ListStoriesResponse(BaseModel):
    """Response from listing stories."""

    stories: list[Story]


class ListStoriesUseCase:
    """Use case for listing all stories.

    .. usecase-documentation:: julee.hcd.domain.use_cases.story.list:ListStoriesUseCase
    """

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

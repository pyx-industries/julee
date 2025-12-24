"""Get story use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.story import Story

from ...repositories.story import StoryRepository


class GetStoryRequest(BaseModel):
    """Request for getting a story by slug."""

    slug: str


class GetStoryResponse(BaseModel):
    """Response from getting a story."""

    story: Story | None


class GetStoryUseCase:
    """Use case for getting a story by slug.

    .. usecase-documentation:: julee.hcd.domain.use_cases.story.get:GetStoryUseCase
    """

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency.

        Args:
            story_repo: Story repository instance
        """
        self.story_repo = story_repo

    async def execute(self, request: GetStoryRequest) -> GetStoryResponse:
        """Get a story by slug.

        Args:
            request: Request containing the story slug

        Returns:
            Response containing the story if found, or None
        """
        story = await self.story_repo.get(request.slug)
        return GetStoryResponse(story=story)

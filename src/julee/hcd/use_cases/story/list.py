"""List stories use case with co-located request/response."""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.hcd.entities.story import Story
from julee.hcd.repositories.story import StoryRepository


class ListStoriesRequest(BaseModel):
    """Request for listing stories with optional filters.

    All filters are optional. When multiple filters are specified,
    they are combined with AND logic.
    """

    app_slug: str | None = Field(
        default=None, description="Filter to stories for this application"
    )
    persona: str | None = Field(
        default=None, description="Filter to stories for this persona"
    )


class ListStoriesResponse(BaseModel):
    """Response from listing stories."""

    stories: list[Story]

    @property
    def count(self) -> int:
        """Number of stories returned."""
        return len(self.stories)

    def grouped_by_persona(self) -> dict[str, list[Story]]:
        """Group stories by persona name."""
        result: dict[str, list[Story]] = {}
        for story in self.stories:
            result.setdefault(story.persona, []).append(story)
        return result

    def grouped_by_app(self) -> dict[str, list[Story]]:
        """Group stories by app slug."""
        result: dict[str, list[Story]] = {}
        for story in self.stories:
            result.setdefault(story.app_slug, []).append(story)
        return result


@use_case
class ListStoriesUseCase:
    """List stories with optional filtering.

    Supports filtering by application and/or persona. When no filters
    are provided, returns all stories.

    Examples:
        # All stories
        response = use_case.execute(ListStoriesRequest())

        # Stories for a specific app
        response = use_case.execute(ListStoriesRequest(app_slug="staff-portal"))

        # Stories for a persona
        response = use_case.execute(ListStoriesRequest(persona="Pilot Manager"))

        # Combined filters (AND logic)
        response = use_case.execute(ListStoriesRequest(
            app_slug="staff-portal",
            persona="Pilot Manager"
        ))
    """

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency.

        Args:
            story_repo: Story repository instance
        """
        self.story_repo = story_repo

    async def execute(self, request: ListStoriesRequest) -> ListStoriesResponse:
        """List stories with optional filtering.

        Args:
            request: List request with optional app_slug and persona filters

        Returns:
            Response containing filtered list of stories
        """
        stories = await self.story_repo.list_all()

        # Apply filters
        if request.app_slug:
            stories = [s for s in stories if s.matches_app(request.app_slug)]

        if request.persona:
            stories = [s for s in stories if s.matches_persona(request.persona)]

        return ListStoriesResponse(stories=stories)

"""List stories use case using FilterableListUseCase."""

from pydantic import BaseModel, Field

from julee.core.use_cases.generic_crud import (
    FilterableListUseCase,
    make_list_request,
)
from julee.hcd.entities.story import Story
from julee.hcd.repositories.story import StoryRepository

# Dynamic request from repository's list_filtered signature
ListStoriesRequest = make_list_request("ListStoriesRequest", StoryRepository)


class ListStoriesResponse(BaseModel):
    """Response from listing stories.

    Uses validation_alias to accept 'entities' from generic CRUD infrastructure
    while serializing as 'stories' for API consumers.
    """

    stories: list[Story] = Field(default=[], validation_alias="entities")

    @property
    def entities(self) -> list[Story]:
        """Alias for generic list operations."""
        return self.stories

    @property
    def count(self) -> int:
        """Number of stories returned."""
        return len(self.stories)

    def grouped_by_persona(self) -> dict[str, list[Story]]:
        """Group stories by persona."""
        result: dict[str, list[Story]] = {}
        for story in self.stories:
            persona = story.persona or "unknown"
            result.setdefault(persona, []).append(story)
        return result

    def grouped_by_app(self) -> dict[str, list[Story]]:
        """Group stories by app."""
        result: dict[str, list[Story]] = {}
        for story in self.stories:
            app = story.app_slug or "unknown"
            result.setdefault(app, []).append(story)
        return result


class ListStoriesUseCase(FilterableListUseCase[Story, StoryRepository]):
    """List stories with optional filtering.

    Filters are derived from StoryRepository.list_filtered() signature:
    - app_slug: Filter to stories for this application
    - persona: Filter to stories for this persona

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

    response_cls = ListStoriesResponse

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency."""
        super().__init__(story_repo)

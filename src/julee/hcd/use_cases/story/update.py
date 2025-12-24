"""Update story use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.story import Story
from julee.hcd.repositories.story import StoryRepository


class UpdateStoryRequest(BaseModel):
    """Request for updating a story (slug identifies target)."""

    slug: str
    feature_title: str | None = None
    persona: str | None = None
    i_want: str | None = None
    so_that: str | None = None
    file_path: str | None = None
    abs_path: str | None = None
    gherkin_snippet: str | None = None

    def apply_to(self, existing: Story) -> Story:
        """Apply non-None fields to existing story."""
        updates = {
            k: v
            for k, v in {
                "feature_title": self.feature_title,
                "persona": self.persona,
                "i_want": self.i_want,
                "so_that": self.so_that,
                "file_path": self.file_path,
                "abs_path": self.abs_path,
                "gherkin_snippet": self.gherkin_snippet,
            }.items()
            if v is not None
        }
        return existing.model_copy(update=updates) if updates else existing


class UpdateStoryResponse(BaseModel):
    """Response from updating a story."""

    story: Story | None
    found: bool = True


class UpdateStoryUseCase:
    """Use case for updating a story.

    .. usecase-documentation:: julee.hcd.domain.use_cases.story.update:UpdateStoryUseCase
    """

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

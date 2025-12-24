"""Update epic use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.epic import Epic

from ...repositories.epic import EpicRepository


class UpdateEpicRequest(BaseModel):
    """Request for updating an epic."""

    slug: str
    description: str | None = None
    story_refs: list[str] | None = None

    def apply_to(self, existing: Epic) -> Epic:
        """Apply non-None fields to existing epic."""
        updates = {
            k: v
            for k, v in {
                "description": self.description,
                "story_refs": self.story_refs,
            }.items()
            if v is not None
        }
        return existing.model_copy(update=updates) if updates else existing


class UpdateEpicResponse(BaseModel):
    """Response from updating an epic."""

    epic: Epic | None
    found: bool = True


class UpdateEpicUseCase:
    """Use case for updating an epic.

    .. usecase-documentation:: julee.hcd.domain.use_cases.epic.update:UpdateEpicUseCase
    """

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

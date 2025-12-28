"""Epic orchestration use case.

Business logic for post-creation/update epic orchestration.
Detects domain conditions (empty epic, unknown story refs) and
reports them for handler delegation.
"""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.hcd.entities.epic import Epic
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name


class EpicOrchestrationRequest(BaseModel):
    """Request for epic orchestration check."""

    epic: Epic = Field(description="The epic to check for orchestration conditions")


class EpicCondition(BaseModel):
    """A detected domain condition for an epic."""

    condition: str = Field(description="Condition type identifier")
    epic_slug: str = Field(description="The epic's slug")
    details: dict = Field(
        default_factory=dict, description="Condition-specific details"
    )


class EpicOrchestrationResponse(BaseModel):
    """Response from epic orchestration check."""

    epic: Epic = Field(description="The checked epic")
    conditions: list[EpicCondition] = Field(
        default_factory=list, description="Detected conditions"
    )

    @property
    def has_empty_epic(self) -> bool:
        """Check if empty epic condition was detected."""
        return any(c.condition == "empty_epic" for c in self.conditions)

    @property
    def has_unknown_story_refs(self) -> bool:
        """Check if unknown story refs condition was detected."""
        return any(c.condition == "unknown_story_refs" for c in self.conditions)


@use_case
class EpicOrchestrationUseCase:
    """Detect orchestration conditions for an epic.

    Checks for domain conditions that may require follow-up action:
    1. Empty epic - epic has no story_refs
    2. Unknown story refs - story_refs not found in StoryRepository

    Returns detected conditions for handler delegation.
    """

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repositories for condition detection.

        Args:
            story_repo: Repository for story lookups
        """
        self._story_repo = story_repo

    async def execute(
        self, request: EpicOrchestrationRequest
    ) -> EpicOrchestrationResponse:
        """Execute orchestration condition detection.

        Args:
            request: Contains the epic to check

        Returns:
            Response with detected conditions
        """
        epic = request.epic
        conditions: list[EpicCondition] = []

        # Condition 1: Empty epic (no story refs)
        if not epic.story_refs:
            conditions.append(
                EpicCondition(
                    condition="empty_epic",
                    epic_slug=epic.slug,
                    details={"description": epic.description},
                )
            )

        # Condition 2: Unknown story refs
        if epic.story_refs:
            # Get all known story titles (normalized)
            all_stories = await self._story_repo.list_all()
            known_titles = {normalize_name(s.feature_title) for s in all_stories}

            # Find refs that don't match any known story
            unknown_refs = [
                ref
                for ref in epic.story_refs
                if normalize_name(ref) not in known_titles
            ]

            if unknown_refs:
                conditions.append(
                    EpicCondition(
                        condition="unknown_story_refs",
                        epic_slug=epic.slug,
                        details={"unknown_refs": unknown_refs},
                    )
                )

        return EpicOrchestrationResponse(epic=epic, conditions=conditions)

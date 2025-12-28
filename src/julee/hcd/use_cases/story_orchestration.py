"""Story orchestration use case.

Business logic for post-creation/update story orchestration.
Detects domain conditions (unknown persona, orphan story) and
reports them for handler delegation.
"""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.hcd.entities.story import Story
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.persona import PersonaRepository


class StoryOrchestrationRequest(BaseModel):
    """Request for story orchestration check."""

    story: Story = Field(description="The story to check for orchestration conditions")


class StoryCondition(BaseModel):
    """A detected domain condition for a story."""

    condition: str = Field(description="Condition type identifier")
    story_slug: str = Field(description="The story's slug")
    details: dict = Field(
        default_factory=dict, description="Condition-specific details"
    )


class StoryOrchestrationResponse(BaseModel):
    """Response from story orchestration check."""

    story: Story = Field(description="The checked story")
    conditions: list[StoryCondition] = Field(
        default_factory=list, description="Detected conditions"
    )

    @property
    def has_unknown_persona(self) -> bool:
        """Check if unknown persona condition was detected."""
        return any(c.condition == "unknown_persona" for c in self.conditions)

    @property
    def has_orphan_story(self) -> bool:
        """Check if orphan story condition was detected."""
        return any(c.condition == "orphan_story" for c in self.conditions)


@use_case
class StoryOrchestrationUseCase:
    """Detect orchestration conditions for a story.

    Checks for domain conditions that may require follow-up action:
    1. Unknown persona - story.persona not found in PersonaRepository
    2. Orphan story - story not referenced in any Epic.story_refs

    Returns detected conditions for handler delegation.
    """

    def __init__(
        self,
        persona_repo: PersonaRepository,
        epic_repo: EpicRepository,
    ) -> None:
        """Initialize with repositories for condition detection.

        Args:
            persona_repo: Repository for persona lookups
            epic_repo: Repository for epic lookups
        """
        self._persona_repo = persona_repo
        self._epic_repo = epic_repo

    async def execute(
        self, request: StoryOrchestrationRequest
    ) -> StoryOrchestrationResponse:
        """Execute orchestration condition detection.

        Args:
            request: Contains the story to check

        Returns:
            Response with detected conditions
        """
        story = request.story
        conditions: list[StoryCondition] = []

        # Condition 1: Unknown persona
        if story.persona != "unknown":
            persona = await self._persona_repo.get_by_normalized_name(
                story.persona_normalized
            )
            if persona is None:
                conditions.append(
                    StoryCondition(
                        condition="unknown_persona",
                        story_slug=story.slug,
                        details={"persona_name": story.persona},
                    )
                )

        # Condition 2: Orphan story (not in any epic)
        epics = await self._epic_repo.list_all()
        story_in_epic = any(story.feature_title in epic.story_refs for epic in epics)
        if not story_in_epic:
            conditions.append(
                StoryCondition(
                    condition="orphan_story",
                    story_slug=story.slug,
                    details={"feature_title": story.feature_title},
                )
            )

        return StoryOrchestrationResponse(story=story, conditions=conditions)

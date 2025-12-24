"""Create journey use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from ...models.journey import Journey, JourneyStep, StepType
from ...repositories.journey import JourneyRepository


class JourneyStepItem(BaseModel):
    """Nested item representing a journey step."""

    step_type: str = Field(description="Type of step: story, epic, or phase")
    ref: str = Field(description="Reference identifier")
    description: str = Field(default="", description="Optional description")

    def to_domain_model(self) -> JourneyStep:
        """Convert to JourneyStep."""
        return JourneyStep(
            step_type=StepType.from_string(self.step_type),
            ref=self.ref,
            description=self.description,
        )


class CreateJourneyRequest(BaseModel):
    """Request model for creating a journey.

    Fields excluded from client control:
    - persona_normalized: Computed by domain model
    - docname: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    persona: str = Field(default="", description="The persona undertaking this journey")
    intent: str = Field(
        default="", description="What the persona wants (their motivation)"
    )
    outcome: str = Field(
        default="", description="What success looks like (business value)"
    )
    goal: str = Field(default="", description="Activity description (what they do)")
    depends_on: list[str] = Field(
        default_factory=list, description="Journey slugs that must be completed first"
    )
    steps: list[JourneyStepItem] = Field(
        default_factory=list, description="Sequence of journey steps"
    )
    preconditions: list[str] = Field(
        default_factory=list, description="Conditions that must be true before starting"
    )
    postconditions: list[str] = Field(
        default_factory=list,
        description="Conditions that will be true after completion",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Journey.validate_slug(v)

    def to_domain_model(self) -> Journey:
        """Convert to Journey."""
        return Journey(
            slug=self.slug,
            persona=self.persona,
            intent=self.intent,
            outcome=self.outcome,
            goal=self.goal,
            depends_on=self.depends_on,
            steps=[s.to_domain_model() for s in self.steps],
            preconditions=self.preconditions,
            postconditions=self.postconditions,
            docname="",
        )


class CreateJourneyResponse(BaseModel):
    """Response from creating a journey."""

    journey: Journey


class CreateJourneyUseCase:
    """Use case for creating a journey.

    .. usecase-documentation:: julee.hcd.domain.use_cases.journey.create:CreateJourneyUseCase
    """

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: CreateJourneyRequest) -> CreateJourneyResponse:
        """Create a new journey.

        Args:
            request: Journey creation request with journey data

        Returns:
            Response containing the created journey
        """
        journey = request.to_domain_model()
        await self.journey_repo.save(journey)
        return CreateJourneyResponse(journey=journey)

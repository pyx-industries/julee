"""Update journey use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.hcd.entities.journey import Journey

from ...repositories.journey import JourneyRepository
from .create import JourneyStepItem


class UpdateJourneyRequest(BaseModel):
    """Request for updating a journey."""

    slug: str
    persona: str | None = None
    intent: str | None = None
    outcome: str | None = None
    goal: str | None = None
    depends_on: list[str] | None = None
    steps: list[JourneyStepItem] | None = None
    preconditions: list[str] | None = None
    postconditions: list[str] | None = None

    def apply_to(self, existing: Journey) -> Journey:
        """Apply non-None fields to existing journey."""
        updates: dict[str, Any] = {}
        if self.persona is not None:
            updates["persona"] = self.persona
        if self.intent is not None:
            updates["intent"] = self.intent
        if self.outcome is not None:
            updates["outcome"] = self.outcome
        if self.goal is not None:
            updates["goal"] = self.goal
        if self.depends_on is not None:
            updates["depends_on"] = self.depends_on
        if self.steps is not None:
            updates["steps"] = [s.to_domain_model() for s in self.steps]
        if self.preconditions is not None:
            updates["preconditions"] = self.preconditions
        if self.postconditions is not None:
            updates["postconditions"] = self.postconditions
        return existing.model_copy(update=updates) if updates else existing


class UpdateJourneyResponse(BaseModel):
    """Response from updating a journey."""

    journey: Journey | None
    found: bool = True


class UpdateJourneyUseCase:
    """Use case for updating a journey.

    .. usecase-documentation:: julee.hcd.domain.use_cases.journey.update:UpdateJourneyUseCase
    """

    def __init__(self, journey_repo: JourneyRepository) -> None:
        """Initialize with repository dependency.

        Args:
            journey_repo: Journey repository instance
        """
        self.journey_repo = journey_repo

    async def execute(self, request: UpdateJourneyRequest) -> UpdateJourneyResponse:
        """Update an existing journey.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated journey if found
        """
        existing = await self.journey_repo.get(request.slug)
        if not existing:
            return UpdateJourneyResponse(journey=None, found=False)

        updated = request.apply_to(existing)
        await self.journey_repo.save(updated)
        return UpdateJourneyResponse(journey=updated, found=True)

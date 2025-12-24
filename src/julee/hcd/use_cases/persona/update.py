"""Update persona use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.hcd.entities.persona import Persona
from julee.hcd.repositories.persona import PersonaRepository


class UpdatePersonaRequest(BaseModel):
    """Request for updating a persona."""

    slug: str
    name: str | None = None
    goals: list[str] | None = None
    frustrations: list[str] | None = None
    jobs_to_be_done: list[str] | None = None
    context: str | None = None

    def apply_to(self, existing: Persona) -> Persona:
        """Apply non-None fields to existing persona."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.goals is not None:
            updates["goals"] = self.goals
        if self.frustrations is not None:
            updates["frustrations"] = self.frustrations
        if self.jobs_to_be_done is not None:
            updates["jobs_to_be_done"] = self.jobs_to_be_done
        if self.context is not None:
            updates["context"] = self.context
        return existing.model_copy(update=updates) if updates else existing


class UpdatePersonaResponse(BaseModel):
    """Response from updating a persona."""

    persona: Persona | None
    found: bool = True


class UpdatePersonaUseCase:
    """Use case for updating a persona.

    .. usecase-documentation:: julee.hcd.domain.use_cases.persona.update:UpdatePersonaUseCase
    """

    def __init__(self, persona_repo: PersonaRepository) -> None:
        """Initialize with repository dependency.

        Args:
            persona_repo: Persona repository instance
        """
        self.persona_repo = persona_repo

    async def execute(self, request: UpdatePersonaRequest) -> UpdatePersonaResponse:
        """Update an existing persona.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing updated persona, or found=False if not found
        """
        existing = await self.persona_repo.get(request.slug)
        if existing is None:
            return UpdatePersonaResponse(persona=None, found=False)

        updated = request.apply_to(existing)
        await self.persona_repo.save(updated)
        return UpdatePersonaResponse(persona=updated, found=True)

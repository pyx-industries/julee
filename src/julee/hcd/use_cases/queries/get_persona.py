"""GetPersonaUseCase with co-located request/response.

Use case for getting a persona by name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from julee.hcd.entities.persona import Persona
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.story import StoryRepository
from julee.hcd.utils import normalize_name

from .derive_personas import DerivePersonasRequest, DerivePersonasUseCase

if TYPE_CHECKING:
    from julee.hcd.repositories.persona import PersonaRepository


class GetPersonaRequest(BaseModel):
    """Request for getting a persona by name."""

    name: str = Field(description="Persona name to search for")


class GetPersonaResponse(BaseModel):
    """Response from getting a persona by name."""

    persona: Persona | None


class GetPersonaUseCase:
    """Use case for getting a persona by name.

    .. usecase-documentation:: julee.hcd.domain.use_cases.queries.get_persona:GetPersonaUseCase

    Searches both defined and derived personas, returning merged results.
    """

    def __init__(
        self,
        story_repo: StoryRepository,
        epic_repo: EpicRepository,
        persona_repo: PersonaRepository | None = None,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            story_repo: Story repository instance
            epic_repo: Epic repository instance
            persona_repo: Optional persona repository for defined personas
        """
        self.story_repo = story_repo
        self.epic_repo = epic_repo
        self.persona_repo = persona_repo

    async def execute(self, request: GetPersonaRequest) -> GetPersonaResponse:
        """Get a persona by name (case-insensitive).

        Searches merged personas (defined + derived) and returns
        the matching persona if found.

        Args:
            request: Request containing the persona name

        Returns:
            Response containing the persona if found, or None
        """
        # Derive all personas (merged with defined) and find the matching one
        derive_use_case = DerivePersonasUseCase(
            self.story_repo, self.epic_repo, self.persona_repo
        )
        derive_response = await derive_use_case.execute(DerivePersonasRequest())

        normalized_search = normalize_name(request.name)
        for persona in derive_response.personas:
            if persona.normalized_name == normalized_search:
                return GetPersonaResponse(persona=persona)

        return GetPersonaResponse(persona=None)

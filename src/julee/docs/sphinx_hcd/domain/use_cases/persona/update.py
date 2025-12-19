"""UpdatePersonaUseCase.

Use case for updating an existing persona.
"""

from .....hcd_api.requests import UpdatePersonaRequest
from .....hcd_api.responses import UpdatePersonaResponse
from ...repositories.persona import PersonaRepository


class UpdatePersonaUseCase:
    """Use case for updating a persona."""

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

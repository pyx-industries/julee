"""CreatePersonaUseCase.

Use case for creating a new persona.
"""

from .....hcd_api.requests import CreatePersonaRequest
from .....hcd_api.responses import CreatePersonaResponse
from ...repositories.persona import PersonaRepository


class CreatePersonaUseCase:
    """Use case for creating a persona."""

    def __init__(self, persona_repo: PersonaRepository) -> None:
        """Initialize with repository dependency.

        Args:
            persona_repo: Persona repository instance
        """
        self.persona_repo = persona_repo

    async def execute(self, request: CreatePersonaRequest) -> CreatePersonaResponse:
        """Create a new persona.

        Args:
            request: Persona creation request with persona data

        Returns:
            Response containing the created persona
        """
        persona = request.to_domain_model()
        await self.persona_repo.save(persona)
        return CreatePersonaResponse(persona=persona)

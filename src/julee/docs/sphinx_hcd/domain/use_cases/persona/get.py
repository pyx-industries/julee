"""GetPersonaBySlugUseCase.

Use case for getting a defined persona by slug.
"""

from pydantic import BaseModel

from .....hcd_api.responses import GetPersonaResponse
from ...repositories.persona import PersonaRepository


class GetPersonaBySlugRequest(BaseModel):
    """Request for getting a persona by slug."""

    slug: str


class GetPersonaBySlugUseCase:
    """Use case for getting a defined persona by slug.

    This retrieves a persona from the PersonaRepository directly.
    For getting personas (defined or derived) by name, use
    GetPersonaUseCase from queries.
    """

    def __init__(self, persona_repo: PersonaRepository) -> None:
        """Initialize with repository dependency.

        Args:
            persona_repo: Persona repository instance
        """
        self.persona_repo = persona_repo

    async def execute(self, request: GetPersonaBySlugRequest) -> GetPersonaResponse:
        """Get a defined persona by slug.

        Args:
            request: Request with slug to look up

        Returns:
            Response containing the persona if found
        """
        persona = await self.persona_repo.get(request.slug)
        return GetPersonaResponse(persona=persona)

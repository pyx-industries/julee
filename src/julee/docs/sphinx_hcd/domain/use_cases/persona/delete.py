"""DeletePersonaUseCase.

Use case for deleting a persona.
"""

from .....hcd_api.requests import DeletePersonaRequest
from .....hcd_api.responses import DeletePersonaResponse
from ...repositories.persona import PersonaRepository


class DeletePersonaUseCase:
    """Use case for deleting a persona."""

    def __init__(self, persona_repo: PersonaRepository) -> None:
        """Initialize with repository dependency.

        Args:
            persona_repo: Persona repository instance
        """
        self.persona_repo = persona_repo

    async def execute(self, request: DeletePersonaRequest) -> DeletePersonaResponse:
        """Delete a persona by slug.

        Args:
            request: Delete request with slug

        Returns:
            Response indicating whether the persona was deleted
        """
        deleted = await self.persona_repo.delete(request.slug)
        return DeletePersonaResponse(deleted=deleted)

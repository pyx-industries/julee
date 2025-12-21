"""ListPersonasUseCase.

Use case for listing all defined personas.
"""

from ..requests import ListPersonasRequest
from ..responses import ListPersonasResponse
from ...repositories.persona import PersonaRepository


class ListPersonasUseCase:
    """Use case for listing personas."""

    def __init__(self, persona_repo: PersonaRepository) -> None:
        """Initialize with repository dependency.

        Args:
            persona_repo: Persona repository instance
        """
        self.persona_repo = persona_repo

    async def execute(self, request: ListPersonasRequest) -> ListPersonasResponse:
        """List all defined personas.

        Args:
            request: List request (currently empty, for future filtering)

        Returns:
            Response containing list of personas
        """
        personas = await self.persona_repo.list_all()
        return ListPersonasResponse(personas=personas)

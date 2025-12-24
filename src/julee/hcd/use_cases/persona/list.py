"""List personas use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.entities.persona import Persona
from julee.hcd.repositories.persona import PersonaRepository


class ListPersonasRequest(BaseModel):
    """Request for listing personas."""

    pass


class ListPersonasResponse(BaseModel):
    """Response from listing personas."""

    personas: list[Persona]


class ListPersonasUseCase:
    """Use case for listing personas.

    .. usecase-documentation:: julee.hcd.domain.use_cases.persona.list:ListPersonasUseCase
    """

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

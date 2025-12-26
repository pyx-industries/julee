"""List personas use case with co-located request/response."""

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.hcd.entities.persona import Persona
from julee.hcd.repositories.persona import PersonaRepository


class ListPersonasRequest(BaseModel):
    """Request for listing defined personas.

    For personas derived from stories, use DerivePersonasUseCase instead.
    """

    pass


class ListPersonasResponse(BaseModel):
    """Response from listing personas."""

    personas: list[Persona]

    @property
    def count(self) -> int:
        """Number of personas returned."""
        return len(self.personas)


@use_case
class ListPersonasUseCase:
    """List defined personas.

    Returns personas that were explicitly defined via define-persona
    directive. For derived personas (from stories), use DerivePersonasUseCase.

    Examples:
        # All defined personas
        response = use_case.execute(ListPersonasRequest())
        for persona in response.personas:
            print(persona.name)
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
            request: List request

        Returns:
            Response containing list of defined personas
        """
        personas = await self.persona_repo.list_all()
        return ListPersonasResponse(personas=personas)

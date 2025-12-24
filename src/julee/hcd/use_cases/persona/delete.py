"""Delete persona use case with co-located request/response."""

from pydantic import BaseModel

from julee.hcd.repositories.persona import PersonaRepository


class DeletePersonaRequest(BaseModel):
    """Request for deleting a persona by slug."""

    slug: str


class DeletePersonaResponse(BaseModel):
    """Response from deleting a persona."""

    deleted: bool


class DeletePersonaUseCase:
    """Use case for deleting a persona.

    .. usecase-documentation:: julee.hcd.domain.use_cases.persona.delete:DeletePersonaUseCase
    """

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

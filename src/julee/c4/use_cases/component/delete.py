"""Delete component use case with co-located request/response."""

from pydantic import BaseModel

from julee.c4.repositories.component import ComponentRepository


class DeleteComponentRequest(BaseModel):
    """Request for deleting a component by slug."""

    slug: str


class DeleteComponentResponse(BaseModel):
    """Response from deleting a component."""

    deleted: bool


class DeleteComponentUseCase:
    """Use case for deleting a component.

    .. usecase-documentation:: julee.c4.domain.use_cases.component.delete:DeleteComponentUseCase
    """

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: DeleteComponentRequest) -> DeleteComponentResponse:
        """Delete a component by slug.

        Args:
            request: Delete request containing the component slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.component_repo.delete(request.slug)
        return DeleteComponentResponse(deleted=deleted)

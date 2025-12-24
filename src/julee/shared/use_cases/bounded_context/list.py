"""ListBoundedContextsUseCase with co-located request/response.

Use case for listing all bounded contexts discovered in a codebase.
"""

from pydantic import BaseModel

from julee.shared.domain.models.bounded_context import BoundedContext
from julee.shared.domain.repositories import BoundedContextRepository


class ListBoundedContextsRequest(BaseModel):
    """Request for listing bounded contexts.

    Extensible for future filtering options.
    """

    pass


class ListBoundedContextsResponse(BaseModel):
    """Response from listing bounded contexts."""

    bounded_contexts: list[BoundedContext]


class ListBoundedContextsUseCase:
    """Use case for listing all bounded contexts.

    .. usecase-documentation:: julee.shared.domain.use_cases.bounded_context.list:ListBoundedContextsUseCase
    """

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for discovering bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: ListBoundedContextsRequest
    ) -> ListBoundedContextsResponse:
        """List all bounded contexts.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all discovered bounded contexts
        """
        bounded_contexts = await self.bounded_context_repo.list_all()
        return ListBoundedContextsResponse(bounded_contexts=bounded_contexts)

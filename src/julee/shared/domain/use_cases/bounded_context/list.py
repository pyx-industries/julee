"""ListBoundedContextsUseCase.

Use case for listing all bounded contexts discovered in a codebase.
"""

from julee.shared.domain.repositories import BoundedContextRepository
from julee.shared.domain.use_cases.requests import ListBoundedContextsRequest
from julee.shared.domain.use_cases.responses import ListBoundedContextsResponse


class ListBoundedContextsUseCase:
    """Use case for listing all bounded contexts."""

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

"""GetBoundedContextUseCase with co-located request/response.

Use case for getting a single bounded context by slug.
"""

from pydantic import BaseModel, Field

from julee.shared.domain.models.bounded_context import BoundedContext
from julee.shared.domain.repositories import BoundedContextRepository


class GetBoundedContextRequest(BaseModel):
    """Request for getting a bounded context by slug."""

    slug: str = Field(description="The bounded context slug to look up")


class GetBoundedContextResponse(BaseModel):
    """Response from getting a bounded context."""

    bounded_context: BoundedContext | None


class GetBoundedContextUseCase:
    """Use case for getting a bounded context by slug.

    .. usecase-documentation:: julee.shared.domain.use_cases.bounded_context.get:GetBoundedContextUseCase
    """

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for accessing bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: GetBoundedContextRequest
    ) -> GetBoundedContextResponse:
        """Get a bounded context by slug.

        Args:
            request: Request containing the slug to look up

        Returns:
            Response containing the bounded context if found, None otherwise
        """
        bounded_context = await self.bounded_context_repo.get(request.slug)
        return GetBoundedContextResponse(bounded_context=bounded_context)

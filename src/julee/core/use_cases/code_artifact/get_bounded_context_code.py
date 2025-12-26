"""GetBoundedContextCodeUseCase.

Composite use case that returns all code artifacts for bounded contexts
in a single call. This is more efficient than calling individual
List*UseCase methods when you need multiple artifact types.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.core.entities.code_info import BoundedContextInfo
from julee.core.parsers.ast import parse_bounded_context
from julee.core.repositories.bounded_context import BoundedContextRepository


class GetBoundedContextCodeRequest(BaseModel):
    """Request for getting bounded context code info.

    Optionally filter to a specific bounded context by slug.
    If not specified, returns code info for all bounded contexts.
    """

    bounded_context: str | None = Field(
        default=None, description="Filter to this bounded context only"
    )


class GetBoundedContextCodeResponse(BaseModel):
    """Response containing code info for bounded contexts.

    Each BoundedContextInfo contains all code artifacts:
    - entities
    - use_cases
    - requests
    - responses
    - repository_protocols
    - service_protocols
    - pipelines
    """

    contexts: list[BoundedContextInfo] = Field(
        default_factory=list,
        description="Code info for each bounded context",
    )

    @property
    def context_count(self) -> int:
        """Get number of bounded contexts."""
        return len(self.contexts)

    def get_context(self, slug: str) -> BoundedContextInfo | None:
        """Get code info for a specific bounded context by slug."""
        for ctx in self.contexts:
            if ctx.slug == slug:
                return ctx
        return None


@use_case
class GetBoundedContextCodeUseCase:
    """Get complete code information for bounded contexts.

    Returns all code artifacts (entities, use cases, protocols, etc.)
    for one or more bounded contexts in a single call.

    This is more efficient than calling individual List*UseCase methods
    when you need multiple artifact types, as it parses each bounded
    context only once.

    Args:
        bounded_context_repo: Repository for discovering bounded contexts
    """

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency."""
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: GetBoundedContextCodeRequest
    ) -> GetBoundedContextCodeResponse:
        """Get code info for bounded contexts.

        Args:
            request: Request with optional bounded_context filter

        Returns:
            Response containing BoundedContextInfo for each context
        """
        # Get bounded contexts to scan
        if request.bounded_context:
            ctx = await self.bounded_context_repo.get(request.bounded_context)
            bc_list = [ctx] if ctx else []
        else:
            bc_list = await self.bounded_context_repo.list_all()

        # Parse each bounded context
        contexts = []
        for bc in bc_list:
            info = parse_bounded_context(Path(bc.path))
            if info:
                contexts.append(info)

        return GetBoundedContextCodeResponse(contexts=contexts)

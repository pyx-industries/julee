"""ListEntitiesUseCase.

Use case for listing domain entities across bounded contexts.
"""

from pathlib import Path

from julee.core.decorators import use_case
from julee.core.parsers.ast import parse_bounded_context
from julee.core.repositories.bounded_context import BoundedContextRepository

from .uc_interfaces import (
    CodeArtifactWithContext,
    ListCodeArtifactsRequest,
    ListCodeArtifactsResponse,
)


class ListEntitiesRequest(ListCodeArtifactsRequest):
    """Request for listing entities."""


class ListEntitiesResponse(ListCodeArtifactsResponse):
    """Response from listing entities."""


@use_case
class ListEntitiesUseCase:
    """Use case for listing domain entities."""

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for discovering bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: ListCodeArtifactsRequest
    ) -> ListCodeArtifactsResponse:
        """List domain entities across bounded contexts.

        Args:
            request: Request with optional bounded_context filter

        Returns:
            Response containing list of entities with their bounded context
        """
        # Get bounded contexts to scan
        if request.bounded_context:
            ctx = await self.bounded_context_repo.get(request.bounded_context)
            contexts = [ctx] if ctx else []
        else:
            contexts = await self.bounded_context_repo.list_all()

        # Extract entities from each context
        artifacts = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info:
                for entity in info.entities:
                    artifacts.append(
                        CodeArtifactWithContext(
                            artifact=entity,
                            bounded_context=ctx.slug,
                        )
                    )

        return ListCodeArtifactsResponse(artifacts=artifacts)

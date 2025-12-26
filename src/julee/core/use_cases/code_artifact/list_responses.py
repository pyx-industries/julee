"""ListResponsesUseCase.

Use case for listing response classes across bounded contexts.
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


class ListResponsesRequest(ListCodeArtifactsRequest):
    """Request for listing response classes."""


class ListResponsesResponse(ListCodeArtifactsResponse):
    """Response from listing response classes."""


@use_case
class ListResponsesUseCase:
    """Use case for listing response classes."""

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for discovering bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: ListCodeArtifactsRequest
    ) -> ListCodeArtifactsResponse:
        """List response classes across bounded contexts.

        Args:
            request: Request with optional bounded_context filter

        Returns:
            Response containing list of response classes with their bounded context
        """
        # Get bounded contexts to scan
        if request.bounded_context:
            ctx = await self.bounded_context_repo.get(request.bounded_context)
            contexts = [ctx] if ctx else []
        else:
            contexts = await self.bounded_context_repo.list_all()

        # Extract responses from each context
        artifacts = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info:
                for resp in info.responses:
                    artifacts.append(
                        CodeArtifactWithContext(
                            artifact=resp,
                            bounded_context=ctx.slug,
                        )
                    )

        return ListCodeArtifactsResponse(artifacts=artifacts)

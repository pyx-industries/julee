"""ListHandlerProtocolsUseCase.

Use case for listing handler protocol classes across bounded contexts.
"""

from pathlib import Path

from julee.core.parsers.ast import parse_bounded_context
from julee.core.repositories.bounded_context import BoundedContextRepository

from .uc_interfaces import (
    CodeArtifactWithContext,
    ListCodeArtifactsRequest,
    ListCodeArtifactsResponse,
)


class ListHandlerProtocolsRequest(ListCodeArtifactsRequest):
    """Request for listing handler protocol classes."""


class ListHandlerProtocolsResponse(ListCodeArtifactsResponse):
    """Response from listing handler protocol classes."""


class ListHandlerProtocolsUseCase:
    """Use case for listing handler protocol classes."""

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for discovering bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: ListHandlerProtocolsRequest
    ) -> ListHandlerProtocolsResponse:
        """List handler protocol classes across bounded contexts.

        Args:
            request: Request with optional bounded_context filter

        Returns:
            Response containing list of handler protocol classes with
            their bounded context
        """
        if request.bounded_context:
            ctx = await self.bounded_context_repo.get(request.bounded_context)
            contexts = [ctx] if ctx else []
        else:
            contexts = await self.bounded_context_repo.list_all()

        artifacts = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info:
                for protocol in info.handler_protocols:
                    artifacts.append(
                        CodeArtifactWithContext(
                            artifact=protocol,
                            bounded_context=ctx.slug,
                        )
                    )

        return ListHandlerProtocolsResponse(artifacts=artifacts)

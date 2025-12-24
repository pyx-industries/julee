"""ListRepositoryProtocolsUseCase.

Use case for listing repository protocols across bounded contexts.
"""

from pathlib import Path

from julee.core.parsers.ast import parse_bounded_context
from julee.core.repositories import BoundedContextRepository

from .uc_interfaces import (
    CodeArtifactWithContext,
    ListCodeArtifactsRequest,
    ListCodeArtifactsResponse,
)


class ListRepositoryProtocolsUseCase:
    """Use case for listing repository protocols."""

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for discovering bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: ListCodeArtifactsRequest
    ) -> ListCodeArtifactsResponse:
        """List repository protocols across bounded contexts.

        Args:
            request: Request with optional bounded_context filter

        Returns:
            Response containing list of repository protocols with their bounded context
        """
        # Get bounded contexts to scan
        if request.bounded_context:
            ctx = await self.bounded_context_repo.get(request.bounded_context)
            contexts = [ctx] if ctx else []
        else:
            contexts = await self.bounded_context_repo.list_all()

        # Extract repository protocols from each context
        artifacts = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info:
                for protocol in info.repository_protocols:
                    artifacts.append(
                        CodeArtifactWithContext(
                            artifact=protocol,
                            bounded_context=ctx.slug,
                        )
                    )

        return ListCodeArtifactsResponse(artifacts=artifacts)

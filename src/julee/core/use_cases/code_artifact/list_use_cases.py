"""ListUseCasesUseCase.

Use case for listing use case classes across bounded contexts.
"""

from pathlib import Path

from julee.core.parsers.ast import parse_bounded_context
from julee.core.repositories import BoundedContextRepository

from .uc_interfaces import (
    CodeArtifactWithContext,
    ListCodeArtifactsRequest,
    ListCodeArtifactsResponse,
)


class ListUseCasesUseCase:
    """Use case for listing use case classes."""

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for discovering bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(
        self, request: ListCodeArtifactsRequest
    ) -> ListCodeArtifactsResponse:
        """List use case classes across bounded contexts.

        Args:
            request: Request with optional bounded_context filter

        Returns:
            Response containing list of use cases with their bounded context
        """
        # Get bounded contexts to scan
        if request.bounded_context:
            ctx = await self.bounded_context_repo.get(request.bounded_context)
            contexts = [ctx] if ctx else []
        else:
            contexts = await self.bounded_context_repo.list_all()

        # Extract use cases from each context
        artifacts = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info:
                for use_case in info.use_cases:
                    artifacts.append(
                        CodeArtifactWithContext(
                            artifact=use_case,
                            bounded_context=ctx.slug,
                        )
                    )

        return ListCodeArtifactsResponse(artifacts=artifacts)

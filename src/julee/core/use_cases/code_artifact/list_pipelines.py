"""ListPipelinesUseCase.

Use case for listing pipelines across bounded contexts.
"""

from pathlib import Path

from julee.core.parsers.ast import parse_pipelines_from_bounded_context
from julee.core.repositories.bounded_context import BoundedContextRepository

from .uc_interfaces import ListCodeArtifactsRequest, ListPipelinesResponse


class ListPipelinesUseCase:
    """Use case for listing pipelines.

    Pipelines are use cases treated for Temporal workflow execution.
    This use case discovers all pipelines in apps/worker/pipelines.py
    across bounded contexts.
    """

    def __init__(self, bounded_context_repo: BoundedContextRepository) -> None:
        """Initialize with repository dependency.

        Args:
            bounded_context_repo: Repository for discovering bounded contexts
        """
        self.bounded_context_repo = bounded_context_repo

    async def execute(self, request: ListCodeArtifactsRequest) -> ListPipelinesResponse:
        """List pipelines across bounded contexts.

        Args:
            request: Request with optional bounded_context filter

        Returns:
            Response containing list of pipelines with their metadata
        """
        # Get bounded contexts to scan
        if request.bounded_context:
            ctx = await self.bounded_context_repo.get(request.bounded_context)
            contexts = [ctx] if ctx else []
        else:
            contexts = await self.bounded_context_repo.list_all()

        # Extract pipelines from each context
        pipelines = []
        for ctx in contexts:
            context_pipelines = parse_pipelines_from_bounded_context(Path(ctx.path))
            pipelines.extend(context_pipelines)

        return ListPipelinesResponse(pipelines=pipelines)

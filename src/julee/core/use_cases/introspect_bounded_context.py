"""Introspect bounded context use case.

Returns code structure information for a bounded context - entities,
repositories, use cases, and service protocols.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.core.entities.code_info import BoundedContextInfo, ClassInfo
from julee.core.services.code_introspection import CodeIntrospectionService


class IntrospectBoundedContextRequest(BaseModel):
    """Request to introspect a bounded context."""

    context_path: Path = Field(description="Path to bounded context directory")


class IntrospectBoundedContextResponse(BaseModel):
    """Response containing bounded context code structure."""

    info: BoundedContextInfo | None = None
    found: bool = False

    model_config = {"arbitrary_types_allowed": True}


@use_case
class IntrospectBoundedContextUseCase:
    """Introspect a bounded context's code structure.

    Returns entities, repositories, use cases, and service protocols
    discovered in the bounded context's source directories.
    """

    def __init__(self, introspection_service: CodeIntrospectionService) -> None:
        """Initialize with introspection service.

        Args:
            introspection_service: Service for parsing code structure
        """
        self._service = introspection_service

    async def execute(
        self, request: IntrospectBoundedContextRequest
    ) -> IntrospectBoundedContextResponse:
        """Execute the use case.

        Args:
            request: Request with context path

        Returns:
            Response containing bounded context info
        """
        info = self._service.get_bounded_context(request.context_path)
        return IntrospectBoundedContextResponse(
            info=info,
            found=info is not None,
        )


class ListBoundedContextsRequest(BaseModel):
    """Request to list all bounded contexts."""

    src_dir: Path = Field(description="Root source directory to scan")


class ListBoundedContextsResponse(BaseModel):
    """Response containing discovered bounded contexts."""

    contexts: list[BoundedContextInfo] = Field(default_factory=list)
    count: int = 0

    model_config = {"arbitrary_types_allowed": True}


@use_case
class ListBoundedContextsUseCase:
    """List all bounded contexts in a source directory.

    Scans for directories with entities/ or use_cases/ subdirectories
    and returns their code structure.
    """

    def __init__(self, introspection_service: CodeIntrospectionService) -> None:
        """Initialize with introspection service.

        Args:
            introspection_service: Service for parsing code structure
        """
        self._service = introspection_service

    async def execute(
        self, request: ListBoundedContextsRequest
    ) -> ListBoundedContextsResponse:
        """Execute the use case.

        Args:
            request: Request with source directory path

        Returns:
            Response containing discovered bounded contexts
        """
        contexts = self._service.list_bounded_contexts(request.src_dir)
        return ListBoundedContextsResponse(
            contexts=contexts,
            count=len(contexts),
        )

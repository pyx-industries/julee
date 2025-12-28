"""CoreContext for code introspection.

Provides a context object that holds the introspection service and use cases,
initialized at builder-inited and accessible from directives.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from julee.core.entities.code_info import BoundedContextInfo
from julee.core.infrastructure.repositories.ast.julee_code import (
    AstJuleeCodeRepository,
)
from julee.core.repositories.julee_code import JuleeCodeRepository
from julee.core.use_cases.introspect_bounded_context import (
    IntrospectBoundedContextRequest,
    IntrospectBoundedContextUseCase,
    ListBoundedContextsRequest,
    ListBoundedContextsUseCase,
)

if TYPE_CHECKING:
    from sphinx.application import Sphinx


@dataclass
class CoreContext:
    """Context for core documentation directives.

    Holds the code repository and provides synchronous access to
    bounded context information.
    """

    repository: JuleeCodeRepository
    src_root: Path

    def get_bounded_context(self, module_path: str) -> BoundedContextInfo | None:
        """Get bounded context info by module path.

        Args:
            module_path: Dotted module path like 'julee.hcd'

        Returns:
            BoundedContextInfo if found, None otherwise
        """
        context_path = self._resolve_path(module_path)
        use_case = IntrospectBoundedContextUseCase(self.repository)
        request = IntrospectBoundedContextRequest(context_path=context_path)

        import asyncio

        async def run():
            return await use_case.execute(request)

        response = asyncio.run(run())
        return response.info

    def list_bounded_contexts(self) -> list[BoundedContextInfo]:
        """List all bounded contexts.

        Returns:
            List of BoundedContextInfo for discovered contexts
        """
        use_case = ListBoundedContextsUseCase(self.repository)
        request = ListBoundedContextsRequest(src_dir=self.src_root / "src" / "julee")

        import asyncio

        async def run():
            return await use_case.execute(request)

        response = asyncio.run(run())
        return response.contexts

    def _resolve_path(self, module_path: str) -> Path:
        """Resolve module path to filesystem path."""
        parts = module_path.split(".")
        candidate = self.src_root / "src" / Path(*parts)
        if candidate.exists():
            return candidate
        return self.src_root / Path(*parts)


def get_core_context(app: "Sphinx") -> CoreContext:
    """Get CoreContext from Sphinx app.

    Args:
        app: Sphinx application

    Returns:
        CoreContext attached to app

    Raises:
        AttributeError: If context not initialized
    """
    return app._core_context


def set_core_context(app: "Sphinx", context: CoreContext) -> None:
    """Set CoreContext on Sphinx app.

    Args:
        app: Sphinx application
        context: CoreContext to attach
    """
    app._core_context = context


def initialize_core_context(app: "Sphinx") -> None:
    """Initialize CoreContext at builder-inited.

    Args:
        app: Sphinx application
    """
    src_root = Path(app.srcdir).parent
    repository = AstJuleeCodeRepository()
    context = CoreContext(repository=repository, src_root=src_root)
    set_core_context(app, context)

"""CoreContext for code introspection.

Provides a context object that holds the introspection service and use cases,
initialized at builder-inited and accessible from directives.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from julee.core.entities.application import Application
from julee.core.entities.bounded_context import BoundedContext
from julee.core.entities.code_info import BoundedContextInfo
from julee.core.entities.deployment import Deployment
from julee.core.infrastructure.repositories.ast.julee_code import (
    AstJuleeCodeRepository,
)
from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.deployment import (
    FilesystemDeploymentRepository,
)
from julee.core.repositories.julee_code import JuleeCodeRepository
from julee.core.use_cases.application.list import (
    ListApplicationsRequest,
    ListApplicationsUseCase,
)
from julee.core.use_cases.bounded_context.list import (
    ListBoundedContextsRequest as BCListRequest,
    ListBoundedContextsUseCase as BCListUseCase,
)
from julee.core.use_cases.deployment.list import (
    ListDeploymentsRequest,
    ListDeploymentsUseCase,
)
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

    Holds repositories and provides synchronous access to solution
    structure information: bounded contexts, applications, deployments.
    """

    repository: JuleeCodeRepository
    src_root: Path
    bc_repository: FilesystemBoundedContextRepository | None = None
    app_repository: FilesystemApplicationRepository | None = None
    deployment_repository: FilesystemDeploymentRepository | None = None

    def list_solution_bounded_contexts(self) -> list[BoundedContext]:
        """List bounded contexts with descriptions using entity-based use case.

        Returns:
            List of BoundedContext entities with descriptions
        """
        if self.bc_repository is None:
            return []

        use_case = BCListUseCase(bounded_context_repo=self.bc_repository)
        request = BCListRequest()

        async def run():
            return await use_case.execute(request)

        response = asyncio.run(run())
        return response.bounded_contexts

    def list_applications(self) -> list[Application]:
        """List all applications with descriptions.

        Returns:
            List of Application entities
        """
        if self.app_repository is None:
            return []

        use_case = ListApplicationsUseCase(application_repo=self.app_repository)
        request = ListApplicationsRequest()

        async def run():
            return await use_case.execute(request)

        response = asyncio.run(run())
        return response.applications

    def list_deployments(self) -> list[Deployment]:
        """List all deployments.

        Returns:
            List of Deployment entities
        """
        if self.deployment_repository is None:
            return []

        use_case = ListDeploymentsUseCase(deployment_repo=self.deployment_repository)
        request = ListDeploymentsRequest()

        async def run():
            return await use_case.execute(request)

        response = asyncio.run(run())
        return response.deployments

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

    # Create entity-based repositories for solution structure
    bc_repository = FilesystemBoundedContextRepository(src_root)
    app_repository = FilesystemApplicationRepository(src_root)
    deployment_repository = FilesystemDeploymentRepository(src_root)

    context = CoreContext(
        repository=repository,
        src_root=src_root,
        bc_repository=bc_repository,
        app_repository=app_repository,
        deployment_repository=deployment_repository,
    )
    set_core_context(app, context)

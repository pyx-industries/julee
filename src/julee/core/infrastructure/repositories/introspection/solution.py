"""Filesystem-based solution repository.

Discovers solutions by scanning the filesystem structure, including
bounded contexts, applications, deployments, and nested solutions.
"""

from pathlib import Path

from julee.core.doctrine_constants import (
    APPS_ROOT,
    CONTRIB_DIR,
    DEPLOYMENTS_ROOT,
    SEARCH_ROOT,
)
from julee.core.entities.application import Application
from julee.core.entities.bounded_context import BoundedContext
from julee.core.entities.deployment import Deployment
from julee.core.entities.solution import Solution
from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.deployment import (
    FilesystemDeploymentRepository,
)

__all__ = ["FilesystemSolutionRepository"]


class FilesystemSolutionRepository:
    """Repository that discovers solutions by scanning filesystem.

    A solution consists of:
    - Bounded contexts at {solution}/src/julee/ (or configured search root)
    - Applications at {solution}/apps/
    - Deployments at {solution}/deployments/
    - Nested solutions (like contrib/) which may contain their own BCs and apps

    This repository coordinates FilesystemBoundedContextRepository,
    FilesystemApplicationRepository, and FilesystemDeploymentRepository to
    build a complete Solution graph.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize repository.

        Args:
            project_root: Root directory of the solution
        """
        self.project_root = project_root
        self._cache: Solution | None = None

    def _discover_bc_embedded_apps(
        self, bc: BoundedContext
    ) -> list[Application]:
        """Discover applications embedded within a bounded context.

        Some BCs (especially in contrib/) contain reference applications
        at {bc}/apps/. These are discovered separately from the main apps/.
        """
        bc_apps_path = Path(bc.path) / APPS_ROOT
        if not bc_apps_path.exists():
            return []

        # Use application repository to scan the BC's apps directory
        # We create a temporary repo pointing at the BC path
        app_repo = FilesystemApplicationRepository(Path(bc.path))
        # Manually discover since we're not at a standard solution root
        apps = app_repo._discover_all()
        return apps

    def _discover_nested_solution(
        self, path: Path, name: str, parent_path: str
    ) -> Solution:
        """Discover a nested solution (like contrib/).

        Nested solutions contain BCs but typically don't have their own
        apps/ directory at the nested solution level. Instead, individual
        BCs within the nested solution may have their own apps/.
        """
        # Discover BCs within the nested solution
        # We need to look directly in the nested solution path, not src/julee/
        bc_repo = FilesystemBoundedContextRepository(self.project_root)

        # Get BCs that are marked as contrib (they're in the nested solution)
        # This is a bit of a workaround - we filter by is_contrib
        nested_bcs = []
        all_bcs = bc_repo._discover_all()
        for bc in all_bcs:
            if bc.is_contrib and str(path) in bc.path:
                nested_bcs.append(bc)

        # Discover apps embedded in each BC
        nested_apps: list[Application] = []
        for bc in nested_bcs:
            bc_apps = self._discover_bc_embedded_apps(bc)
            nested_apps.extend(bc_apps)

        return Solution(
            name=name,
            path=str(path),
            bounded_contexts=nested_bcs,
            applications=nested_apps,
            nested_solutions=[],  # Could recurse further if needed
            is_nested=True,
            parent_path=parent_path,
        )

    def _discover_solution(self) -> Solution:
        """Discover the complete solution structure."""
        # Discover top-level bounded contexts (non-contrib)
        bc_repo = FilesystemBoundedContextRepository(self.project_root)
        all_bcs = bc_repo._discover_all()
        top_level_bcs = [bc for bc in all_bcs if not bc.is_contrib]

        # Discover top-level applications
        app_repo = FilesystemApplicationRepository(self.project_root)
        top_level_apps = app_repo._discover_all()

        # Discover top-level deployments
        dep_repo = FilesystemDeploymentRepository(self.project_root)
        top_level_deps = dep_repo._discover_all()

        # Discover nested solutions (contrib/)
        nested_solutions: list[Solution] = []
        contrib_path = self.project_root / SEARCH_ROOT / CONTRIB_DIR
        if contrib_path.exists() and contrib_path.is_dir():
            nested_solution = self._discover_nested_solution(
                contrib_path,
                name=CONTRIB_DIR,
                parent_path=str(self.project_root),
            )
            if nested_solution.bounded_contexts or nested_solution.applications:
                nested_solutions.append(nested_solution)

        # Derive solution name from project root
        solution_name = self.project_root.name
        if solution_name == "." or not solution_name:
            solution_name = Path.cwd().name

        return Solution(
            name=solution_name,
            path=str(self.project_root),
            bounded_contexts=top_level_bcs,
            applications=top_level_apps,
            deployments=top_level_deps,
            nested_solutions=nested_solutions,
            is_nested=False,
            parent_path=None,
        )

    async def get(self) -> Solution:
        """Get the current solution.

        Returns the solution rooted at the project_root provided during
        initialization. Results are cached.
        """
        if self._cache is None:
            self._cache = self._discover_solution()
        return self._cache

    def invalidate_cache(self) -> None:
        """Clear the discovery cache."""
        self._cache = None

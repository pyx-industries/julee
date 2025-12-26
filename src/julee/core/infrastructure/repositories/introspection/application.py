"""Filesystem-based application repository.

Discovers applications by scanning the filesystem structure.
This is a read-only repository - applications are defined by
the filesystem, not created through this repository.
"""

from pathlib import Path

from julee.core.doctrine_constants import (
    APP_BC_ORGANIZATION_EXCLUDES,
    APPS_ROOT,
)

# Structural directories that indicate app internals, not BC organization
_STRUCTURAL_SUBDIRS = frozenset(
    {
        "routers",
        "tools",
        "directives",
        "commands",
        "templates",
        "pipelines",
        "activities",
        "handlers",
        "event_handlers",
        "middleware",
        "schemas",
        "services",
        "repositories",
        "models",
        "utils",
        "lib",
    }
)
from julee.core.entities.application import (
    Application,
    AppStructuralMarkers,
    AppType,
)

__all__ = ["FilesystemApplicationRepository"]


class FilesystemApplicationRepository:
    """Repository that discovers applications by scanning filesystem.

    Inspects directory structure to find applications under {solution}/apps/.
    Applications are classified by type based on structural markers.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize repository.

        Args:
            project_root: Root directory of the project (solution)
        """
        self.project_root = project_root
        self._cache: list[Application] | None = None

    def _is_python_package(self, path: Path) -> bool:
        """Check if directory is a Python package."""
        return (path / "__init__.py").exists()

    def _has_subdir(self, path: Path, name: str) -> bool:
        """Check if path contains a subdirectory with the given name."""
        return (path / name).is_dir()

    def _has_subdir_recursive(self, path: Path, name: str) -> bool:
        """Check if path or any subdirectory contains a directory with given name.

        Used for apps that use BC-based organization where markers may be
        in subdirectories (e.g., apps/api/ceap/routers/).

        Also checks inside 'shared/' which is a common location for shared
        infrastructure within an app.
        """
        if self._has_subdir(path, name):
            return True

        for child in path.iterdir():
            if child.is_dir() and not child.name.startswith(("_", ".")):
                # Check inside shared/ (common for shared infrastructure)
                if child.name == "shared":
                    if self._has_subdir(child, name):
                        return True
                # Check inside BC-organized subdirs
                elif child.name not in APP_BC_ORGANIZATION_EXCLUDES:
                    if self._has_subdir(child, name):
                        return True
        return False

    def _is_temporal_worker(self, path: Path) -> bool:
        """Detect if app is a Temporal worker by checking imports.

        Temporal workers may not have local pipelines (they can import from BCs),
        so we check for temporalio imports in main.py.
        """
        main_py = path / "main.py"
        if main_py.exists():
            try:
                content = main_py.read_text()
                if "temporalio" in content and "Worker" in content:
                    return True
            except OSError:
                pass
        return False

    def _detect_bc_organization(self, path: Path) -> bool:
        """Detect if app uses bounded-context-based organization.

        Returns True if the app has subdirectories that look like BC names
        (Python packages excluding reserved names and structural directories).
        """
        bc_like_subdirs = 0
        for child in path.iterdir():
            if not child.is_dir():
                continue
            if child.name.startswith(("_", ".")):
                continue
            if child.name in APP_BC_ORGANIZATION_EXCLUDES:
                continue
            # Structural directories are not BC organization
            if child.name in _STRUCTURAL_SUBDIRS:
                continue
            if self._is_python_package(child):
                bc_like_subdirs += 1

        # If there are 2+ BC-like subdirs, assume BC organization
        return bc_like_subdirs >= 2

    def _detect_markers(self, path: Path) -> AppStructuralMarkers:
        """Detect structural markers in an application directory."""
        uses_bc_org = self._detect_bc_organization(path)

        # For BC-organized apps, look in subdirs; otherwise look at root
        check_fn = self._has_subdir_recursive if uses_bc_org else self._has_subdir

        return AppStructuralMarkers(
            has_tests=check_fn(path, "tests"),
            has_dependencies=(path / "dependencies.py").exists()
            or any(
                (path / subdir / "dependencies.py").exists()
                for subdir in path.iterdir()
                if subdir.is_dir() and subdir.name not in APP_BC_ORGANIZATION_EXCLUDES
            ),
            has_routers=check_fn(path, "routers"),
            has_tools=check_fn(path, "tools"),
            has_directives=check_fn(path, "directives"),
            has_pipelines=check_fn(path, "pipelines")
            or (path / "pipelines.py").exists()
            or any(
                (path / subdir / "pipelines.py").exists()
                for subdir in path.iterdir()
                if subdir.is_dir()
            ),
            has_activities=check_fn(path, "activities")
            or (path / "activities.py").exists(),
            has_commands=check_fn(path, "commands"),
            uses_bc_organization=uses_bc_org,
        )

    def _infer_app_type(self, path: Path, markers: AppStructuralMarkers) -> AppType:
        """Infer application type from structural markers and content analysis."""
        if markers.has_routers:
            return AppType.REST_API
        if markers.has_tools:
            return AppType.MCP
        if markers.has_directives:
            return AppType.SPHINX_EXTENSION
        if markers.has_pipelines or markers.has_activities:
            return AppType.TEMPORAL_WORKER
        # Check for Temporal worker via import analysis (composite workers)
        if self._is_temporal_worker(path):
            return AppType.TEMPORAL_WORKER
        if markers.has_commands:
            return AppType.CLI
        # Default to CLI if no markers detected
        return AppType.CLI

    def _discover_all(self) -> list[Application]:
        """Discover all applications."""
        apps_path = self.project_root / APPS_ROOT

        if not apps_path.exists():
            return []

        applications = []

        for candidate in apps_path.iterdir():
            if not candidate.is_dir():
                continue

            # Skip dot-prefixed directories
            if candidate.name.startswith("."):
                continue

            # Skip __pycache__
            if candidate.name == "__pycache__":
                continue

            # Must be a Python package
            if not self._is_python_package(candidate):
                continue

            markers = self._detect_markers(candidate)
            app_type = self._infer_app_type(candidate, markers)

            app = Application(
                slug=candidate.name,
                path=str(candidate),
                app_type=app_type,
                markers=markers,
            )
            applications.append(app)

        return sorted(applications, key=lambda a: a.slug)

    async def list_all(self) -> list[Application]:
        """List all discovered applications."""
        if self._cache is None:
            self._cache = self._discover_all()
        return self._cache

    async def get(self, slug: str) -> Application | None:
        """Get an application by slug."""
        applications = await self.list_all()
        for app in applications:
            if app.slug == slug:
                return app
        return None

    async def list_by_type(self, app_type: AppType) -> list[Application]:
        """List applications of a specific type."""
        applications = await self.list_all()
        return [app for app in applications if app.app_type == app_type]

    def invalidate_cache(self) -> None:
        """Clear the discovery cache."""
        self._cache = None

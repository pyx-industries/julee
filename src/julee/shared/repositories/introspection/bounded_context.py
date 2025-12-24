"""Filesystem-based bounded context repository.

Discovers bounded contexts by scanning the filesystem structure.
This is a read-only repository - bounded contexts are defined by
the filesystem, not created through this repository.
"""

import subprocess
from pathlib import Path

from julee.shared.domain.models import BoundedContext, StructuralMarkers


# =============================================================================
# Directory Structure Configuration
# =============================================================================
# Bounded contexts follow the {bc}/domain/{layer}/ pattern.

MODELS_DIR = ("domain", "models")
REPOSITORIES_DIR = ("domain", "repositories")
SERVICES_DIR = ("domain", "services")
USE_CASES_DIR = ("domain", "use_cases")


# =============================================================================
# Reserved Words
# =============================================================================
# Directory names with special structural meaning that cannot be bounded
# context names.

RESERVED_STRUCTURAL = frozenset({
    "core",       # The idioms accelerator
    "contrib",    # Batteries-included modules
    "applications",
    "docs",
    "deployment",
})

RESERVED_COMMON = frozenset({
    "shared",     # The foundational accelerator (current name for core)
    "util",
    "utils",
    "common",
    "tests",
})

RESERVED_WORDS = RESERVED_STRUCTURAL | RESERVED_COMMON


# =============================================================================
# Viewpoint Bounded Contexts
# =============================================================================

VIEWPOINT_SLUGS = frozenset({
    "hcd",
    "c4",
})


# =============================================================================
# Search Configuration
# =============================================================================

SEARCH_ROOT = "src/julee"


# =============================================================================
# Gitignore Handling
# =============================================================================

def _is_gitignored(path: Path, project_root: Path) -> bool:
    """Check if a path is ignored by git.

    Uses `git check-ignore` to respect .gitignore rules.
    Falls back to False if git is not available or path is not in a repo.
    """
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=project_root,
            capture_output=True,
            timeout=5,
        )
        # Exit code 0 means the path IS ignored
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # git not available or other error - don't ignore
        return False


# =============================================================================
# Repository Implementation
# =============================================================================

class FilesystemBoundedContextRepository:
    """Repository that discovers bounded contexts by scanning filesystem.

    Inspects directory structure to find bounded contexts that follow
    the domain/{models,repositories,services,use_cases} pattern.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize repository.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self._cache: list[BoundedContext] | None = None

    def _is_python_package(self, path: Path) -> bool:
        """Check if directory is a Python package."""
        return (path / "__init__.py").exists()

    def _has_subdir(self, path: Path, parts: tuple[str, ...]) -> bool:
        """Check if path contains a subdirectory."""
        return path.joinpath(*parts).is_dir()

    def _detect_markers(self, path: Path) -> StructuralMarkers:
        """Detect structural markers in a directory."""
        return StructuralMarkers(
            has_domain_models=self._has_subdir(path, MODELS_DIR),
            has_domain_repositories=self._has_subdir(path, REPOSITORIES_DIR),
            has_domain_services=self._has_subdir(path, SERVICES_DIR),
            has_domain_use_cases=self._has_subdir(path, USE_CASES_DIR),
            has_tests=self._has_subdir(path, ("tests",)),
            has_parsers=self._has_subdir(path, ("parsers",)),
            has_serializers=self._has_subdir(path, ("serializers",)),
        )

    def _is_bounded_context(self, markers: StructuralMarkers) -> bool:
        """Check if markers indicate a bounded context.

        A bounded context must have models or use_cases.
        """
        return markers.has_domain_models or markers.has_domain_use_cases

    def _discover_in_directory(
        self,
        search_path: Path,
        is_contrib: bool = False,
    ) -> list[BoundedContext]:
        """Discover bounded contexts in a directory."""
        contexts = []

        if not search_path.exists():
            return contexts

        for candidate in search_path.iterdir():
            if not candidate.is_dir():
                continue

            # Skip dot-prefixed directories
            if candidate.name.startswith("."):
                continue

            # Skip gitignored directories
            if _is_gitignored(candidate, self.project_root):
                continue

            # Skip reserved words
            if candidate.name in RESERVED_WORDS:
                continue

            # Must be a Python package
            if not self._is_python_package(candidate):
                continue

            markers = self._detect_markers(candidate)

            # Must have bounded context structure
            if not self._is_bounded_context(markers):
                continue

            context = BoundedContext(
                slug=candidate.name,
                path=str(candidate),
                is_contrib=is_contrib,
                is_viewpoint=candidate.name in VIEWPOINT_SLUGS,
                markers=markers,
            )
            contexts.append(context)

        return sorted(contexts, key=lambda c: c.slug)

    def _discover_all(self) -> list[BoundedContext]:
        """Discover all bounded contexts."""
        search_path = self.project_root / SEARCH_ROOT

        top_level = self._discover_in_directory(search_path)

        contrib_path = search_path / "contrib"
        contrib = self._discover_in_directory(contrib_path, is_contrib=True)

        return top_level + contrib

    async def list_all(self) -> list[BoundedContext]:
        """List all discovered bounded contexts."""
        if self._cache is None:
            self._cache = self._discover_all()
        return self._cache

    async def get(self, slug: str) -> BoundedContext | None:
        """Get a bounded context by slug."""
        contexts = await self.list_all()
        for context in contexts:
            if context.slug == slug:
                return context
        return None

    def invalidate_cache(self) -> None:
        """Clear the discovery cache."""
        self._cache = None

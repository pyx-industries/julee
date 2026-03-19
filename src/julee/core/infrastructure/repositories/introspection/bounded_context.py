"""Filesystem-based bounded context repository.

Discovers bounded contexts by scanning the filesystem structure.
This is a read-only repository - bounded contexts are defined by
the filesystem, not created through this repository.
"""

import ast
import subprocess
from pathlib import Path

from julee.core.doctrine_constants import (
    CONTRIB_DIR,
    ENTITIES_PATH,
    REPOSITORIES_PATH,
    RESERVED_WORDS,
    SERVICES_PATH,
    USE_CASES_PATH,
    VIEWPOINT_SLUGS,
)
from julee.core.entities.bounded_context import BoundedContext, StructuralMarkers

__all__ = ["FilesystemBoundedContextRepository"]


# =============================================================================
# Docstring Extraction
# =============================================================================


def _get_first_docstring_line(path: Path) -> str | None:
    """Extract first line of docstring from a Python package's __init__.py.

    Args:
        path: Directory containing __init__.py

    Returns:
        First non-empty line of docstring or None if not found
    """
    init_file = path / "__init__.py"
    if not init_file.exists():
        return None

    try:
        source = init_file.read_text()
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)
        if docstring:
            for line in docstring.split("\n"):
                line = line.strip()
                if line:
                    return line
    except (SyntaxError, OSError):
        pass

    return None


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
    the {entities,repositories,services,use_cases} pattern (flattened)
    or the legacy domain/{models,repositories,services,use_cases} pattern.
    """

    def __init__(
        self,
        project_root: Path,
        search_root: str,
    ) -> None:
        """Initialize repository.

        Args:
            project_root: Root directory of the project
            search_root: Root directory for bounded context discovery,
                relative to project_root (e.g., "src/myapp").
        """
        self.project_root = project_root
        self.search_root = search_root
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
            has_domain_models=self._has_subdir(path, ENTITIES_PATH),
            has_domain_repositories=self._has_subdir(path, REPOSITORIES_PATH),
            has_domain_services=self._has_subdir(path, SERVICES_PATH),
            has_domain_use_cases=self._has_subdir(path, USE_CASES_PATH),
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
                description=_get_first_docstring_line(candidate),
                is_contrib=is_contrib,
                is_viewpoint=candidate.name in VIEWPOINT_SLUGS,
                markers=markers,
            )
            contexts.append(context)

        return sorted(contexts, key=lambda c: c.slug)

    def _is_nested_solution(self, path: Path) -> bool:
        """Check if a directory is a nested solution container.

        A nested solution is a Python package that:
        - Does NOT have BC structure itself (no entities/ or use_cases/)
        - Contains at least one subdirectory that IS a bounded context

        Examples: contrib/, experimental/, plugins/
        """
        if not self._is_python_package(path):
            return False

        # If it has BC structure, it's a BC not a nested solution
        markers = self._detect_markers(path)
        if self._is_bounded_context(markers):
            return False

        # Check if any child is a bounded context
        for child in path.iterdir():
            if not child.is_dir() or child.name.startswith("."):
                continue
            if not self._is_python_package(child):
                continue
            child_markers = self._detect_markers(child)
            if self._is_bounded_context(child_markers):
                return True

        return False

    def _discover_all(self) -> list[BoundedContext]:
        """Discover all bounded contexts.

        Scans top-level directories and recursively discovers BCs in
        nested solutions. A nested solution is a Python package that
        contains BCs but isn't a BC itself (e.g., contrib/, experimental/).
        """
        search_path = self.project_root / self.search_root
        all_contexts: list[BoundedContext] = []

        if not search_path.exists():
            return all_contexts

        for candidate in search_path.iterdir():
            if not candidate.is_dir():
                continue
            if candidate.name.startswith("."):
                continue
            if _is_gitignored(candidate, self.project_root):
                continue
            if candidate.name in RESERVED_WORDS:
                continue
            if not self._is_python_package(candidate):
                continue

            markers = self._detect_markers(candidate)

            if self._is_bounded_context(markers):
                # It's a bounded context
                is_contrib = candidate.name == CONTRIB_DIR
                context = BoundedContext(
                    slug=candidate.name,
                    path=str(candidate),
                    description=_get_first_docstring_line(candidate),
                    is_contrib=is_contrib,
                    is_viewpoint=candidate.name in VIEWPOINT_SLUGS,
                    markers=markers,
                )
                all_contexts.append(context)
            elif self._is_nested_solution(candidate):
                # It's a nested solution - discover BCs within it
                is_contrib = candidate.name == CONTRIB_DIR
                nested_contexts = self._discover_in_directory(
                    candidate, is_contrib=is_contrib
                )
                all_contexts.extend(nested_contexts)

        return sorted(all_contexts, key=lambda c: c.slug)

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

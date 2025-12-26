"""Filesystem-based documentation repository.

Discovers documentation configuration by scanning the filesystem structure.
This is a read-only repository - documentation is defined by the filesystem,
not created through this repository.
"""

import re
from pathlib import Path

from julee.core.doctrine_constants import DOCS_ROOT
from julee.core.entities.documentation import (
    Documentation,
    DocumentationStructuralMarkers,
)

__all__ = ["FilesystemDocumentationRepository"]


class FilesystemDocumentationRepository:
    """Repository that discovers documentation by scanning filesystem.

    Inspects directory structure to find documentation at {solution}/docs/.
    Validates Sphinx configuration and build infrastructure.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize repository.

        Args:
            project_root: Root directory of the project (solution)
        """
        self.project_root = project_root
        self._cache: Documentation | None = None

    def _has_file(self, path: Path, name: str) -> bool:
        """Check if path contains a file with the given name."""
        return (path / name).is_file()

    def _has_subdir(self, path: Path, name: str) -> bool:
        """Check if path contains a subdirectory with the given name."""
        return (path / name).is_dir()

    def _check_makefile_has_html_target(self, makefile_path: Path) -> bool:
        """Check if Makefile supports 'make html'.

        Sphinx Makefiles typically use one of two patterns:
        1. Explicit 'html:' target
        2. Catch-all '%: Makefile' pattern that routes to sphinx-build -M
        """
        if not makefile_path.exists():
            return False

        try:
            content = makefile_path.read_text()
            # Look for explicit 'html:' target
            if re.search(r"^html\s*:", content, re.MULTILINE):
                return True
            # Look for Sphinx catch-all pattern '%: Makefile' with sphinx-build -M
            if (
                re.search(r"^%:\s*Makefile", content, re.MULTILINE)
                and "sphinx-build" in content
            ):
                return True
            return False
        except OSError:
            return False

    def _extract_sphinx_project(self, conf_py_path: Path) -> str | None:
        """Extract project name from Sphinx conf.py."""
        if not conf_py_path.exists():
            return None

        try:
            content = conf_py_path.read_text()
            # Look for: project = "name" or project = 'name'
            match = re.search(
                r"^project\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE
            )
            return match.group(1) if match else None
        except OSError:
            return None

    def _detect_markers(self, path: Path) -> DocumentationStructuralMarkers:
        """Detect structural markers in a documentation directory."""
        makefile_path = path / "Makefile"

        return DocumentationStructuralMarkers(
            # Sphinx markers
            has_conf_py=self._has_file(path, "conf.py"),
            has_makefile=makefile_path.is_file(),
            has_index_rst=self._has_file(path, "index.rst"),
            # Build infrastructure
            has_make_html_target=self._check_makefile_has_html_target(makefile_path),
            # Optional markers
            has_api_docs=(
                self._has_subdir(path, "api")
                or self._has_subdir(path, "autoapi")
                or self._has_subdir(path, "_api")
            ),
            has_static=self._has_subdir(path, "_static"),
            has_templates=self._has_subdir(path, "_templates"),
        )

    def _discover(self) -> Documentation | None:
        """Discover documentation configuration."""
        docs_path = self.project_root / DOCS_ROOT

        if not docs_path.exists() or not docs_path.is_dir():
            return None

        markers = self._detect_markers(docs_path)
        conf_py_path = docs_path / "conf.py"

        return Documentation(
            path=str(docs_path),
            markers=markers,
            sphinx_project=self._extract_sphinx_project(conf_py_path),
        )

    async def get(self) -> Documentation | None:
        """Get the documentation configuration.

        Returns the documentation at {solution}/docs/ or None if not found.
        Results are cached.
        """
        if self._cache is None:
            self._cache = self._discover()
        return self._cache

    async def exists(self) -> bool:
        """Check if documentation directory exists."""
        docs_path = self.project_root / DOCS_ROOT
        return docs_path.exists() and docs_path.is_dir()

    def invalidate_cache(self) -> None:
        """Clear the discovery cache."""
        self._cache = None

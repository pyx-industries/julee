"""Documentation doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

The principle: Code exists -> autodoc generates documentation.
Hand-written RST is only for design artifacts (directives) and editorial content.
"""

import re
from pathlib import Path

import pytest

from julee.core.doctrine_constants import DOCS_ROOT

# =============================================================================
# DOCTRINE: Code-Outward Documentation
# =============================================================================


class TestCodeOutwardDocumentation:
    """Doctrine about code-outward documentation.

    Documentation should flow FROM code TO rendered output, not be maintained
    as parallel content. Docstrings are the source of truth; autodoc renders them.
    """

    # Manual Python documentation directives that indicate redundant RST
    MANUAL_PY_DIRECTIVES = [
        r"\.\.\s+py:module::",
        r"\.\.\s+py:class::",
        r"\.\.\s+py:function::",
        r"\.\.\s+py:method::",
        r"\.\.\s+py:attribute::",
        r"\.\.\s+py:data::",
        r"\.\.\s+py:exception::",
        r"\.\.\s+py:decorator::",
    ]

    # Autodoc directives that are acceptable
    AUTODOC_DIRECTIVES = [
        r"\.\.\s+automodule::",
        r"\.\.\s+autoclass::",
        r"\.\.\s+autofunction::",
        r"\.\.\s+autosummary::",
        r"\.\.\s+automethod::",
        r"\.\.\s+autoattribute::",
        r"\.\.\s+autodata::",
        r"\.\.\s+autoexception::",
    ]

    # Directories to exclude from checking
    EXCLUDE_DIRS = {
        "_generated",  # Autodoc output
        "_templates",  # Jinja templates
        "_build",  # Build output
        "_static",  # Static files
    }

    def _find_rst_files(self, docs_path: Path) -> list[Path]:
        """Find all RST files in docs/, excluding generated/template dirs."""
        rst_files = []
        for rst_file in docs_path.rglob("*.rst"):
            # Skip excluded directories
            if any(excl in rst_file.parts for excl in self.EXCLUDE_DIRS):
                continue
            rst_files.append(rst_file)
        return rst_files

    def _has_manual_py_directives(self, content: str) -> list[str]:
        """Check if content contains manual Python documentation directives."""
        found = []
        for pattern in self.MANUAL_PY_DIRECTIVES:
            if re.search(pattern, content):
                # Extract the directive type
                directive = pattern.replace(r"\.\.\s+", ".. ").replace("::", "")
                found.append(directive)
        return found

    def _module_exists(self, module_name: str) -> bool:
        """Check if a Python module exists."""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def _extract_module_refs(self, content: str) -> list[str]:
        """Extract module references from manual py:module directives."""
        modules = []
        pattern = r"\.\.\s+py:module::\s+([\w.]+)"
        for match in re.finditer(pattern, content):
            modules.append(match.group(1))
        return modules

    def test_RST_MUST_NOT_use_manual_py_directives_for_existing_modules(
        self, project_root: Path
    ):
        """RST files MUST NOT use manual py:* directives for modules that exist.

        If a Python module exists, documentation MUST use autodoc directives
        (automodule, autoclass, etc.) to render from docstrings, not manual
        py:module, py:class, etc. directives.

        Manual py:* directives are only acceptable for documenting planned
        but not-yet-implemented modules.
        """
        docs_path = project_root / DOCS_ROOT

        if not docs_path.exists():
            pytest.skip("No docs directory")

        violations = []

        for rst_file in self._find_rst_files(docs_path):
            content = rst_file.read_text()

            # Check for manual py:module directives
            module_refs = self._extract_module_refs(content)
            for module_name in module_refs:
                if self._module_exists(module_name):
                    violations.append(
                        f"{rst_file.relative_to(project_root)}: "
                        f"Manual py:module::{module_name} - module exists, "
                        f"use automodule instead"
                    )

            # Check for other manual py:* directives (general warning)
            manual_directives = self._has_manual_py_directives(content)
            if manual_directives and not module_refs:
                # Has manual directives but not py:module - still flag
                for directive in manual_directives:
                    violations.append(
                        f"{rst_file.relative_to(project_root)}: "
                        f"Contains {directive} - consider using autodoc directives"
                    )

        assert (
            not violations
        ), "RST files MUST use autodoc for existing modules:\n" + "\n".join(violations)


# =============================================================================
# DOCTRINE: Single Source of Truth
# =============================================================================


class TestSingleSourceOfTruth:
    """Doctrine about documentation single source of truth.

    Docstrings ARE the documentation. RST files should either:
    1. Drive autodoc (autosummary, automodule) - renders from docstrings
    2. Use directives that generate content (define-*, index directives)
    3. Provide editorial content (guides, tutorials, concepts)

    RST files MUST NOT duplicate content that exists in docstrings.
    """

    def test_api_generated_dir_MUST_exist(self, project_root: Path):
        """The API _generated directory MUST exist after docs build.

        This ensures autodoc is configured and generating documentation
        from code rather than requiring manual RST maintenance.
        """
        generated_path = project_root / DOCS_ROOT / "api" / "_generated"

        # Note: This test passes if the directory exists (after a build)
        # It's informational - the directory is created by sphinx-build
        if not generated_path.exists():
            pytest.skip(
                "Run 'make -C docs html' to generate API docs. "
                "The _generated directory is created during build."
            )

        # Verify it has content
        rst_files = list(generated_path.glob("*.rst"))
        assert len(rst_files) > 0, (
            "API _generated directory exists but is empty. "
            "Check autosummary configuration in docs/conf.py"
        )


# =============================================================================
# DOCTRINE: Design Documents
# =============================================================================


class TestDesignDocuments:
    """Doctrine about design documents.

    Design documents (proposals, ADRs) are acceptable hand-written RST
    because they document intent and decisions, not code structure.

    Once code is implemented, the design doc's technical content becomes
    redundant - the code and its docstrings are the truth.
    """

    # Directories that are explicitly for design/editorial content
    DESIGN_DIRS = {
        "proposals",
        "ADRs",
        "architecture",  # Contains guides and design artifacts
        "users",  # HCD content using directives
        "domain",  # Domain documentation using directives
    }

    def test_design_directories_are_allowed(self, project_root: Path):
        """Design directories are allowed to contain hand-written RST.

        These directories serve specific purposes:
        - proposals/: Design proposals for new features
        - ADRs/: Architecture Decision Records
        - architecture/: Guides and design artifacts (using directives)
        - users/: HCD documentation (personas, journeys, epics)
        - domain/: Domain entities documentation (using directives)
        """
        docs_path = project_root / DOCS_ROOT

        if not docs_path.exists():
            pytest.skip("No docs directory")

        # Verify design directories exist and serve their purpose
        found_design_dirs = []
        for design_dir in self.DESIGN_DIRS:
            dir_path = docs_path / design_dir
            if dir_path.exists() and dir_path.is_dir():
                found_design_dirs.append(design_dir)

        # This test documents what's allowed, not what's required
        # At least some design directories should exist in a mature project
        assert len(found_design_dirs) > 0 or not docs_path.exists(), (
            "Expected at least one design directory for documentation. "
            f"Allowed: {self.DESIGN_DIRS}"
        )

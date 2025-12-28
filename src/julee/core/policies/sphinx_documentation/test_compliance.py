"""Compliance tests for Sphinx Documentation policy.

These tests verify that a solution has proper Sphinx documentation.
"""

import pytest

from julee.core.infrastructure.repositories.introspection.solution import (
    FilesystemSolutionRepository,
)


class TestSphinxDocumentationCompliance:
    """Compliance tests for sphinx-documentation policy."""

    @pytest.mark.asyncio
    async def test_solution_MUST_have_documentation(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A solution MUST have a docs/ directory."""
        solution = await solution_repo.get()

        assert (
            solution.documentation is not None
        ), "Solution MUST have documentation (docs/ directory)"

    @pytest.mark.asyncio
    async def test_documentation_MUST_have_sphinx_conf_py(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """The docs/ directory MUST have a valid Sphinx conf.py."""
        solution = await solution_repo.get()

        assert solution.documentation is not None, "Solution MUST have documentation"
        assert (
            solution.documentation.markers.has_conf_py
        ), "docs/ MUST have conf.py (Sphinx configuration)"

    @pytest.mark.asyncio
    async def test_documentation_MUST_have_makefile(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """The docs/ directory MUST have a Makefile."""
        solution = await solution_repo.get()

        assert solution.documentation is not None, "Solution MUST have documentation"
        assert solution.documentation.markers.has_makefile, "docs/ MUST have Makefile"

    @pytest.mark.asyncio
    async def test_documentation_MUST_support_make_html(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """The docs/Makefile MUST have an 'html' target."""
        solution = await solution_repo.get()

        assert solution.documentation is not None, "Solution MUST have documentation"
        assert (
            solution.documentation.markers.has_make_html_target
        ), "docs/Makefile MUST have 'html' target (build with 'make html')"

    @pytest.mark.asyncio
    async def test_documentation_MUST_be_buildable(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """Documentation MUST be buildable with 'make html'.

        This is the combined check: Makefile exists AND has html target.
        """
        solution = await solution_repo.get()

        assert solution.documentation is not None, "Solution MUST have documentation"
        assert (
            solution.documentation.is_buildable
        ), "Documentation MUST be buildable (Makefile with 'html' target)"

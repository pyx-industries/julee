"""Solution doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

A Solution is the top-level container for a julee-based project:
- Solution MUST have Documentation (docs/)
- Solution MAY contain one or more Bounded Contexts
- Solution MAY contain one or more Applications
- Solution MAY contain one or more Deployments
- Solution MAY contain one or more nested Solutions

The canonical structure is:
    {solution}/
    ├── docs/                # Documentation (REQUIRED)
    │   ├── conf.py          # Sphinx configuration
    │   ├── Makefile         # Build with 'make html'
    │   └── index.rst        # Entry point
    ├── src/{solution}/      # Bounded contexts live here
    │   ├── {bc}/            # Bounded context directories
    │   └── {nested}/        # Optional nested solution(s)
    │       └── {bc}/        # Bounded contexts in nested solution
    ├── apps/                # Applications live here
    │   └── {app}/           # Application directories
    └── deployments/         # Deployments live here
        └── {env}/           # Environment directories
"""

import pytest

from julee.core.infrastructure.repositories.introspection.solution import (
    FilesystemSolutionRepository,
)

# =============================================================================
# DOCTRINE: Solution Discovery
# =============================================================================


class TestSolutionDiscovery:
    """Doctrine about solution discovery."""

    @pytest.mark.asyncio
    async def test_solution_MUST_be_discoverable(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A solution MUST be discoverable from its project root."""
        solution = await solution_repo.get()

        assert solution is not None, "Solution MUST be discoverable"
        assert solution.name, "Solution MUST have a name"
        assert solution.path, "Solution MUST have a path"

    @pytest.mark.asyncio
    async def test_solution_MUST_NOT_be_marked_as_nested(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A root solution MUST NOT be marked as nested."""
        solution = await solution_repo.get()

        assert solution.is_nested is False, "Root solution MUST NOT be nested"
        assert solution.parent_path is None, "Root solution MUST NOT have parent_path"


# =============================================================================
# DOCTRINE: Solution Contains Bounded Contexts
# =============================================================================


class TestSolutionBoundedContexts:
    """Doctrine about bounded contexts within solutions."""

    @pytest.mark.asyncio
    async def test_solution_MAY_contain_bounded_contexts(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A solution MAY contain one or more bounded contexts.

        Bounded contexts are discovered at {solution}/src/julee/ (or configured
        search root). This tests the capability, not a specific count.
        """
        solution = await solution_repo.get()

        # The solution's bounded_contexts property returns BCs in this solution
        # (not nested solutions)
        assert isinstance(solution.bounded_contexts, list)

        # Our test solution (julee2) has BCs - verify the property works
        if solution.bounded_contexts:
            for bc in solution.bounded_contexts:
                assert bc.slug, "Each BC MUST have a slug"
                assert bc.path, "Each BC MUST have a path"

    @pytest.mark.asyncio
    async def test_solution_all_bounded_contexts_MUST_include_nested(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """Solution.all_bounded_contexts MUST include BCs from nested solutions.

        This aggregate property flattens the hierarchy for convenient access.
        """
        solution = await solution_repo.get()

        # all_bounded_contexts should include nested
        all_bcs = solution.all_bounded_contexts

        # Count BCs in nested solutions
        nested_bc_count = sum(
            len(nested.bounded_contexts) for nested in solution.nested_solutions
        )

        # all_bounded_contexts should equal direct + nested
        expected_count = len(solution.bounded_contexts) + nested_bc_count
        assert len(all_bcs) == expected_count, (
            f"all_bounded_contexts ({len(all_bcs)}) MUST equal "
            f"direct ({len(solution.bounded_contexts)}) + "
            f"nested ({nested_bc_count})"
        )


# =============================================================================
# DOCTRINE: Solution Contains Applications
# =============================================================================


class TestSolutionApplications:
    """Doctrine about applications within solutions."""

    @pytest.mark.asyncio
    async def test_solution_MAY_contain_applications(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A solution MAY contain one or more applications.

        Applications are discovered at {solution}/apps/. This tests the
        capability, not a specific count.
        """
        solution = await solution_repo.get()

        # The solution's applications property returns apps in this solution
        assert isinstance(solution.applications, list)

        # Our test solution (julee2) has apps - verify the property works
        if solution.applications:
            for app in solution.applications:
                assert app.slug, "Each app MUST have a slug"
                assert app.path, "Each app MUST have a path"
                assert app.app_type, "Each app MUST have an app_type"

    @pytest.mark.asyncio
    async def test_solution_all_applications_MUST_include_nested(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """Solution.all_applications MUST include apps from nested solutions.

        This aggregate property flattens the hierarchy for convenient access.
        """
        solution = await solution_repo.get()

        # all_applications should include nested
        all_apps = solution.all_applications

        # Count apps in nested solutions
        nested_app_count = sum(
            len(nested.applications) for nested in solution.nested_solutions
        )

        # all_applications should equal direct + nested
        expected_count = len(solution.applications) + nested_app_count
        assert len(all_apps) == expected_count, (
            f"all_applications ({len(all_apps)}) MUST equal "
            f"direct ({len(solution.applications)}) + "
            f"nested ({nested_app_count})"
        )


# =============================================================================
# DOCTRINE: Solution Contains Nested Solutions
# =============================================================================


class TestNestedSolutions:
    """Doctrine about nested solutions."""

    @pytest.mark.asyncio
    async def test_solution_MAY_contain_nested_solutions(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A solution MAY contain one or more nested solutions.

        Nested solutions (like contrib/) are containers for additional bounded
        contexts and their reference applications.
        """
        solution = await solution_repo.get()

        # The solution's nested_solutions property returns nested solutions
        assert isinstance(solution.nested_solutions, list)

        # If there are nested solutions, verify their structure
        for nested in solution.nested_solutions:
            assert nested.name, "Nested solution MUST have a name"
            assert nested.path, "Nested solution MUST have a path"
            assert nested.is_nested is True, "Nested solution MUST be marked as nested"
            assert nested.parent_path, "Nested solution MUST have parent_path"

    @pytest.mark.asyncio
    async def test_nested_solution_MUST_be_marked_as_nested(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A nested solution MUST have is_nested=True."""
        solution = await solution_repo.get()

        for nested in solution.nested_solutions:
            assert (
                nested.is_nested is True
            ), f"Nested solution '{nested.name}' MUST have is_nested=True"

    @pytest.mark.asyncio
    async def test_nested_solution_MUST_reference_parent(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A nested solution MUST reference its parent solution path."""
        solution = await solution_repo.get()

        for nested in solution.nested_solutions:
            assert nested.parent_path == solution.path, (
                f"Nested solution '{nested.name}' parent_path MUST match "
                f"root solution path"
            )


# =============================================================================
# DOCTRINE: Solution Lookup Methods
# =============================================================================


class TestSolutionLookup:
    """Doctrine about solution entity lookup methods."""

    @pytest.mark.asyncio
    async def test_get_bounded_context_MUST_search_nested(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """Solution.get_bounded_context MUST search nested solutions.

        The lookup method should find BCs regardless of whether they are in
        the root solution or a nested solution.
        """
        solution = await solution_repo.get()

        # If we have nested solutions with BCs, verify we can find them
        for nested in solution.nested_solutions:
            for bc in nested.bounded_contexts:
                found = solution.get_bounded_context(bc.slug)
                assert (
                    found is not None
                ), f"get_bounded_context('{bc.slug}') MUST find BC in nested solution"
                assert found.slug == bc.slug

    @pytest.mark.asyncio
    async def test_get_application_MUST_search_nested(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """Solution.get_application MUST search nested solutions.

        The lookup method should find apps regardless of whether they are in
        the root solution or a nested solution.
        """
        solution = await solution_repo.get()

        # If we have nested solutions with apps, verify we can find them
        for nested in solution.nested_solutions:
            for app in nested.applications:
                found = solution.get_application(app.slug)
                assert (
                    found is not None
                ), f"get_application('{app.slug}') MUST find app in nested solution"
                assert found.slug == app.slug


# =============================================================================
# DOCTRINE: Solution Documentation Requirements
# =============================================================================


class TestSolutionDocumentation:
    """Doctrine about solution documentation.

    Every julee solution MUST have documentation. Documentation is required,
    not optional, because a solution without documentation is not a complete
    deliverable.
    """

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

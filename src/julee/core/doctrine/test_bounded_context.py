"""Bounded context doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.conftest import create_bounded_context, create_solution
from julee.core.doctrine_constants import (
    CONTRIB_DIR,
    ENTITIES_PATH,
    RESERVED_WORDS,
    SEARCH_ROOT,
    VIEWPOINT_SLUGS,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.use_cases.bounded_context.list import (
    ListBoundedContextsRequest,
    ListBoundedContextsUseCase,
)

# =============================================================================
# DOCTRINE: Bounded Context Structure
# =============================================================================


class TestBoundedContextStructure:
    """Doctrine about bounded context structure."""

    @pytest.mark.asyncio
    async def test_bounded_context_MUST_have_entities_or_use_cases(
        self, tmp_path: Path
    ):
        """A bounded context MUST have entities/ or use_cases/."""
        root = create_solution(tmp_path)
        create_bounded_context(root, "valid", layers=[ENTITIES_PATH])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            assert (
                ctx.markers.has_clean_architecture_layers
            ), f"'{ctx.slug}' MUST have entities/ or use_cases/"

    @pytest.mark.asyncio
    async def test_bounded_context_MUST_be_python_package(self, tmp_path: Path):
        """A bounded context MUST be a Python package."""
        root = create_solution(tmp_path)
        create_bounded_context(root, "valid")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            init_file = ctx.absolute_path / "__init__.py"
            assert init_file.exists(), f"'{ctx.slug}' MUST have __init__.py"


# =============================================================================
# DOCTRINE: Reserved Words
# =============================================================================


class TestReservedWords:
    """Doctrine about reserved words."""

    @pytest.mark.asyncio
    async def test_bounded_context_MUST_NOT_use_reserved_word(self, tmp_path: Path):
        """A bounded context MUST NOT use a reserved word as its name."""
        root = create_solution(tmp_path)
        create_bounded_context(root, "billing")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            assert (
                ctx.slug not in RESERVED_WORDS
            ), f"'{ctx.slug}' MUST NOT use reserved word"

    def test_RESERVED_WORDS_MUST_be_derived_from_doctrine_constants(self):
        """RESERVED_WORDS MUST be derived from doctrine constants.

        Reserved words are directories with special architectural meaning:
        - apps: application layer (APPS_ROOT)
        - deployments: deployment configurations (DEPLOYMENTS_ROOT)
        - deployment: legacy singular form (LAYER_DEPLOYMENT)

        Utility directories (util, docs, tests) are NOT reserved because
        they fail the structural check (no entities/ or use_cases/).
        """
        from julee.core.doctrine_constants import (
            APPS_ROOT,
            DEPLOYMENTS_ROOT,
            LAYER_DEPLOYMENT,
        )

        # Must include doctrine-derived values
        assert APPS_ROOT in RESERVED_WORDS
        assert DEPLOYMENTS_ROOT in RESERVED_WORDS
        assert LAYER_DEPLOYMENT in RESERVED_WORDS

    def test_RESERVED_WORDS_MUST_NOT_include_redundant_directories(self):
        """RESERVED_WORDS MUST NOT include directories that fail structural check.

        The 'tests' directory naturally fails bounded context detection
        (no entities/ or use_cases/) so reserving it would be redundant.
        """
        redundant = {"tests"}
        assert not redundant.intersection(RESERVED_WORDS), (
            f"RESERVED_WORDS contains redundant entries: "
            f"{redundant.intersection(RESERVED_WORDS)}"
        )

    def test_core_MUST_NOT_be_reserved(self):
        """'core' MUST NOT be reserved - it's a foundational bounded context."""
        assert "core" not in RESERVED_WORDS

    def test_contrib_MUST_NOT_be_reserved(self):
        """'contrib' MUST NOT be reserved - it's a nested solution container."""
        assert "contrib" not in RESERVED_WORDS


# =============================================================================
# DOCTRINE: Import Paths
# =============================================================================


class TestImportPaths:
    """Doctrine about import paths."""

    @pytest.mark.asyncio
    async def test_import_path_MUST_NOT_contain_path_separators(self, tmp_path: Path):
        """A bounded context import path MUST NOT contain / or \\ characters."""
        root = create_solution(tmp_path)
        create_bounded_context(root, "valid")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            assert (
                "/" not in ctx.import_path
            ), f"'{ctx.slug}' import path MUST NOT contain /"
            assert (
                "\\" not in ctx.import_path
            ), f"'{ctx.slug}' import path MUST NOT contain \\"


# =============================================================================
# DOCTRINE: Viewpoints
# =============================================================================


class TestViewpoints:
    """Doctrine about viewpoints."""

    def test_VIEWPOINT_SLUGS_MUST_be_hcd_and_c4(self):
        """VIEWPOINT_SLUGS MUST be exactly {'hcd', 'c4'}."""
        assert VIEWPOINT_SLUGS == {"hcd", "c4"}

    @pytest.mark.asyncio
    async def test_viewpoint_MUST_be_marked_is_viewpoint_true(self, tmp_path: Path):
        """A viewpoint bounded context MUST have is_viewpoint=True."""
        root = create_solution(tmp_path)
        create_bounded_context(root, "hcd")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            if ctx.slug in VIEWPOINT_SLUGS:
                assert (
                    ctx.is_viewpoint is True
                ), f"'{ctx.slug}' MUST have is_viewpoint=True"


# =============================================================================
# DOCTRINE: Contrib
# =============================================================================


class TestContrib:
    """Doctrine about contrib modules."""

    @pytest.mark.asyncio
    async def test_contrib_module_MUST_have_is_contrib_true(self, tmp_path: Path):
        """A bounded context under contrib/ MUST have is_contrib=True."""
        root = create_solution(tmp_path)
        contrib = root / "contrib"
        contrib.mkdir()
        (contrib / "__init__.py").touch()
        create_bounded_context(contrib, "mymodule")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            if "contrib" in str(ctx.path):
                assert ctx.is_contrib is True, f"'{ctx.slug}' MUST have is_contrib=True"

    @pytest.mark.asyncio
    async def test_top_level_module_MUST_have_is_contrib_false(self, tmp_path: Path):
        """A bounded context NOT under contrib/ MUST have is_contrib=False."""
        root = create_solution(tmp_path)
        create_bounded_context(root, "toplevel")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            if "contrib" not in str(ctx.path):
                assert (
                    ctx.is_contrib is False
                ), f"'{ctx.slug}' MUST have is_contrib=False"


# =============================================================================
# DOCTRINE: Solution Exhaustiveness
# =============================================================================


class TestSolutionExhaustiveness:
    """Doctrine about solution exhaustiveness.

    All Python packages in a solution root MUST be:
    - Valid bounded contexts (with entities/ or use_cases/), OR
    - Nested solutions (containing bounded contexts), OR
    - Reserved words (structural/utility directories)

    This prevents "orphan" packages that slip through doctrine checks by not
    being discovered as bounded contexts.
    """

    def _is_nested_solution(self, path: Path) -> bool:
        """Check if a directory is a nested solution (contains bounded contexts)."""
        if not path.is_dir() or not (path / "__init__.py").exists():
            return False

        # A nested solution contains at least one bounded context
        for child in path.iterdir():
            if not child.is_dir() or not (child / "__init__.py").exists():
                continue
            # Check if child has BC structure
            if (child / "entities").is_dir() or (child / "use_cases").is_dir():
                return True
        return False

    @pytest.mark.asyncio
    async def test_all_packages_in_solution_MUST_be_BC_or_reserved_or_nested_solution(
        self, project_root: Path
    ):
        """All Python packages in solution root MUST be BC, reserved, or nested solution.

        This is the exhaustiveness check. It catches packages that exist but don't
        follow doctrine - like a bounded context that has domain/ instead of entities/.
        """
        search_path = project_root / SEARCH_ROOT

        # TODO: Relocate util to core - see https://github.com/pyx-industries/julee/issues/XXX
        # Once relocated, remove this exclusion
        pending_relocation = {"util"}

        # Get discovered bounded contexts
        repo = FilesystemBoundedContextRepository(project_root)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())
        discovered_slugs = {ctx.slug for ctx in response.bounded_contexts}

        # Check all Python packages in solution root
        violations = []
        for candidate in search_path.iterdir():
            if not candidate.is_dir():
                continue
            if candidate.name.startswith(".") or candidate.name == "__pycache__":
                continue
            if not (candidate / "__init__.py").exists():
                continue

            # This is a Python package. It MUST be one of:
            # 1. A discovered bounded context
            # 2. A reserved word
            # 3. A nested solution
            # 4. Pending relocation (temporary)

            if candidate.name in discovered_slugs:
                continue  # Valid: discovered BC

            if candidate.name in RESERVED_WORDS:
                continue  # Valid: reserved word

            if self._is_nested_solution(candidate):
                continue  # Valid: nested solution

            if candidate.name in pending_relocation:
                continue  # Temporary: pending relocation

            violations.append(
                f"'{candidate.name}' at {candidate}: Python package is not a valid "
                "bounded context (missing entities/ or use_cases/), not reserved, "
                "and not a nested solution"
            )

        assert not violations, (
            "All Python packages in solution root MUST be bounded contexts, "
            "reserved words, or nested solutions:\n" + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_all_packages_in_nested_solution_MUST_be_BC_or_reserved(
        self, project_root: Path
    ):
        """All Python packages in nested solution MUST be BC or reserved.

        Nested solutions (like contrib/) contain bounded contexts, not other
        nested solutions (no deep nesting allowed).
        """
        contrib_path = project_root / SEARCH_ROOT / CONTRIB_DIR

        if not contrib_path.exists():
            pytest.skip("No contrib directory")

        # Get discovered bounded contexts in contrib
        repo = FilesystemBoundedContextRepository(project_root)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())
        contrib_slugs = {
            ctx.slug for ctx in response.bounded_contexts if ctx.is_contrib
        }

        # Check all Python packages in contrib
        violations = []
        for candidate in contrib_path.iterdir():
            if not candidate.is_dir():
                continue
            if candidate.name.startswith(".") or candidate.name == "__pycache__":
                continue
            if not (candidate / "__init__.py").exists():
                continue

            # This is a Python package. It MUST be one of:
            # 1. A discovered bounded context
            # 2. A reserved word
            # (No nested solutions in nested solutions)

            if candidate.name in contrib_slugs:
                continue  # Valid: discovered BC

            if candidate.name in RESERVED_WORDS:
                continue  # Valid: reserved word

            violations.append(
                f"'{candidate.name}' at {candidate}: Python package in nested solution "
                "is not a valid bounded context (missing entities/ or use_cases/) "
                "and not reserved"
            )

        assert not violations, (
            "All Python packages in nested solution MUST be bounded contexts or "
            "reserved words:\n" + "\n".join(violations)
        )

"""Bounded context doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.shared.doctrine.conftest import create_bounded_context, create_solution
from julee.shared.domain.doctrine_constants import RESERVED_WORDS, VIEWPOINT_SLUGS
from julee.shared.domain.use_cases import (
    ListBoundedContextsRequest,
    ListBoundedContextsUseCase,
)
from julee.shared.repositories.introspection import FilesystemBoundedContextRepository

# =============================================================================
# DOCTRINE: Bounded Context Structure
# =============================================================================


class TestBoundedContextStructure:
    """Doctrine about bounded context structure."""

    @pytest.mark.asyncio
    async def test_bounded_context_MUST_have_domain_models_or_use_cases(
        self, tmp_path: Path
    ):
        """A bounded context MUST have domain/models or domain/use_cases."""
        root = create_solution(tmp_path)
        create_bounded_context(root, "valid", layers=["models"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListBoundedContextsUseCase(repo)
        response = await use_case.execute(ListBoundedContextsRequest())

        for ctx in response.bounded_contexts:
            assert (
                ctx.markers.has_clean_architecture_layers
            ), f"'{ctx.slug}' MUST have domain/models or domain/use_cases"

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

    def test_RESERVED_WORDS_MUST_include_structural_directories(self):
        """RESERVED_WORDS MUST include: core, contrib, applications, docs, deployment."""
        required = {"core", "contrib", "applications", "docs", "deployment"}
        assert required.issubset(RESERVED_WORDS)

    def test_RESERVED_WORDS_MUST_include_common_directories(self):
        """RESERVED_WORDS MUST include: shared, util, utils, common, tests."""
        required = {"shared", "util", "utils", "common", "tests"}
        assert required.issubset(RESERVED_WORDS)


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

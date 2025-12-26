"""Tests for FilesystemBoundedContextRepository."""

from pathlib import Path
from unittest.mock import patch

import pytest

from julee.core.doctrine_constants import RESERVED_WORDS, VIEWPOINT_SLUGS
from julee.core.infrastructure.repositories.introspection import (
    FilesystemBoundedContextRepository,
)


def create_bounded_context(base_path: Path, name: str, layers: list[str] | None = None):
    """Helper to create a bounded context directory structure."""
    ctx_path = base_path / name
    ctx_path.mkdir(parents=True)
    (ctx_path / "__init__.py").touch()

    if layers is None:
        layers = ["entities", "use_cases"]

    for layer in layers:
        layer_path = ctx_path / layer
        layer_path.mkdir(parents=True)
        (layer_path / "__init__.py").touch()

    return ctx_path


def create_search_root(tmp_path: Path) -> Path:
    """Create the standard search root structure."""
    search_root = tmp_path / "src" / "julee"
    search_root.mkdir(parents=True)
    return search_root


class TestDiscoveryBasics:
    """Basic discovery tests."""

    @pytest.mark.asyncio
    async def test_discovers_bounded_context_with_entities(self, tmp_path: Path):
        """Should discover context with entities/."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing", layers=["entities"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "billing"
        assert contexts[0].markers.has_domain_models is True

    @pytest.mark.asyncio
    async def test_discovers_bounded_context_with_use_cases(self, tmp_path: Path):
        """Should discover context with use_cases/."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing", layers=["use_cases"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "billing"
        assert contexts[0].markers.has_domain_use_cases is True

    @pytest.mark.asyncio
    async def test_discovers_multiple_bounded_contexts(self, tmp_path: Path):
        """Should discover multiple bounded contexts."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")
        create_bounded_context(search_root, "inventory")
        create_bounded_context(search_root, "shipping")

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 3
        slugs = {c.slug for c in contexts}
        assert slugs == {"billing", "inventory", "shipping"}

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_contexts(self, tmp_path: Path):
        """Should return empty list when no bounded contexts found."""
        create_search_root(tmp_path)

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert contexts == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_search_root_missing(self, tmp_path: Path):
        """Should return empty list when search root doesn't exist."""
        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert contexts == []


class TestExclusions:
    """Tests for exclusion logic."""

    @pytest.mark.asyncio
    async def test_excludes_reserved_words(self, tmp_path: Path):
        """Should exclude directories with reserved names.

        Reserved words are derived from doctrine constants - these have
        special architectural meaning and their own discovery mechanisms.
        """
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        # Create reserved word directories with BC structure
        # These should be excluded even if they have entities/use_cases
        for reserved in RESERVED_WORDS:
            create_bounded_context(search_root, reserved)

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "billing"

    @pytest.mark.asyncio
    async def test_excludes_dot_prefixed_directories(self, tmp_path: Path):
        """Should exclude directories starting with a dot."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")
        create_bounded_context(search_root, ".hidden")

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "billing"

    @pytest.mark.asyncio
    async def test_excludes_non_packages(self, tmp_path: Path):
        """Should exclude directories without __init__.py."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        # Create directory with BC structure but no __init__.py
        not_package = search_root / "not_a_package"
        not_package.mkdir()
        (not_package / "domain" / "models").mkdir(parents=True)

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "billing"

    @pytest.mark.asyncio
    async def test_excludes_directories_without_bc_structure(self, tmp_path: Path):
        """Should exclude packages without domain/models or domain/use_cases."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        # Create package without BC structure
        no_structure = search_root / "utilities"
        no_structure.mkdir()
        (no_structure / "__init__.py").touch()
        (no_structure / "helpers.py").touch()

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "billing"

    @pytest.mark.asyncio
    async def test_excludes_gitignored_directories(self, tmp_path: Path):
        """Should exclude directories ignored by git."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")
        create_bounded_context(search_root, "ignored_bc")

        def mock_gitignore(path, project_root):
            return "ignored_bc" in str(path)

        with patch(
            "julee.core.infrastructure.repositories.introspection.bounded_context._is_gitignored",
            mock_gitignore,
        ):
            repo = FilesystemBoundedContextRepository(tmp_path)
            contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "billing"


class TestMarkerDetection:
    """Tests for structural marker detection."""

    @pytest.mark.asyncio
    async def test_detects_all_domain_layers(self, tmp_path: Path):
        """Should detect all domain layer markers."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(
            search_root,
            "complete",
            layers=["entities", "repositories", "services", "use_cases"],
        )

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        markers = contexts[0].markers
        assert markers.has_domain_models is True
        assert markers.has_domain_repositories is True
        assert markers.has_domain_services is True
        assert markers.has_domain_use_cases is True

    @pytest.mark.asyncio
    async def test_detects_additional_markers(self, tmp_path: Path):
        """Should detect tests, parsers, serializers."""
        search_root = create_search_root(tmp_path)
        ctx_path = create_bounded_context(search_root, "billing")

        # Add additional directories
        for extra in ["tests", "parsers", "serializers"]:
            extra_path = ctx_path / extra
            extra_path.mkdir()
            (extra_path / "__init__.py").touch()

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        markers = contexts[0].markers
        assert markers.has_tests is True
        assert markers.has_parsers is True
        assert markers.has_serializers is True


class TestViewpointDetection:
    """Tests for viewpoint detection."""

    @pytest.mark.asyncio
    async def test_detects_hcd_as_viewpoint(self, tmp_path: Path):
        """Should mark 'hcd' as a viewpoint."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "hcd")

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "hcd"
        assert contexts[0].is_viewpoint is True

    @pytest.mark.asyncio
    async def test_detects_c4_as_viewpoint(self, tmp_path: Path):
        """Should mark 'c4' as a viewpoint."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "c4")

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 1
        assert contexts[0].slug == "c4"
        assert contexts[0].is_viewpoint is True

    @pytest.mark.asyncio
    async def test_non_viewpoint_slugs(self, tmp_path: Path):
        """Should not mark regular contexts as viewpoints."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert contexts[0].is_viewpoint is False


class TestContribDiscovery:
    """Tests for contrib bounded context discovery."""

    @pytest.mark.asyncio
    async def test_discovers_contrib_modules(self, tmp_path: Path):
        """Should discover bounded contexts under contrib/."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        # Create contrib structure
        contrib_path = search_root / "contrib"
        contrib_path.mkdir()
        (contrib_path / "__init__.py").touch()
        create_bounded_context(contrib_path, "polling")

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        assert len(contexts) == 2
        slugs = {c.slug for c in contexts}
        assert slugs == {"billing", "polling"}

    @pytest.mark.asyncio
    async def test_marks_contrib_modules(self, tmp_path: Path):
        """Should mark contrib modules with is_contrib=True."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        contrib_path = search_root / "contrib"
        contrib_path.mkdir()
        (contrib_path / "__init__.py").touch()
        create_bounded_context(contrib_path, "polling")

        repo = FilesystemBoundedContextRepository(tmp_path)
        contexts = await repo.list_all()

        billing = next(c for c in contexts if c.slug == "billing")
        polling = next(c for c in contexts if c.slug == "polling")

        assert billing.is_contrib is False
        assert polling.is_contrib is True


class TestGetMethod:
    """Tests for get() method."""

    @pytest.mark.asyncio
    async def test_get_returns_matching_context(self, tmp_path: Path):
        """Should return context matching slug."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")
        create_bounded_context(search_root, "inventory")

        repo = FilesystemBoundedContextRepository(tmp_path)
        context = await repo.get("billing")

        assert context is not None
        assert context.slug == "billing"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_unknown_slug(self, tmp_path: Path):
        """Should return None for unknown slug."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        repo = FilesystemBoundedContextRepository(tmp_path)
        context = await repo.get("unknown")

        assert context is None


class TestCaching:
    """Tests for caching behavior."""

    @pytest.mark.asyncio
    async def test_caches_results(self, tmp_path: Path):
        """Should cache discovery results."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        repo = FilesystemBoundedContextRepository(tmp_path)

        # First call populates cache
        contexts1 = await repo.list_all()
        assert len(contexts1) == 1

        # Add another context
        create_bounded_context(search_root, "inventory")

        # Second call returns cached results
        contexts2 = await repo.list_all()
        assert len(contexts2) == 1  # Still 1, cached

    @pytest.mark.asyncio
    async def test_invalidate_cache_triggers_rediscovery(self, tmp_path: Path):
        """Should rediscover after cache invalidation."""
        search_root = create_search_root(tmp_path)
        create_bounded_context(search_root, "billing")

        repo = FilesystemBoundedContextRepository(tmp_path)

        contexts1 = await repo.list_all()
        assert len(contexts1) == 1

        # Add another context
        create_bounded_context(search_root, "inventory")

        # Invalidate cache
        repo.invalidate_cache()

        # Now should find both
        contexts2 = await repo.list_all()
        assert len(contexts2) == 2


class TestReservedWordsConfiguration:
    """Tests verifying reserved words configuration."""

    def test_reserved_words_derived_from_doctrine_constants(self):
        """Reserved words should be derived from doctrine constants.

        Reserved words have special architectural meaning defined by
        doctrine constants like APPS_ROOT and DEPLOYMENTS_ROOT.
        """
        from julee.core.doctrine_constants import (
            APPS_ROOT,
            DEPLOYMENTS_ROOT,
            LAYER_DEPLOYMENT,
        )

        assert APPS_ROOT in RESERVED_WORDS
        assert DEPLOYMENTS_ROOT in RESERVED_WORDS
        assert LAYER_DEPLOYMENT in RESERVED_WORDS

    def test_reserved_words_not_redundant(self):
        """Reserved words should NOT include directories that fail structural check.

        The 'tests' directory naturally fails the bounded context structural
        check (no entities/ or use_cases/) so reserving it would be redundant.
        """
        redundant = {"tests"}
        intersection = redundant.intersection(RESERVED_WORDS)
        assert not intersection, f"Redundant reserved words: {intersection}"

    def test_core_is_not_reserved(self):
        """'core' should NOT be reserved - it's a bounded context."""
        assert "core" not in RESERVED_WORDS

    def test_contrib_is_not_reserved(self):
        """'contrib' should NOT be reserved - it's a nested solution."""
        assert "contrib" not in RESERVED_WORDS

    def test_viewpoint_slugs_are_correct(self):
        """Viewpoint slugs should be hcd and c4."""
        assert VIEWPOINT_SLUGS == {"hcd", "c4"}

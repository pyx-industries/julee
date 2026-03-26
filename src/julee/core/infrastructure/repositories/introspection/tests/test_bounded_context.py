"""Unit tests for the filesystem bounded context repository.

Exercises discovery logic that doctrine tests depend on to find bounded
contexts. Uses tmp_path to create realistic directory structures.
"""

import pytest

from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
    _get_first_docstring_line,
)

pytestmark = pytest.mark.unit


# =============================================================================
# Helpers
# =============================================================================


def _make_bc(root, name, layers=("entities",), docstring=None):
    """Create a minimal bounded context directory."""
    bc = root / name
    bc.mkdir(parents=True, exist_ok=True)
    init = f'"""{docstring}"""\n' if docstring else ""
    (bc / "__init__.py").write_text(init)
    for layer in layers:
        layer_dir = bc / layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        (layer_dir / "__init__.py").write_text("")
    return bc


def _make_repo(tmp_path, search_root="src/app"):
    """Create a repository with a standard project layout."""
    (tmp_path / search_root).mkdir(parents=True, exist_ok=True)
    (tmp_path / ".git").mkdir()  # fake git dir so git check-ignore works
    return FilesystemBoundedContextRepository(
        project_root=tmp_path,
        search_root=search_root,
    )


# =============================================================================
# _get_first_docstring_line
# =============================================================================


class TestGetFirstDocstringLine:
    """Tests for package docstring extraction."""

    def test_extracts_first_line(self, tmp_path):
        pkg = tmp_path / "my_pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text('"""First line.\n\nMore.\n"""')
        assert _get_first_docstring_line(pkg) == "First line."

    def test_returns_none_without_init(self, tmp_path):
        pkg = tmp_path / "no_init"
        pkg.mkdir()
        assert _get_first_docstring_line(pkg) is None

    def test_returns_none_without_docstring(self, tmp_path):
        pkg = tmp_path / "no_doc"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("x = 1\n")
        assert _get_first_docstring_line(pkg) is None

    def test_skips_blank_lines_in_docstring(self, tmp_path):
        pkg = tmp_path / "blanks"
        pkg.mkdir()
        (pkg / "__init__.py").write_text('"""\n\nActual first line.\n"""')
        assert _get_first_docstring_line(pkg) == "Actual first line."


# =============================================================================
# Discovery
# =============================================================================


class TestBoundedContextDiscovery:
    """Tests for BC discovery from filesystem structure."""

    async def test_discovers_bc_with_entities_dir(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("entities",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "billing" in slugs

    async def test_discovers_bc_with_use_cases_dir(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "auth", layers=("use_cases",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "auth" in slugs

    async def test_skips_directory_without_bc_structure(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        # Package with no entities/ or use_cases/
        pkg = search / "utils"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "utils" not in slugs

    async def test_skips_reserved_words(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        # "apps" is a reserved word, even with BC structure
        _make_bc(search, "apps", layers=("entities",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "apps" not in slugs

    async def test_skips_dot_prefixed_dirs(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, ".hidden", layers=("entities",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert ".hidden" not in slugs

    async def test_skips_non_packages(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        # Directory with entities/ but no __init__.py
        bc = search / "not_a_package"
        bc.mkdir()
        (bc / "entities").mkdir()
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "not_a_package" not in slugs

    async def test_returns_sorted_by_slug(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "zebra", layers=("entities",))
        _make_bc(search, "alpha", layers=("entities",))
        _make_bc(search, "middle", layers=("entities",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert slugs == sorted(slugs)

    async def test_empty_search_root_returns_empty(self, tmp_path):
        repo = _make_repo(tmp_path)
        contexts = await repo.list_all()
        assert contexts == []

    async def test_nonexistent_search_root_returns_empty(self, tmp_path):
        repo = FilesystemBoundedContextRepository(
            project_root=tmp_path,
            search_root="does/not/exist",
        )
        contexts = await repo.list_all()
        assert contexts == []


# =============================================================================
# Structural markers
# =============================================================================


class TestStructuralMarkers:
    """Tests for detection of CA layer directories."""

    async def test_detects_all_layers(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(
            search,
            "full",
            layers=("entities", "use_cases", "repositories", "services", "tests"),
        )
        contexts = await repo.list_all()
        m = contexts[0].markers
        assert m.has_domain_models is True
        assert m.has_domain_use_cases is True
        assert m.has_domain_repositories is True
        assert m.has_domain_services is True
        assert m.has_tests is True

    async def test_minimal_bc_has_partial_markers(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "minimal", layers=("entities",))
        contexts = await repo.list_all()
        m = contexts[0].markers
        assert m.has_domain_models is True
        assert m.has_domain_use_cases is False
        assert m.has_domain_repositories is False


# =============================================================================
# Nested solutions (e.g. contrib/)
# =============================================================================


class TestNestedSolutions:
    """Tests for discovery of BCs inside nested solution containers."""

    async def test_discovers_bcs_inside_contrib(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        contrib = search / "contrib"
        contrib.mkdir()
        (contrib / "__init__.py").write_text("")
        _make_bc(contrib, "polling", layers=("use_cases",))
        _make_bc(contrib, "ceap", layers=("entities",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "polling" in slugs
        assert "ceap" in slugs

    async def test_contrib_bcs_have_is_contrib_true(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        contrib = search / "contrib"
        contrib.mkdir()
        (contrib / "__init__.py").write_text("")
        _make_bc(contrib, "polling", layers=("entities",))
        contexts = await repo.list_all()
        polling = [c for c in contexts if c.slug == "polling"][0]
        assert polling.is_contrib is True

    async def test_top_level_bc_has_is_contrib_false(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("entities",))
        contexts = await repo.list_all()
        billing = [c for c in contexts if c.slug == "billing"][0]
        assert billing.is_contrib is False


# =============================================================================
# Caching
# =============================================================================


class TestCaching:
    """Tests for discovery cache behaviour."""

    async def test_list_all_caches_results(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("entities",))

        first = await repo.list_all()
        # Add another BC after first discovery
        _make_bc(search, "auth", layers=("entities",))
        second = await repo.list_all()

        # Should return cached result (no "auth")
        assert len(first) == len(second)

    async def test_invalidate_cache_forces_rediscovery(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("entities",))

        first = await repo.list_all()
        _make_bc(search, "auth", layers=("entities",))
        repo.invalidate_cache()
        second = await repo.list_all()

        assert len(second) == len(first) + 1


# =============================================================================
# get() by slug
# =============================================================================


class TestGetBySlug:
    """Tests for retrieving a single BC by slug."""

    async def test_returns_matching_bc(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("entities",), docstring="Billing BC.")
        result = await repo.get("billing")
        assert result is not None
        assert result.slug == "billing"
        assert result.description == "Billing BC."

    async def test_returns_none_for_unknown_slug(self, tmp_path):
        repo = _make_repo(tmp_path)
        result = await repo.get("nonexistent")
        assert result is None

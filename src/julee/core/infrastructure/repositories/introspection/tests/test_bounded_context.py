"""Unit tests for the filesystem bounded context repository.

Exercises discovery logic that doctrine tests depend on to find bounded
contexts. Uses tmp_path to create realistic directory structures.
"""

from pathlib import Path

import pytest

from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
    _get_first_docstring_line,
)

pytestmark = pytest.mark.unit


# =============================================================================
# Helpers
# =============================================================================


def _make_bc(root, name, layers=("domain/models",), docstring=None):
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

    async def test_discovers_bc_with_domain_models_dir(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("domain/models",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "billing" in slugs

    async def test_discovers_bc_with_use_cases_dir(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "auth", layers=("usecases",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "auth" in slugs

    async def test_skips_directory_without_bc_structure(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        # Package with no entities/ or usecases/
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
        _make_bc(search, "apps", layers=("domain/models",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "apps" not in slugs

    async def test_skips_dot_prefixed_dirs(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, ".hidden", layers=("domain/models",))
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
        _make_bc(search, "zebra", layers=("domain/models",))
        _make_bc(search, "alpha", layers=("domain/models",))
        _make_bc(search, "middle", layers=("domain/models",))
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
            layers=(
                "domain/models",
                "usecases",
                "domain/repositories",
                "domain/services",
                "tests",
            ),
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
        _make_bc(search, "minimal", layers=("domain/models",))
        contexts = await repo.list_all()
        m = contexts[0].markers
        assert m.has_domain_models is True
        assert m.has_domain_use_cases is False
        assert m.has_domain_repositories is False


# =============================================================================
# Nested solutions: a package that holds bounded contexts without being one
# =============================================================================


class TestNestedSolutions:
    """Tests for discovery of BCs inside nested solution containers."""

    async def test_discovers_bcs_inside_a_nested_solution(self, tmp_path):
        """Any package holding contexts without being one is a container.

        No directory name is special about this: the shape decides.
        """
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        plugins = search / "plugins"
        plugins.mkdir()
        (plugins / "__init__.py").write_text("")
        _make_bc(plugins, "polling", layers=("usecases",))
        _make_bc(plugins, "ceap", layers=("domain/models",))
        contexts = await repo.list_all()
        slugs = [c.slug for c in contexts]
        assert "polling" in slugs
        assert "ceap" in slugs

    async def test_nested_bcs_are_marked_nested(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        plugins = search / "plugins"
        plugins.mkdir()
        (plugins / "__init__.py").write_text("")
        _make_bc(plugins, "polling", layers=("domain/models",))
        contexts = await repo.list_all()
        polling = [c for c in contexts if c.slug == "polling"][0]
        assert polling.is_nested is True

    async def test_top_level_bcs_are_not_marked_nested(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("domain/models",))
        contexts = await repo.list_all()
        billing = [c for c in contexts if c.slug == "billing"][0]
        assert billing.is_nested is False

    async def test_a_package_named_contrib_is_no_longer_special(self, tmp_path):
        """contrib was a reserved word while julee had one (ADR 012 step 7).

        A directory of that name is now read like any other: a bounded
        context if it has the layers, a container if it holds contexts.
        """
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "contrib", layers=("domain/models",))
        contexts = await repo.list_all()
        assert "contrib" in [c.slug for c in contexts]


# =============================================================================
# Caching
# =============================================================================


class TestCaching:
    """Tests for discovery cache behaviour."""

    async def test_list_all_caches_results(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("domain/models",))

        first = await repo.list_all()
        # Add another BC after first discovery
        _make_bc(search, "auth", layers=("domain/models",))
        second = await repo.list_all()

        # Should return cached result (no "auth")
        assert len(first) == len(second)

    async def test_invalidate_cache_forces_rediscovery(self, tmp_path):
        repo = _make_repo(tmp_path)
        search = tmp_path / "src" / "app"
        _make_bc(search, "billing", layers=("domain/models",))

        first = await repo.list_all()
        _make_bc(search, "auth", layers=("domain/models",))
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
        _make_bc(search, "billing", layers=("domain/models",), docstring="Billing BC.")
        result = await repo.get("billing")
        assert result is not None
        assert result.slug == "billing"
        assert result.description == "Billing BC."

    async def test_returns_none_for_unknown_slug(self, tmp_path):
        repo = _make_repo(tmp_path)
        result = await repo.get("nonexistent")
        assert result is None


ADR_001_LAYERS = (
    "domain/models",
    "domain/repositories",
    "domain/services",
    "usecases",
)


def package(path: Path) -> Path:
    """Make ``path`` a python package, with its parents."""
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").write_text("")
    return path


@pytest.fixture
def solution(tmp_path: Path) -> Path:
    """A solution whose one context is laid out as ADR 001 prescribes."""
    context = package(tmp_path / "src" / "solution" / "ordering")
    (context / "__init__.py").write_text('"""Ordering."""\n')
    for layer in ADR_001_LAYERS:
        package(context / layer)
    return tmp_path


async def test_a_context_under_domain_reports_the_layers_it_has(
    solution: Path,
) -> None:
    repository = FilesystemBoundedContextRepository(solution, "src/solution")

    (ordering,) = await repository.list_all()

    assert ordering.markers.has_domain_models
    assert ordering.markers.has_domain_repositories
    assert ordering.markers.has_domain_services
    assert ordering.markers.has_domain_use_cases


async def test_each_layer_is_visible_through_has_layer(
    solution: Path,
) -> None:
    repository = FilesystemBoundedContextRepository(solution, "src/solution")

    (ordering,) = await repository.list_all()

    for layer in ("models", "repositories", "services", "use_cases"):
        assert ordering.has_layer(layer), layer


# =============================================================================
# Cache husks
# =============================================================================


class TestCacheHusksAreNotBoundedContexts:
    """A directory left behind by deleted code must not count.

    Git does not track empty directories, so removing a package leaves
    the directory in every working tree that still has its caches. After
    ADR 012 moved the domain out of the framework, a checkout predating
    the move kept src/julee/domain/ holding nothing but __pycache__ —
    and julee looked like a bounded context to its own test.

    A fresh clone has no caches, so CI never sees this. It lands on
    whoever has the older checkout.
    """

    def _husk(self, root: Path, name: str, layer: str = "domain/models") -> Path:
        """A package whose marker directory holds only stale bytecode."""
        package = root / name
        package.mkdir(parents=True, exist_ok=True)
        (package / "__init__.py").write_text("")
        cache = package / layer / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "thing.cpython-312.pyc").write_bytes(b"\x00\x00\x00\x00")
        return package

    def test_a_models_directory_of_only_bytecode_is_not_a_context(
        self, tmp_path
    ) -> None:
        repo = _make_repo(tmp_path)
        self._husk(tmp_path / "src/app", "ghost")

        assert repo.describe(tmp_path / "src/app/ghost") is None

    def test_a_use_cases_directory_of_only_bytecode_is_not_a_context(
        self, tmp_path
    ) -> None:
        """Either marker alone makes a context, so both need the check."""
        repo = _make_repo(tmp_path)
        self._husk(tmp_path / "src/app", "ghost", layer="usecases")

        assert repo.describe(tmp_path / "src/app/ghost") is None

    def test_a_husk_is_not_discovered_among_real_contexts(self, tmp_path) -> None:
        repo = _make_repo(tmp_path)
        _make_bc(tmp_path / "src/app", "real")
        self._husk(tmp_path / "src/app", "ghost")

        assert [context.slug for context in repo.discover_all()] == ["real"]

    def test_an_empty_marker_directory_is_not_a_context(self, tmp_path) -> None:
        """The same hole without the bytecode: the directory alone."""
        repo = _make_repo(tmp_path)
        package = tmp_path / "src/app" / "ghost"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        (package / "domain" / "models").mkdir(parents=True)

        assert repo.describe(tmp_path / "src/app/ghost") is None

    def test_a_marker_directory_with_only_an_init_still_counts(self, tmp_path) -> None:
        """Guards against the fix being too strict.

        julee-ceap's domain/models holds one __init__.py and then
        subpackages, so requiring anything more than a .py file would
        stop a real kit being seen.
        """
        repo = _make_repo(tmp_path)
        package = tmp_path / "src/app" / "real"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        models = package / "domain" / "models"
        models.mkdir(parents=True)
        (models / "__init__.py").write_text("")
        (models / "__pycache__").mkdir()

        found = repo.describe(tmp_path / "src/app/real")

        assert found is not None
        assert found.slug == "real"

    def test_a_real_context_beside_its_caches_still_counts(self, tmp_path) -> None:
        repo = _make_repo(tmp_path)
        package = _make_bc(tmp_path / "src/app", "real")
        (package / "domain" / "models" / "__pycache__").mkdir()

        found = repo.describe(tmp_path / "src/app/real")

        assert found is not None
        assert found.slug == "real"

"""Unit tests for resolving adopted kits.

Installed and adopted are deliberately different sets: a kit that arrives
as a transitive dependency must not take effect on its own.
"""

from pathlib import Path

import pytest

from julee.core import kits as kits_module
from julee.core.entities.kit import Kit

pytestmark = pytest.mark.unit


def a_kit(slug: str, **overrides) -> Kit:
    fields = {"slug": slug, "name": slug.upper(), "package": f"julee_{slug}"}
    return Kit(**{**fields, **overrides})


@pytest.fixture
def solution(tmp_path: Path):
    """A solution root whose [tool.julee] kits we control."""

    def _solution(*slugs: str) -> Path:
        declared = ", ".join(f'"{slug}"' for slug in slugs)
        (tmp_path / "pyproject.toml").write_text(
            f'[tool.julee]\nsearch_root = "src/acme"\nkits = [{declared}]\n'
        )
        return tmp_path

    return _solution


@pytest.fixture
def installed(monkeypatch):
    def _installed(*kits: Kit) -> None:
        monkeypatch.setattr(kits_module, "installed_kits", lambda: tuple(kits))

    return _installed


def test_adoption_follows_the_declared_order(solution, installed) -> None:
    installed(a_kit("ceap"), a_kit("polling"))

    adopted = kits_module.adopted_kits(solution("polling", "ceap"))

    assert [kit.slug for kit in adopted] == ["polling", "ceap"]


def test_an_installed_kit_is_not_adopted_unless_declared(solution, installed) -> None:
    installed(a_kit("ceap"), a_kit("polling"))

    adopted = kits_module.adopted_kits(solution("ceap"))

    assert [kit.slug for kit in adopted] == ["ceap"]


def test_a_declared_slug_with_no_kit_is_reported(solution, installed) -> None:
    installed(a_kit("ceap"))
    root = solution("ceap", "untp")

    assert kits_module.unresolved_kit_slugs(root) == ("untp",)
    assert [kit.slug for kit in kits_module.adopted_kits(root)] == ["ceap"]


def test_a_solution_with_no_kits_section_adopts_nothing(tmp_path, installed) -> None:
    installed(a_kit("ceap"))
    (tmp_path / "pyproject.toml").write_text('[tool.julee]\nsearch_root = "src/acme"\n')

    assert kits_module.adopted_kits(tmp_path) == ()
    assert kits_module.unresolved_kit_slugs(tmp_path) == ()


def test_viewpoints_come_from_the_kits_that_declare_them(
    solution, installed, monkeypatch
) -> None:
    installed(a_kit("viewpoints", viewpoint=True), a_kit("ceap"))
    monkeypatch.setattr(
        kits_module,
        "kit_context_slugs",
        lambda kit: frozenset({"hcd", "c4"}) if kit.viewpoint else frozenset({"ceap"}),
    )

    assert kits_module.viewpoint_slugs(solution("viewpoints", "ceap")) == frozenset(
        {"hcd", "c4"}
    )


def test_a_kit_whose_package_is_missing_contributes_no_contexts() -> None:
    assert (
        kits_module.kit_context_slugs(a_kit("nope", package="not_a_real_pkg"))
        == frozenset()
    )


def test_contexts_are_discovered_from_an_installed_package() -> None:
    """A kit's contexts come from its package, not from its manifest.

    julee-viewpoints is installed in this workspace and is a real kit, so
    it stands for any other.
    """
    slugs = kits_module.kit_context_slugs(
        Kit(
            slug="viewpoints",
            name="Code-outward documentation",
            package="julee_viewpoints",
        )
    )

    assert "sphinx_hcd" in slugs


def _install_package(tmp_path: Path, monkeypatch, name: str, layers: tuple[str, ...]):
    """Put an importable package on sys.path, with the layers given."""
    package = tmp_path / name
    package.mkdir()
    (package / "__init__.py").write_text('"""A kit."""\n')
    for layer in layers:
        layer_dir = package / layer
        layer_dir.mkdir(parents=True)
        (layer_dir / "__init__.py").write_text("")
    monkeypatch.syspath_prepend(str(tmp_path))
    return package


def test_a_kit_whose_package_is_the_context_reports_it(tmp_path, monkeypatch) -> None:
    """A kit may be one bounded context, with nothing inside to find.

    julee-ceap and julee-polling are shaped that way: the package holds
    the layers directly. Looking only inside such a package finds
    nothing, which is what it did before this was fixed.
    """
    _install_package(tmp_path, monkeypatch, "acme_kit", ("usecases", "domain/models"))

    slugs = kits_module.kit_context_slugs(
        Kit(slug="acme", name="Acme", package="acme_kit")
    )

    assert slugs == frozenset({"acme_kit"})


def test_contexts_inside_a_package_win_over_the_package_itself(
    tmp_path, monkeypatch
) -> None:
    """A package holding contexts reports those, not itself."""
    package = _install_package(tmp_path, monkeypatch, "acme_two", ("usecases",))
    inner = package / "billing"
    (inner / "domain" / "models").mkdir(parents=True)
    (inner / "__init__.py").write_text("")
    (inner / "domain" / "__init__.py").write_text("")
    (inner / "domain" / "models" / "__init__.py").write_text("")

    slugs = kits_module.kit_context_slugs(
        Kit(slug="acme-two", name="Acme Two", package="acme_two")
    )

    assert slugs == frozenset({"billing"})


def test_a_package_with_no_bounded_contexts_yields_none() -> None:
    """julee itself: everything in it is kernel, integrations or reserved."""
    assert (
        kits_module.kit_context_slugs(Kit(slug="julee", name="julee", package="julee"))
        == frozenset()
    )

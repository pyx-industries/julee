"""Tests for a codebase recognising itself as a kit.

A kit is a julee solution in its own right and does not adopt itself, so
its own manifest is in none of the adoption functions. Doctrine run
against a kit still needs it — a rule about what a kit contributes has to
find the manifest doing the contributing.
"""

from pathlib import Path

import pytest

from julee.core.entities.kit import Kit
from julee.core.kits import contributed_objects, own_kit, own_packages

pytestmark = pytest.mark.unit


def a_kit(slug: str, package: str, **contributes: str | tuple[str, ...]) -> Kit:
    """A kit shipping that package."""
    return Kit(
        slug=slug,
        name=slug.upper(),
        package=package,
        contributes={
            point.replace("_", "."): paths for point, paths in contributes.items()
        },
    )


def a_package(root: Path, name: str) -> None:
    """A top-level package, the way a distribution lays one out."""
    package = root / "src" / name
    package.mkdir(parents=True)
    (package / "__init__.py").touch()


# =============================================================================
# own_packages
# =============================================================================


def test_a_src_layout_package_is_found(tmp_path: Path) -> None:
    a_package(tmp_path, "julee_hcd")

    assert own_packages(tmp_path) == frozenset({"julee_hcd"})


def test_a_flat_layout_package_is_found(tmp_path: Path) -> None:
    """Not every julee solution keeps its code under src/."""
    (tmp_path / "acme").mkdir()
    (tmp_path / "acme" / "__init__.py").touch()

    assert own_packages(tmp_path) == frozenset({"acme"})


def test_a_directory_without_an_init_is_not_a_package(tmp_path: Path) -> None:
    """docs/ and tests/ sit beside the package, not among them."""
    a_package(tmp_path, "julee_hcd")
    (tmp_path / "src" / "notes").mkdir()

    assert own_packages(tmp_path) == frozenset({"julee_hcd"})


def test_a_root_that_is_not_there_ships_nothing(tmp_path: Path) -> None:
    assert own_packages(tmp_path / "absent") == frozenset()


# =============================================================================
# own_kit
# =============================================================================


def test_the_kit_shipping_this_package_is_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_package(tmp_path, "julee_hcd")
    installed = (a_kit("c4", "julee_c4"), a_kit("hcd", "julee_hcd"))
    monkeypatch.setattr("julee.core.kits.installed_kits", lambda: installed)

    found = own_kit(tmp_path)

    assert found is not None
    assert found.slug == "hcd"


def test_a_solution_that_is_no_kit_has_no_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ordinary case: a solution adopts kits and is not one."""
    a_package(tmp_path, "acme")
    monkeypatch.setattr(
        "julee.core.kits.installed_kits", lambda: (a_kit("hcd", "julee_hcd"),)
    )

    assert own_kit(tmp_path) is None


def test_a_kit_that_is_not_installed_cannot_recognise_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The entry point is what carries a manifest, so it must be there."""
    a_package(tmp_path, "julee_hcd")
    monkeypatch.setattr("julee.core.kits.installed_kits", tuple)

    assert own_kit(tmp_path) is None


# =============================================================================
# contributed_objects
# =============================================================================


def test_a_point_the_kit_does_not_offer_gives_nothing() -> None:
    assert contributed_objects(a_kit("hcd", "julee_hcd"), "temporal.activities") == ()


def test_an_attribute_is_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    kit = a_kit("hcd", "julee_hcd", temporal_activities="json:dumps")

    import json

    assert contributed_objects(kit, "temporal.activities") == (json.dumps,)


def test_a_tuple_is_flattened_into_its_members() -> None:
    """A kit with eight activity classes names one tuple, not eight paths."""
    kit = a_kit("hcd", "julee_hcd", temporal_activities="json:__all__")

    import json

    found = contributed_objects(kit, "temporal.activities")

    assert found == tuple(json.__all__)
    assert len(found) > 1


def test_several_paths_keep_the_order_the_kit_declares() -> None:
    kit = a_kit("hcd", "julee_hcd", temporal_activities=("json:dumps", "json:loads"))

    import json

    assert contributed_objects(kit, "temporal.activities") == (json.dumps, json.loads)


def test_a_module_resolves_to_itself() -> None:
    kit = a_kit("hcd", "julee_hcd", sphinx_extension="json")

    import json

    assert contributed_objects(kit, "sphinx.extension") == (json,)


def test_a_path_naming_nothing_raises() -> None:
    """Silence here would be a worker quietly missing an activity."""
    kit = a_kit("hcd", "julee_hcd", temporal_activities="json:absent")

    with pytest.raises(AttributeError):
        contributed_objects(kit, "temporal.activities")

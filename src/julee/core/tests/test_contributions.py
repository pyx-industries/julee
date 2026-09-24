"""Tests for reading what the adopted kits contribute.

A kit declares what it offers; until now nothing read it, so a solution
adopting a kit still named that kit's modules by hand. These cover the
reading, which is the half that makes a manifest worth writing.
"""

from pathlib import Path

import pytest

from julee.core.entities.kit import Kit
from julee.core.kits import contributions, sphinx_extensions

pytestmark = pytest.mark.unit


def a_kit(slug: str, **contributes: str | tuple[str, ...]) -> Kit:
    """A kit offering these contributions."""
    return Kit(
        slug=slug,
        name=slug.upper(),
        package=f"julee_{slug}",
        contributes={
            point.replace("_", "."): paths for point, paths in contributes.items()
        },
    )


@pytest.fixture
def solution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A solution adopting viewpoints then ceap, in that order."""
    adopted = (
        a_kit(
            "viewpoints",
            sphinx_extension=(
                "julee_viewpoints.sphinx_hcd",
                "julee_viewpoints.sphinx_c4",
            ),
        ),
        a_kit(
            "ceap",
            sphinx_extension="julee_ceap.sphinx",
            fastapi_routers="julee_ceap.apps.api.app:app",
        ),
    )
    monkeypatch.setattr("julee.core.kits.adopted_kits", lambda _root: adopted)
    return tmp_path


# =============================================================================
# One point, several kits
# =============================================================================


def test_a_point_nobody_offers_gives_nothing(solution: Path) -> None:
    """Most solutions use a handful of the points that exist."""
    assert contributions(solution, "temporal.activities") == ()


def test_a_point_one_kit_offers_gives_that(solution: Path) -> None:
    """The ordinary case."""
    assert contributions(solution, "fastapi.routers") == (
        "julee_ceap.apps.api.app:app",
    )


def test_every_kit_offering_a_point_is_asked(solution: Path) -> None:
    """A solution wants all of them, not the first one it finds."""
    found = contributions(solution, "sphinx.extension")

    assert len(found) == 3


def test_a_kit_may_offer_several_at_one_point(solution: Path) -> None:
    """viewpoints ships three Sphinx extensions and one point for them."""
    found = contributions(solution, "sphinx.extension")

    assert "julee_viewpoints.sphinx_hcd" in found
    assert "julee_viewpoints.sphinx_c4" in found


def test_contributions_arrive_in_adoption_order(solution: Path) -> None:
    """So a solution controls the order by the order it lists its kits.

    Sphinx extensions can depend on each other's registrations, so this
    is the solution's decision to make and not the framework's.
    """
    found = contributions(solution, "sphinx.extension")

    assert found == (
        "julee_viewpoints.sphinx_hcd",
        "julee_viewpoints.sphinx_c4",
        "julee_ceap.sphinx",
    )


# =============================================================================
# Nothing is imported to answer
# =============================================================================


def test_a_path_naming_nothing_is_still_returned(tmp_path: Path, monkeypatch) -> None:
    """Reading a manifest imports nothing, and that holds here too.

    Resolving the path belongs to whichever integration knows the
    technology; this only says what was offered.
    """
    monkeypatch.setattr(
        "julee.core.kits.adopted_kits",
        lambda _root: (a_kit("x", fastapi_routers="nothing.that.exists:app"),),
    )

    assert contributions(tmp_path, "fastapi.routers") == ("nothing.that.exists:app",)


# =============================================================================
# The Sphinx helper
# =============================================================================


def test_sphinx_extensions_are_what_conf_py_needs(solution: Path) -> None:
    """A list of module paths, which is what Sphinx expects to be given."""
    extensions = sphinx_extensions(solution)

    assert isinstance(extensions, list)
    assert extensions == [
        "julee_viewpoints.sphinx_hcd",
        "julee_viewpoints.sphinx_c4",
        "julee_ceap.sphinx",
    ]


def test_a_solution_adopting_nothing_gets_an_empty_list(
    tmp_path: Path, monkeypatch
) -> None:
    """conf.py should be able to add its own to it without a check."""
    monkeypatch.setattr("julee.core.kits.adopted_kits", lambda _root: ())

    assert sphinx_extensions(tmp_path) == []


# =============================================================================
# A kit answering for itself
# =============================================================================


def test_a_kit_offering_one_path_answers_with_one() -> None:
    """A caller should not have to care whether it was one or several."""
    assert a_kit("x", fastapi_routers="a.b:app").contributed("fastapi.routers") == (
        "a.b:app",
    )


def test_a_kit_offering_nothing_at_a_point_answers_with_nothing() -> None:
    """Rather than raising, since most points are offered by most kits."""
    assert a_kit("x").contributed("sphinx.extension") == ()

"""Tests for the boundary rules.

ADR 012 §3 stated these in prose and nothing checked them, which is the
place a kit makes the dependency rule easiest to break.
"""

import pytest

from julee.core.doctrine.rules.boundary import (
    imports_of_unadopted_kits,
    imports_reaching_into_a_kit,
    within_a_composition_root,
)
from julee.core.parsers.imports import ImportInfo

pytestmark = pytest.mark.unit


def an_import(module: str, file: str = "acme/domain/models/order.py") -> ImportInfo:
    """An import of a module, from somewhere in a solution."""
    return ImportInfo(module=module, file=file, line=7)


UNADOPTED = {"julee_ceap": "ceap"}
ADOPTED = ("julee_hcd", "julee_c4")


# =============================================================================
# A solution imports what it has adopted
# =============================================================================


def test_importing_an_adopted_kit_is_allowed() -> None:
    """The ordinary case, and the reason to adopt one."""
    imports = [an_import("julee_hcd.domain.models.story")]

    assert imports_of_unadopted_kits(imports, UNADOPTED) == []


def test_importing_an_unadopted_kit_is_reported() -> None:
    """Depending on something the solution never declared."""
    imports = [an_import("julee_ceap.domain.models.document")]

    objections = imports_of_unadopted_kits(imports, UNADOPTED)

    assert len(objections) == 1
    assert "has not adopted" in objections[0]


def test_importing_the_kit_package_itself_is_reported() -> None:
    """`import julee_ceap` is as much a dependency as reaching inside it."""
    assert imports_of_unadopted_kits([an_import("julee_ceap")], UNADOPTED) != []


def test_a_package_merely_starting_with_the_same_letters_is_allowed() -> None:
    """julee_ceap_extras is not julee_ceap."""
    imports = [an_import("julee_ceap_extras.helpers")]

    assert imports_of_unadopted_kits(imports, UNADOPTED) == []


def test_the_objection_points_at_the_line() -> None:
    """So that fixing it does not mean searching the file."""
    objection = imports_of_unadopted_kits([an_import("julee_ceap")], UNADOPTED)[0]

    assert "acme/domain/models/order.py:7" in objection


def test_a_solution_importing_nothing_of_anyone_else_offends_nothing() -> None:
    """Most files import only the standard library and their own package."""
    imports = [an_import("dataclasses"), an_import("acme.domain.models")]

    assert imports_of_unadopted_kits(imports, UNADOPTED) == []


# =============================================================================
# How far into a kit a solution may reach
# =============================================================================


def test_importing_a_kit_s_entities_is_allowed() -> None:
    """Its models are what a kit offers."""
    imports = [an_import("julee_hcd.domain.models.story")]

    assert imports_reaching_into_a_kit(imports, ADOPTED) == []


def test_importing_a_kit_s_use_cases_is_allowed() -> None:
    """So are its use cases."""
    imports = [an_import("julee_hcd.usecases.derive_personas")]

    assert imports_reaching_into_a_kit(imports, ADOPTED) == []


def test_importing_a_kit_s_repository_protocol_is_allowed() -> None:
    """A protocol is a contract, which is the point of offering one."""
    imports = [an_import("julee_hcd.domain.repositories.story")]

    assert imports_reaching_into_a_kit(imports, ADOPTED) == []


def test_reaching_into_a_kit_s_infrastructure_is_reported() -> None:
    """How a kit stores things is a decision it may change."""
    imports = [an_import("julee_hcd.infrastructure.repositories.memory.story")]

    objections = imports_reaching_into_a_kit(imports, ADOPTED)

    assert len(objections) == 1
    assert "infrastructure" in objections[0]


def test_reaching_into_a_kit_s_apps_is_reported() -> None:
    """How a kit is served is also its own business."""
    imports = [an_import("julee_c4.apps.api")]

    assert imports_reaching_into_a_kit(imports, ADOPTED) != []


def test_a_module_merely_named_like_infrastructure_is_allowed() -> None:
    """julee_hcd.infrastructure_notes is not julee_hcd.infrastructure."""
    imports = [an_import("julee_hcd.infrastructure_notes")]

    assert imports_reaching_into_a_kit(imports, ADOPTED) == []


def test_an_unadopted_kit_s_infrastructure_is_left_to_the_other_rule() -> None:
    """One fault, one objection: importing it at all is the problem."""
    imports = [an_import("julee_ceap.infrastructure.repositories")]

    assert imports_reaching_into_a_kit(imports, ADOPTED) == []


# =============================================================================
# Nothing at all
# =============================================================================


@pytest.mark.parametrize(
    "rule",
    [
        lambda: imports_of_unadopted_kits([], {}),
        lambda: imports_reaching_into_a_kit([], ()),
    ],
)
def test_a_solution_adopting_no_kits_offends_nothing(rule) -> None:
    """Which julee itself does."""
    assert rule() == []


# ---------------------------------------------------------------------------
# within_a_composition_root
# ---------------------------------------------------------------------------


def test_a_file_under_apps_is_a_composition_root() -> None:
    assert within_a_composition_root(("apps", "api", "app.py"), ("apps",))


def test_a_file_outside_is_not() -> None:
    assert not within_a_composition_root(("hcd", "usecases", "x.py"), ("apps",))


def test_apps_is_found_at_any_depth() -> None:
    """What "apps" already meant: a context's own apps/ counted too."""
    assert within_a_composition_root(("hcd", "apps", "cli.py"), ("apps",))


def test_a_multi_segment_root_matches_its_run() -> None:
    """The case this exists for: viewpoints wires in sphinx_c4/sphinx."""
    parts = ("sphinx_c4", "sphinx", "context.py")

    assert within_a_composition_root(parts, ("sphinx_c4/sphinx",))


def test_a_multi_segment_root_matches_deeper_files() -> None:
    parts = ("sphinx_c4", "sphinx", "wiring", "context.py")

    assert within_a_composition_root(parts, ("sphinx_c4/sphinx",))


def test_the_segments_of_a_multi_segment_root_must_be_adjacent() -> None:
    """sphinx_c4/other/sphinx is not sphinx_c4/sphinx."""
    parts = ("sphinx_c4", "other", "sphinx", "context.py")

    assert not within_a_composition_root(parts, ("sphinx_c4/sphinx",))


def test_the_segments_must_be_in_order() -> None:
    parts = ("sphinx", "sphinx_c4", "context.py")

    assert not within_a_composition_root(parts, ("sphinx_c4/sphinx",))


def test_half_a_root_is_not_a_match() -> None:
    """Matching "sphinx" alone would exempt every directive as well."""
    assert not within_a_composition_root(
        ("sphinx_hcd", "sphinx", "directives", "persona.py"),
        ("sphinx_c4/sphinx",),
    )


def test_any_of_several_roots_will_do() -> None:
    roots = ("apps", "sphinx_c4/sphinx", "sphinx_hcd/sphinx")

    assert within_a_composition_root(("sphinx_hcd", "sphinx", "context.py"), roots)


def test_declaring_no_roots_exempts_nothing() -> None:
    """A solution that says composition_roots = [] holds everything to
    what its kits offer, which is a legitimate thing to want."""
    assert not within_a_composition_root(("apps", "api", "app.py"), ())


def test_an_empty_root_string_is_ignored_rather_than_matching_everything() -> None:
    """Otherwise a stray "" in the list would switch the rule off."""
    assert not within_a_composition_root(("hcd", "usecases", "x.py"), ("",))


def test_a_root_with_a_trailing_slash_still_works() -> None:
    """A hand-written toml list is going to contain one of these."""
    assert within_a_composition_root(("apps", "api", "app.py"), ("apps/",))

"""Tests for the boundary rules.

ADR 012 §3 stated these in prose and nothing checked them, which is the
place a kit makes the dependency rule easiest to break.
"""

import pytest

from julee.core.doctrine.rules.boundary import (
    imports_of_unadopted_kits,
    imports_reaching_into_a_kit,
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

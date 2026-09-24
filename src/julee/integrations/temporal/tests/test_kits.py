"""Tests for resolving the activity classes the adopted kits contribute.

The last contribution point to get a consumer. Until it had one, a
solution adopting CEAP imported its activity classes by hand, which made
the manifest a description nobody acted on (#193).
"""

from pathlib import Path

import pytest

from julee.core.entities.kit import Kit
from julee.integrations.temporal.kits import CONTRIBUTION_POINT, kit_activities

pytestmark = pytest.mark.unit


class Alpha:
    """Stands in for a decorated repository."""


class Beta:
    """And another, so order can be checked."""


class Gamma:
    """From a second kit."""


ACTIVITY_CLASSES = (Alpha, Beta)
SECOND_KIT_CLASSES = (Gamma,)
NOT_A_CLASS = ("julee_acme.repositories:Alpha",)


def a_kit(slug: str, *paths: str) -> Kit:
    """A kit contributing these paths at the activity point."""
    return Kit(
        slug=slug,
        name=slug.upper(),
        package=f"julee_{slug}",
        contributes={CONTRIBUTION_POINT: paths} if paths else {},
    )


def adopting(monkeypatch: pytest.MonkeyPatch, *kits: Kit) -> Path:
    """A solution adopting these kits, in this order.

    Patched where kit_activities looks it up, not where it is defined:
    the module binds the name at import, so patching julee.core.kits
    would leave the real function in place — and the tests that expect
    nothing would still pass, having resolved a real empty solution.
    """
    monkeypatch.setattr(
        "julee.integrations.temporal.kits.adopted_kits", lambda _root: kits
    )
    return Path("/nowhere")


HERE = "julee.integrations.temporal.tests.test_kits"


def test_a_solution_adopting_nothing_gets_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert kit_activities(adopting(monkeypatch)) == []


def test_a_kit_offering_nothing_here_contributes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Most kits have no activities at all; ceap and polling do."""
    solution = adopting(monkeypatch, a_kit("hcd"))

    assert kit_activities(solution) == []


def test_the_tuple_a_kit_points_at_is_flattened(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Eight activity classes travel as one contribution, not eight paths."""
    solution = adopting(monkeypatch, a_kit("ceap", f"{HERE}:ACTIVITY_CLASSES"))

    assert kit_activities(solution) == [Alpha, Beta]


def test_classes_arrive_in_adoption_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """A solution controls registration order by the order it lists kits."""
    solution = adopting(
        monkeypatch,
        a_kit("ceap", f"{HERE}:ACTIVITY_CLASSES"),
        a_kit("polling", f"{HERE}:SECOND_KIT_CLASSES"),
    )

    assert kit_activities(solution) == [Alpha, Beta, Gamma]


def test_a_kit_may_offer_several_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """ceap has two activity modules: its repositories and its services."""
    solution = adopting(
        monkeypatch,
        a_kit("ceap", f"{HERE}:ACTIVITY_CLASSES", f"{HERE}:SECOND_KIT_CLASSES"),
    )

    assert kit_activities(solution) == [Alpha, Beta, Gamma]


def test_contributing_something_that_is_not_a_class_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dropping it quietly would leave a worker missing an activity.

    The workflow calling it then waits for its timeout, which is the
    failure furthest from the cause and the one this whole contribution
    point exists to prevent.
    """
    solution = adopting(monkeypatch, a_kit("ceap", f"{HERE}:NOT_A_CLASS"))

    with pytest.raises(TypeError, match="ceap contributes"):
        kit_activities(solution)


def test_a_path_naming_nothing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Startup, loudly, beats a worker quietly short of an activity."""
    solution = adopting(monkeypatch, a_kit("ceap", f"{HERE}:ABSENT"))

    with pytest.raises(AttributeError):
        kit_activities(solution)


def test_a_module_that_is_not_there_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    solution = adopting(monkeypatch, a_kit("ceap", "julee_gone.activities:CLASSES"))

    with pytest.raises(ImportError):
        kit_activities(solution)

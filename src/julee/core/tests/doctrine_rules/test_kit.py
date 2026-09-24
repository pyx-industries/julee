"""Tests for the kit rules."""

import pytest

from julee.core.doctrine.rules.kit import (
    activities_not_contributed,
    circular_requirements,
    duplicate_slugs,
    malformed_contributions,
    slugs_colliding_with_contexts,
    unadopted_requirements,
    unimportable_packages,
)
from julee.core.entities.code_info import ClassInfo
from julee.core.entities.kit import Kit

pytestmark = pytest.mark.unit


def a_kit(
    slug: str = "hcd",
    requires: tuple[str, ...] = (),
    contributes: dict[str, str | tuple[str, ...]] | None = None,
    package: str | None = None,
) -> Kit:
    """A kit that offends none of the rules."""
    return Kit(
        slug=slug,
        name=slug.upper(),
        package=package or f"julee_{slug}",
        requires=requires,
        contributes=contributes or {},
    )


def everything_imports(_package: str) -> bool:
    """A world where every package is installed."""
    return True


def nothing_imports(_package: str) -> bool:
    """A world where none is."""
    return False


# =============================================================================
# Requirements are adopted, explicitly
# =============================================================================


def test_a_kit_requiring_nothing_is_allowed() -> None:
    """Most kits require nothing."""
    assert unadopted_requirements([a_kit()]) == []


def test_a_kit_requiring_an_adopted_kit_is_allowed() -> None:
    """The requirement is met, so nothing to say."""
    kits = [a_kit(slug="ceap", requires=("polling",)), a_kit(slug="polling")]

    assert unadopted_requirements(kits) == []


def test_a_kit_requiring_an_unadopted_kit_is_reported() -> None:
    """A kit cannot pull in another on the solution's behalf."""
    objections = unadopted_requirements([a_kit(slug="ceap", requires=("polling",))])

    assert objections == ["ceap requires polling, which is not adopted"]


def test_every_unmet_requirement_is_reported() -> None:
    """Fixing one at a time would mean running doctrine once per fix."""
    kits = [a_kit(slug="ceap", requires=("polling", "hcd"))]

    assert len(unadopted_requirements(kits)) == 2


# =============================================================================
# Requirements do not go round
# =============================================================================


def test_a_chain_of_requirements_is_allowed() -> None:
    """Depth is fine; it is the cycle that has no install order."""
    kits = [
        a_kit(slug="a", requires=("b",)),
        a_kit(slug="b", requires=("c",)),
        a_kit(slug="c"),
    ]

    assert circular_requirements(kits) == []


def test_a_kit_requiring_itself_is_a_cycle() -> None:
    """The shortest one there is."""
    assert circular_requirements([a_kit(slug="a", requires=("a",))]) == ["a"]


def test_two_kits_requiring_each_other_is_a_cycle() -> None:
    """Both are named, because either could be the one to change."""
    kits = [a_kit(slug="a", requires=("b",)), a_kit(slug="b", requires=("a",))]

    assert circular_requirements(kits) == ["a", "b"]


def test_a_longer_cycle_is_found() -> None:
    """Three deep, which no amount of reading a manifest would reveal."""
    kits = [
        a_kit(slug="a", requires=("b",)),
        a_kit(slug="b", requires=("c",)),
        a_kit(slug="c", requires=("a",)),
    ]

    assert circular_requirements(kits) == ["a", "b", "c"]


def test_a_diamond_is_not_a_cycle() -> None:
    """Two kits requiring the same third is ordinary, not circular."""
    kits = [
        a_kit(slug="a", requires=("b", "c")),
        a_kit(slug="b", requires=("d",)),
        a_kit(slug="c", requires=("d",)),
        a_kit(slug="d"),
    ]

    assert circular_requirements(kits) == []


# =============================================================================
# Slugs address exactly one thing
# =============================================================================


def test_distinct_slugs_are_allowed() -> None:
    """The ordinary case."""
    assert duplicate_slugs([a_kit(slug="hcd"), a_kit(slug="c4")]) == []


def test_two_kits_sharing_a_slug_are_reported() -> None:
    """Which one [tool.julee] kits means would be anyone's guess."""
    kits = [a_kit(slug="hcd"), a_kit(slug="hcd", package="other_hcd")]

    assert duplicate_slugs(kits) == ["hcd"]


def test_a_kit_slug_that_is_also_a_context_is_reported() -> None:
    """Both are names in one namespace as far as a reader is concerned."""
    objections = slugs_colliding_with_contexts([a_kit(slug="hcd")], ["hcd", "billing"])

    assert objections == ["hcd"]


def test_a_kit_slug_unlike_any_context_is_allowed() -> None:
    """The ordinary case."""
    assert slugs_colliding_with_contexts([a_kit(slug="hcd")], ["billing"]) == []


# =============================================================================
# A manifest describes something that exists
# =============================================================================


def test_a_kit_whose_package_imports_is_allowed() -> None:
    """The ordinary case."""
    assert unimportable_packages([a_kit()], everything_imports) == []


def test_a_kit_whose_package_is_absent_is_reported() -> None:
    """A manifest naming a package nobody can import describes nothing."""
    objections = unimportable_packages([a_kit()], nothing_imports)

    assert objections == ["hcd declares package julee_hcd"]


# =============================================================================
# Contributions are paths, so that reading a manifest imports nothing
# =============================================================================


def test_a_dotted_path_is_allowed() -> None:
    """The ordinary case."""
    kit = a_kit(contributes={"sphinx.extension": "julee_hcd.sphinx"})

    assert malformed_contributions([kit]) == []


def test_a_path_with_an_attribute_is_allowed() -> None:
    """module:attr is how a contribution names something inside a module."""
    kit = a_kit(contributes={"fastapi.routers": "julee_ceap.apps.api:router"})

    assert malformed_contributions([kit]) == []


@pytest.mark.parametrize(
    "path",
    ["", "julee_hcd:a:b", "julee_hcd sphinx"],
    ids=["empty", "two colons", "a space"],
)
def test_a_path_that_is_not_one_is_reported(path: str) -> None:
    """Whatever consumes this has to resolve it; shape is checked here."""
    kit = a_kit(contributes={"sphinx.extension": path})

    assert malformed_contributions([kit]) != []


def test_the_objection_names_the_kit_the_point_and_the_path() -> None:
    """A manifest may have several, and only one of them is wrong."""
    kit = a_kit(contributes={"sphinx.extension": "a b"})

    objection = malformed_contributions([kit])[0]

    assert "hcd" in objection
    assert "sphinx.extension" in objection
    assert "a b" in objection


# =============================================================================
# Nothing at all
# =============================================================================


@pytest.mark.parametrize(
    "rule",
    [
        lambda: unadopted_requirements([]),
        lambda: circular_requirements([]),
        lambda: duplicate_slugs([]),
        lambda: slugs_colliding_with_contexts([], []),
        lambda: unimportable_packages([], nothing_imports),
        lambda: malformed_contributions([]),
    ],
)
def test_a_solution_adopting_no_kits_offends_nothing(rule) -> None:
    """Which julee itself does, now its domain code ships as kits."""
    assert rule() == []


def test_a_point_offering_several_paths_is_allowed() -> None:
    """A kit shipping three Sphinx extensions offers three at one point."""
    kit = a_kit(
        contributes={"sphinx.extension": ("julee_viewpoints.a", "julee_viewpoints.b")}
    )

    assert malformed_contributions([kit]) == []


def test_one_bad_path_among_several_is_reported() -> None:
    """The others being fine is no reason to stay quiet about this one."""
    kit = a_kit(contributes={"sphinx.extension": ("julee_viewpoints.a", "a b")})

    objections = malformed_contributions([kit])

    assert len(objections) == 1
    assert "a b" in objections[0]


# ---------------------------------------------------------------------------
# activities_not_contributed
# ---------------------------------------------------------------------------

ACTIVITY = "julee.integrations.temporal.decorators.temporal_activity_registration"


def a_class(name: str, decorators: tuple[str, ...] = ()) -> ClassInfo:
    """A parsed class carrying the given decorators."""
    return ClassInfo(name=name, file=f"{name.lower()}.py", decorators=list(decorators))


def test_an_undecorated_class_need_not_be_contributed() -> None:
    assert activities_not_contributed([a_class("Plain")], []) == []


def test_a_decorated_class_that_is_contributed_is_allowed() -> None:
    assert activities_not_contributed([a_class("Repo", (ACTIVITY,))], ["Repo"]) == []


def test_a_decorated_class_nobody_contributes_is_reported() -> None:
    violations = activities_not_contributed([a_class("Repo", (ACTIVITY,))], [])

    assert len(violations) == 1
    assert "Repo" in violations[0]
    assert "repo.py" in violations[0]


def test_a_kit_with_activities_and_no_contributions_is_not_let_through() -> None:
    """The failure being guarded is an empty manifest, not a skip.

    Three rules have silently passed over empty data before this one, so
    it gets a test of its own rather than being read off the case above.
    """
    violations = activities_not_contributed(
        [a_class("A", (ACTIVITY,)), a_class("B", (ACTIVITY,))], []
    )

    assert len(violations) == 2


def test_no_classes_at_all_is_allowed() -> None:
    assert activities_not_contributed([], []) == []


def test_contributing_more_than_the_kit_has_is_not_this_rule_s_business() -> None:
    """Naming something absent is contributions_naming_nothing's job."""
    assert activities_not_contributed([], ["Gone"]) == []


def test_the_decorator_is_matched_however_it_was_imported() -> None:
    """A re-export and the defining module resolve to two paths.

    ``from julee.integrations.temporal import temporal_activity_registration``
    and the same name from ``...temporal.decorators`` are one decorator,
    so the rule matches on the last segment.
    """
    reexported = "julee.integrations.temporal.temporal_activity_registration"

    assert len(activities_not_contributed([a_class("Repo", (reexported,))], [])) == 1


def test_an_unrelated_decorator_does_not_make_a_class_an_activity() -> None:
    plain = a_class("Repo", ("dataclasses.dataclass",))

    assert activities_not_contributed([plain], []) == []


def test_a_decorator_merely_ending_in_the_name_is_not_a_match() -> None:
    """`my_temporal_activity_registration` is a different decorator."""
    lookalike = "elsewhere.my_temporal_activity_registration"

    assert activities_not_contributed([a_class("Repo", (lookalike,))], []) == []


def test_the_decorator_being_checked_can_be_named() -> None:
    violations = activities_not_contributed(
        [a_class("Flow", ("temporalio.workflow.defn",))], [], decorator="defn"
    )

    assert len(violations) == 1
    assert "@defn" in violations[0]


def test_violations_are_sorted_so_the_report_is_stable() -> None:
    classes = [a_class(n, (ACTIVITY,)) for n in ("Zebra", "Aardvark", "Mongoose")]

    violations = activities_not_contributed(classes, [])

    assert [v.split()[0] for v in violations] == ["Aardvark", "Mongoose", "Zebra"]

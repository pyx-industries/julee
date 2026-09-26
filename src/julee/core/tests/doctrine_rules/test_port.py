"""Tests for the driven port rules."""

import pytest

from julee.core.doctrine.rules.port import (
    port_implementations_outside_infrastructure,
    ports_bound_to_entities_they_should_not_be,
    ports_misnamed_for_their_directory,
    protocols_in,
)
from julee.core.entities.code_info import ClassInfo, MethodInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

pytestmark = pytest.mark.unit


def a_port(
    name: str,
    directory: str = "services",
    slug: str = "polling",
    references: tuple[str, ...] = (),
) -> tuple[str, CodeArtifactWithContext]:
    """A protocol found under one of ADR 016's port directories.

    `references` become method return types, because a class's
    referenced_types is read off its signatures rather than set.
    """
    return (
        directory,
        CodeArtifactWithContext(
            bounded_context=slug,
            artifact=ClassInfo(
                name=name,
                file=f"{name.lower()}.py",
                methods=[
                    MethodInfo(name=f"method_{i}", return_type=reference)
                    for i, reference in enumerate(references)
                ],
            ),
        ),
    )


# =============================================================================
# What a port calls itself
# =============================================================================


def test_each_directory_accepts_the_role_it_is_for() -> None:
    ports = [
        a_port("PollerService", "services"),
        a_port("SchemaOracle", "oracles"),
        a_port("NewDataCalculator", "calculators"),
        a_port("ClockWitness", "witnesses"),
    ]

    assert ports_misnamed_for_their_directory(ports) == []


def test_a_handler_in_its_own_directory_is_accepted() -> None:
    ports = [a_port("EpicCreatedHandler", "handlers")]

    assert ports_misnamed_for_their_directory(ports) == []


def test_a_handler_left_in_services_is_told_to_move() -> None:
    """Handlers shared domain/services/ until #256.

    That made Handler the one port told apart by its name rather than its
    directory — the mechanism every other port stopped using in #175.
    hcd's services package held eleven handlers and no services at all,
    so the directory's name described nothing in it.
    """
    objections = ports_misnamed_for_their_directory([a_port("EpicCreatedHandler")])

    assert len(objections) == 1
    assert "domain/handlers/" in objections[0]


def test_a_handler_in_the_wrong_place_is_not_told_to_rename_itself() -> None:
    """The diagnosis has to match the defect.

    EpicCreatedHandler is named correctly and shelved wrongly. Telling its
    author to rename it would be both the wrong advice and the wrong
    explanation of what doctrine objects to.
    """
    objections = ports_misnamed_for_their_directory([a_port("EpicCreatedHandler")])

    assert "Rename it" not in objections[0]
    assert "move it" in objections[0]


def test_a_role_is_not_accepted_in_the_wrong_directory() -> None:
    """The claim has to match the shelf it was put on.

    An Oracle must be reached through an activity and a Calculator need
    not be. Filing one under the other's directory would say the opposite
    of what the name says, and one of the two would be wrong.
    """
    objections = ports_misnamed_for_their_directory(
        [a_port("SchemaOracle", "calculators")]
    )

    assert len(objections) == 1
    assert "domain/calculators/" in objections[0]


def test_a_port_claiming_nothing_is_objected_to() -> None:
    objections = ports_misnamed_for_their_directory(
        [a_port("NewDataAnalyzer", "calculators")]
    )

    assert len(objections) == 1
    assert "polling.NewDataAnalyzer" in objections[0]


def test_the_objection_names_both_ways_out() -> None:
    """Rename it, or move it. The message should not leave a reader guessing."""
    objections = ports_misnamed_for_their_directory([a_port("Snoop", "oracles")])

    assert "Rename it" in objections[0]
    assert "belongs in another" in objections[0]


def test_each_directory_now_admits_exactly_one_role() -> None:
    """services/ held two until handlers were given their own directory."""
    objections = ports_misnamed_for_their_directory([a_port("Snoop", "services")])

    assert "*Service" in objections[0]
    assert "*Handler" not in objections[0]


def test_a_directory_with_no_declared_role_is_left_alone() -> None:
    """Repositories declare themselves by inheritance, not by suffix.

    RepositoryOf[Entity] is a stronger claim than a name because mypy
    reads it too, so repositories are absent from ROLES_BY_DIRECTORY and
    the one-entity rule checks them instead.
    """
    assert ports_misnamed_for_their_directory([a_port("Widgets", "repositories")]) == []


def test_every_offender_is_named_rather_than_just_the_first() -> None:
    ports = [
        a_port("Snoop", "oracles"),
        a_port("SchemaOracle", "oracles"),
        a_port("Lurk", "witnesses"),
    ]

    assert len(ports_misnamed_for_their_directory(ports)) == 2


# =============================================================================
# What a port is bound to
# =============================================================================


ENTITIES = {"polling": {"PollingConfig", "PollingResult"}}


def test_an_oracle_naming_no_entity_is_fine() -> None:
    ports = [a_port("SchemaOracle", "oracles", references=("str", "dict"))]

    assert ports_bound_to_entities_they_should_not_be(ports, ENTITIES) == []


def test_an_oracle_naming_an_entity_is_objected_to() -> None:
    """Almost always a repository that wandered."""
    ports = [a_port("SchemaOracle", "oracles", references=("PollingConfig",))]

    objections = ports_bound_to_entities_they_should_not_be(ports, ENTITIES)

    assert len(objections) == 1
    assert "PollingConfig" in objections[0]
    assert "repository" in objections[0]


def test_a_witness_naming_an_entity_is_objected_to() -> None:
    ports = [a_port("ClockWitness", "witnesses", references=("PollingResult",))]

    objections = ports_bound_to_entities_they_should_not_be(ports, ENTITIES)

    assert len(objections) == 1
    assert "PollingResult" in objections[0]


def test_the_objection_names_the_role_in_english() -> None:
    """Written because the first draft said "a witnesse is bound to...".

    The role came from stripping an s off the directory name, which works
    for oracles and not for witnesses. It is now looked up.
    """
    ports = [a_port("ClockWitness", "witnesses", references=("PollingResult",))]

    objections = ports_bound_to_entities_they_should_not_be(ports, ENTITIES)

    assert "a Witness is" in objections[0]


def test_a_calculator_may_be_bound_to_anything() -> None:
    """The decision this test exists to pin down.

    ADR 016 puts a calculator on the inline row at any arity: what makes
    it one is that its answer follows from its arguments, not how many
    entities those arguments involve. A calculator combining two entities
    is as legitimate as one comparing two byte strings.
    """
    ports = [
        a_port(
            "PriorityCalculator",
            "calculators",
            references=("PollingConfig", "PollingResult"),
        )
    ]

    assert ports_bound_to_entities_they_should_not_be(ports, ENTITIES) == []


def test_a_service_is_left_to_its_own_rule() -> None:
    """Services are bound to two or more; that is not this rule's business."""
    ports = [a_port("PollerService", "services", references=("PollingConfig",))]

    assert ports_bound_to_entities_they_should_not_be(ports, ENTITIES) == []


def test_an_entity_of_another_context_is_not_counted() -> None:
    """The intersection is with this context's entities, not every name."""
    ports = [a_port("SchemaOracle", "oracles", references=("Document",))]

    assert ports_bound_to_entities_they_should_not_be(ports, ENTITIES) == []


# =============================================================================
# Shaping what a parser found
# =============================================================================


def test_protocols_in_pairs_each_class_with_its_directory() -> None:
    classes = [ClassInfo(name="SchemaOracle"), ClassInfo(name="HealthOracle")]

    paired = protocols_in("oracles", classes, "ceap")

    assert [directory for directory, _ in paired] == ["oracles", "oracles"]
    assert [found.bounded_context for _, found in paired] == ["ceap", "ceap"]


def test_protocols_in_an_empty_directory_is_empty() -> None:
    assert protocols_in("witnesses", [], "ceap") == []


# =============================================================================
# What layer a port may be written in (#236)
# =============================================================================


def at(path: str, name: str, slug: str = "polling") -> tuple[str, ClassInfo]:
    """A class found at a path relative to its bounded context root."""
    return (slug, ClassInfo(name=name, file=path))


def test_a_protocol_in_its_own_port_directory_is_where_it_belongs() -> None:
    found = [at("domain/services/poller.py", "PollerService")]

    assert port_implementations_outside_infrastructure(found) == []


def test_an_implementation_under_infrastructure_is_where_it_belongs() -> None:
    found = [at("infrastructure/services/http_poller.py", "HttpPollerService")]

    assert port_implementations_outside_infrastructure(found) == []


def test_a_service_in_the_apps_layer_is_objected_to() -> None:
    """The case that found this rule a subject: a facade wearing a port's
    name, where a reader cannot tell which half is wrong."""
    found = [at("apps/api/services/startup.py", "SystemInitializationService")]

    (objection,) = port_implementations_outside_infrastructure(found)

    assert "SystemInitializationService" in objection
    assert "apps/api/services/startup.py" in objection


def test_a_port_in_usecases_is_objected_to() -> None:
    found = [at("usecases/poll.py", "ScheduleCalculator")]

    (objection,) = port_implementations_outside_infrastructure(found)

    assert "domain/calculators/" in objection


@pytest.mark.parametrize(
    "name",
    ["ThingService", "ThingHandler", "ThingOracle", "ThingCalculator", "ThingWitness"],
)
def test_every_named_role_is_held_to_the_rule(name: str) -> None:
    """All five suffixes are claims, so all five are placed."""
    assert port_implementations_outside_infrastructure([at("apps/cli.py", name)])


def test_a_repository_claims_nothing_and_is_left_alone() -> None:
    """It declares its entity by inheriting RepositoryOf[Entity], which is
    why it is exempt from the naming rules and from this one."""
    found = [at("usecases/poll.py", "PollingRepository")]

    assert port_implementations_outside_infrastructure(found) == []


def test_a_class_claiming_no_role_is_left_alone() -> None:
    found = [at("apps/api/routes.py", "PollingRouter")]

    assert port_implementations_outside_infrastructure(found) == []


def test_a_port_under_the_wrong_port_directory_is_left_to_the_naming_rule() -> None:
    """ports_misnamed_for_their_directory already objects to it, and
    reporting the same class twice helps nobody."""
    found = [at("domain/oracles/poller.py", "PollerService")]

    assert port_implementations_outside_infrastructure(found) == []


def test_a_class_with_no_path_is_not_guessed_about() -> None:
    assert port_implementations_outside_infrastructure([at("", "PollerService")]) == []


def test_the_rule_is_silent_about_an_empty_codebase() -> None:
    """Which is what the canary in the doctrine test exists to catch."""
    assert port_implementations_outside_infrastructure([]) == []

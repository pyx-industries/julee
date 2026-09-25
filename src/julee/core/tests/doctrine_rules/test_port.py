"""Tests for the driven port rules."""

import pytest

from julee.core.doctrine.rules.port import (
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


def test_a_handler_is_accepted_beside_services() -> None:
    """Handlers share domain/services/ and are a different artifact.

    hcd's services package holds eleven handlers and no services at all,
    so a rule that objected to them would fail a kit for obeying ADR 003.
    """
    assert ports_misnamed_for_their_directory([a_port("EpicCreatedHandler")]) == []


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


def test_the_services_objection_names_both_roles_it_admits() -> None:
    objections = ports_misnamed_for_their_directory([a_port("Snoop", "services")])

    assert "*Service" in objections[0]
    assert "*Handler" in objections[0]


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

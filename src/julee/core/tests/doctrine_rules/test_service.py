"""Tests for the service protocol rules."""

import pytest

from julee.core.doctrine.rules.service import (
    contexts_whose_services_doctrine_cannot_see,
    services_not_named_for_their_role,
)
from julee.core.entities.code_info import ClassInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

pytestmark = pytest.mark.unit


def a_service(
    name: str = "PollerService",
    slug: str = "polling",
) -> CodeArtifactWithContext:
    """A protocol in domain/services/, named however the caller says."""
    return CodeArtifactWithContext(
        bounded_context=slug,
        artifact=ClassInfo(name=name, file=f"{name.lower()}.py"),
    )


# =============================================================================
# What a protocol in domain/services/ calls itself
# =============================================================================


def test_a_protocol_named_for_a_service_is_accepted() -> None:
    assert services_not_named_for_their_role([a_service()]) == []


def test_a_handler_sharing_the_directory_is_accepted() -> None:
    """Handlers live here too, and claim their role the same way.

    hcd's domain/services/ holds eleven handlers and no services at all,
    so a rule that objected to them would fail a kit for being what ADR
    003 asks it to be.
    """
    services = [a_service(name="EpicCreatedHandler", slug="hcd")]

    assert services_not_named_for_their_role(services) == []


def test_a_protocol_claiming_neither_role_is_objected_to() -> None:
    """The case this rule was written for.

    polling's NewDataAnalyzer was dropped silently while services were
    found by their suffix. Found by directory instead, it is read, and
    its name is a question rather than a filter.
    """
    objections = services_not_named_for_their_role([a_service(name="NewDataAnalyzer")])

    assert len(objections) == 1
    assert "polling.NewDataAnalyzer" in objections[0]


def test_the_objection_says_what_to_do_about_it() -> None:
    """Two answers, and the message offers both rather than just failing."""
    objections = services_not_named_for_their_role([a_service(name="NewDataAnalyzer")])

    assert "Rename it" in objections[0]
    assert "does not belong here" in objections[0]


def test_a_name_merely_containing_the_word_is_not_enough() -> None:
    """The claim is made by the suffix, as it is for use cases and requests."""
    objections = services_not_named_for_their_role([a_service(name="ServiceRegistry")])

    assert len(objections) == 1


def test_every_offender_is_named_rather_than_just_the_first() -> None:
    services = [
        a_service(name="NewDataAnalyzer"),
        a_service(name="PollerService"),
        a_service(name="Snoop"),
    ]

    assert len(services_not_named_for_their_role(services)) == 2


# =============================================================================
# The canary: doctrine can see what it claims to check
# =============================================================================


def test_a_package_doctrine_reads_protocols_out_of_is_fine() -> None:
    assert contexts_whose_services_doctrine_cannot_see([("polling", 3)]) == []


def test_a_populated_package_yielding_nothing_is_objected_to() -> None:
    """What #175 and #231 both looked like: green, and not looking.

    The caller passes only contexts whose services package has modules in
    it, so a zero here means doctrine read a directory with code in it and
    came away with nothing.
    """
    objections = contexts_whose_services_doctrine_cannot_see([("billing", 0)])

    assert len(objections) == 1
    assert "billing" in objections[0]


def test_one_blind_context_does_not_hide_behind_a_sighted_one() -> None:
    contexts = [("polling", 3), ("billing", 0), ("hcd", 11)]

    objections = contexts_whose_services_doctrine_cannot_see(contexts)

    assert len(objections) == 1
    assert "billing" in objections[0]

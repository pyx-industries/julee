"""Tests for the use case rules.

Each rule gets something that should offend it and something that should
not. The second half matters as much: a rule that fires on everything
passes its own test suite just as happily as one that fires on nothing.
"""

import pytest

from julee.core.doctrine.rules.use_case import (
    use_cases_defining_next_action,
    use_cases_not_named_UseCase,
    use_cases_without_docstring,
    use_cases_without_request,
    use_cases_without_response,
)
from julee.core.entities.code_info import ClassInfo, MethodInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

pytestmark = pytest.mark.unit


def a_use_case(
    name: str = "GetStoryUseCase",
    context: str = "hcd",
    docstring: str = "Get a story.",
    methods: tuple[str, ...] = ("execute",),
) -> CodeArtifactWithContext:
    """A use case that offends none of the rules.

    Built from julee's own types rather than stand-ins, so a change to
    ClassInfo breaks these tests instead of letting them drift.
    """
    return CodeArtifactWithContext(
        bounded_context=context,
        artifact=ClassInfo(
            name=name,
            docstring=docstring,
            methods=[MethodInfo(name=m) for m in methods],
        ),
    )


def a_class(name: str, context: str = "hcd") -> CodeArtifactWithContext:
    """Any other class, for the request and response sets."""
    return CodeArtifactWithContext(
        bounded_context=context, artifact=ClassInfo(name=name)
    )


# =============================================================================
# Naming
# =============================================================================


def test_a_use_case_named_correctly_is_allowed() -> None:
    """The ordinary case."""
    assert use_cases_not_named_UseCase([a_use_case()]) == []


def test_a_use_case_not_ending_in_UseCase_is_reported() -> None:
    """The suffix is how everything else finds them."""
    assert use_cases_not_named_UseCase([a_use_case(name="GetStory")]) != []


def test_the_objection_names_the_context_and_the_class() -> None:
    """Two kits may both have a GetStory."""
    objection = use_cases_not_named_UseCase([a_use_case(name="GetStory")])[0]

    assert objection == "hcd.GetStory"


def test_a_name_merely_containing_UseCase_is_not_enough() -> None:
    """It has to end with it, or the prefix rules cannot work."""
    assert use_cases_not_named_UseCase([a_use_case(name="UseCaseHelper")]) != []


# =============================================================================
# Documentation
# =============================================================================


def test_a_documented_use_case_is_allowed() -> None:
    """The ordinary case."""
    assert use_cases_without_docstring([a_use_case()]) == []


def test_a_use_case_that_says_nothing_is_reported() -> None:
    """A use case is a unit of what the solution is for."""
    assert use_cases_without_docstring([a_use_case(docstring="")]) != []


# =============================================================================
# A request and a response each
# =============================================================================


def test_a_use_case_with_its_request_is_allowed() -> None:
    """The ordinary case."""
    objections = use_cases_without_request([a_use_case()], [a_class("GetStoryRequest")])

    assert objections == []


def test_a_use_case_with_no_request_is_reported() -> None:
    """A use case takes one named object, not a parameter list."""
    objections = use_cases_without_request([a_use_case()], [])

    assert objections == ["hcd.GetStoryUseCase: missing GetStoryRequest"]


def test_a_request_in_another_context_does_not_count() -> None:
    """Two contexts may both have a GetStory, and they are not the same."""
    objections = use_cases_without_request(
        [a_use_case()], [a_class("GetStoryRequest", context="c4")]
    )

    assert objections != []


def test_a_generic_base_class_needs_no_request() -> None:
    """It exists to be subclassed; the subclass brings the request."""
    objections = use_cases_without_request(
        [a_use_case(name="FilterableListUseCase")], []
    )

    assert objections == []


def test_a_badly_named_use_case_is_left_to_the_naming_rule() -> None:
    """One fault, one objection: it should not be reported twice."""
    objections = use_cases_without_request([a_use_case(name="GetStory")], [])

    assert objections == []


def test_a_use_case_with_its_response_is_allowed() -> None:
    """The ordinary case."""
    objections = use_cases_without_response(
        [a_use_case()], [a_class("GetStoryResponse")]
    )

    assert objections == []


def test_a_use_case_with_no_response_is_reported() -> None:
    """A use case returns one named object."""
    objections = use_cases_without_response([a_use_case()], [])

    assert objections == ["hcd.GetStoryUseCase: missing GetStoryResponse"]


def test_a_request_is_not_mistaken_for_a_response() -> None:
    """The two rules look for different suffixes, and must not agree."""
    objections = use_cases_without_response(
        [a_use_case()], [a_class("GetStoryRequest")]
    )

    assert objections != []


# =============================================================================
# The superseded orchestration pattern
# =============================================================================


def test_a_use_case_without_next_action_is_allowed() -> None:
    """The ordinary case."""
    assert use_cases_defining_next_action([a_use_case()]) == []


def test_a_use_case_defining_next_action_is_reported() -> None:
    """ADR 003 superseded it: a use case hands off, it does not decide."""
    offender = a_use_case(methods=("execute", "next_action"))

    assert use_cases_defining_next_action([offender]) == ["hcd.GetStoryUseCase"]


def test_a_method_merely_mentioning_next_action_is_not_it() -> None:
    """Matching on a substring would report the wrong thing."""
    innocent = a_use_case(methods=("execute", "describe_next_action_policy"))

    assert use_cases_defining_next_action([innocent]) == []


# =============================================================================
# Nothing at all
# =============================================================================


@pytest.mark.parametrize(
    "rule",
    [
        lambda: use_cases_not_named_UseCase([]),
        lambda: use_cases_without_docstring([]),
        lambda: use_cases_without_request([], []),
        lambda: use_cases_without_response([], []),
        lambda: use_cases_defining_next_action([]),
    ],
)
def test_a_codebase_with_no_use_cases_offends_nothing(rule) -> None:
    """A kit of pure domain models has none, and that is not a fault."""
    assert rule() == []

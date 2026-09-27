"""Tests for the use case rules.

Each rule gets something that should offend it and something that should
not. The second half matters as much: a rule that fires on everything
passes its own test suite just as happily as one that fires on nothing.
"""

import itertools
import sys
from pathlib import Path

import pytest

from julee.core.doctrine.resolution import Verdict, dto_verdicts
from julee.core.doctrine.rules.use_case import (
    requests_that_are_not_pydantic,
    responses_that_are_not_pydantic,
    use_case_sources_mentioning,
    use_cases_defining_next_action,
    use_cases_not_named_UseCase,
    use_cases_whose_execute_returns_the_wrong_response,
    use_cases_whose_execute_takes_the_wrong_request,
    use_cases_without_docstring,
    use_cases_without_execute,
    use_cases_without_request,
    use_cases_without_response,
)
from julee.core.entities.code_info import ClassInfo, MethodInfo, ParameterInfo
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


# =============================================================================
# Something to run
# =============================================================================


def a_use_case_with(
    bases: tuple[str, ...] = (),
    name: str = "GetStoryUseCase",
    execute: MethodInfo | None = None,
) -> CodeArtifactWithContext:
    """A use case with particular bases and a particular execute."""
    return CodeArtifactWithContext(
        bounded_context="hcd",
        artifact=ClassInfo(
            name=name,
            docstring="Get a story.",
            bases=list(bases),
            methods=[execute] if execute else [],
        ),
    )


def an_execute(
    takes: str = "GetStoryRequest", returns: str = "GetStoryResponse"
) -> MethodInfo:
    """An execute that takes and returns the right things."""
    return MethodInfo(
        name="execute",
        parameters=[
            ParameterInfo(name="self"),
            ParameterInfo(name="request", type_annotation=takes),
        ],
        return_type=returns,
    )


def test_a_use_case_declaring_execute_is_allowed() -> None:
    """The ordinary case."""
    assert use_cases_without_execute([a_use_case_with(execute=an_execute())]) == []


def test_a_use_case_with_no_execute_at_all_is_reported() -> None:
    """A use case nobody can call."""
    assert use_cases_without_execute([a_use_case_with()]) != []


def test_execute_inherited_from_a_visible_base_counts() -> None:
    """A subclass need not restate what its base already does."""
    found = [
        a_use_case_with(name="BaseUseCase", execute=an_execute()),
        a_use_case_with(name="GetStoryUseCase", bases=("BaseUseCase",)),
    ]

    assert use_cases_without_execute(found) == []


def test_a_base_the_codebase_cannot_see_is_trusted() -> None:
    """julee's generic CRUD classes provide execute, and are not scanned."""
    found = [a_use_case_with(bases=("GetUseCase",))]

    assert use_cases_without_execute(found) == []


def test_a_cycle_in_the_bases_does_not_hang() -> None:
    """The parser reads text, so it can record something Python could not."""
    found = [
        a_use_case_with(name="A", bases=("B",)),
        a_use_case_with(name="B", bases=("A",)),
    ]

    assert len(use_cases_without_execute(found)) == 2


# =============================================================================
# execute takes and returns its own request and response
# =============================================================================


def test_an_execute_taking_its_own_request_is_allowed() -> None:
    """The ordinary case."""
    found = [a_use_case_with(execute=an_execute())]

    assert use_cases_whose_execute_takes_the_wrong_request(found) == []


def test_an_execute_taking_somebody_else_s_request_is_reported() -> None:
    """Having a matching Request nearby is not the same as accepting it."""
    found = [a_use_case_with(execute=an_execute(takes="ListStoriesRequest"))]

    objections = use_cases_whose_execute_takes_the_wrong_request(found)

    assert len(objections) == 1
    assert "GetStoryRequest" in objections[0]


def test_an_execute_taking_nothing_is_reported() -> None:
    """A use case takes one named object; none is not one."""
    execute = MethodInfo(name="execute", parameters=[ParameterInfo(name="self")])

    objections = use_cases_whose_execute_takes_the_wrong_request(
        [a_use_case_with(execute=execute)]
    )

    assert "no request parameter" in objections[0]


def test_a_dotted_annotation_is_matched_on_its_last_part() -> None:
    """models.GetStoryRequest is the same class as GetStoryRequest."""
    found = [a_use_case_with(execute=an_execute(takes="requests.GetStoryRequest"))]

    assert use_cases_whose_execute_takes_the_wrong_request(found) == []


def test_a_quoted_annotation_is_matched_without_its_quotes() -> None:
    """A forward reference is a string, and names the same class."""
    found = [a_use_case_with(execute=an_execute(takes='"GetStoryRequest"'))]

    assert use_cases_whose_execute_takes_the_wrong_request(found) == []


def test_an_execute_returning_its_own_response_is_allowed() -> None:
    """The ordinary case."""
    found = [a_use_case_with(execute=an_execute())]

    assert use_cases_whose_execute_returns_the_wrong_response(found) == []


def test_an_execute_returning_the_wrong_response_is_reported() -> None:
    """The response has to be wired in, not merely present in the module."""
    found = [a_use_case_with(execute=an_execute(returns="ListStoriesResponse"))]

    assert use_cases_whose_execute_returns_the_wrong_response(found) != []


def test_an_execute_declaring_no_return_type_is_reported() -> None:
    """Silence about what comes back is the thing Response exists to stop."""
    found = [a_use_case_with(execute=an_execute(returns=""))]

    objections = use_cases_whose_execute_returns_the_wrong_response(found)

    assert "declares no return type" in objections[0]


def test_a_generic_base_is_exempt_from_both() -> None:
    """It exists to be subclassed; the subclass brings the pair."""
    found = [
        a_use_case_with(name="FilterableListUseCase", execute=an_execute(takes="Any"))
    ]

    assert use_cases_whose_execute_takes_the_wrong_request(found) == []
    assert use_cases_whose_execute_returns_the_wrong_response(found) == []


# =============================================================================
# What a use case file may not say
# =============================================================================


def test_a_file_saying_nothing_forbidden_is_allowed() -> None:
    """The ordinary case."""
    sources = [("hcd", "get_story.py", "from julee.core import x\n")]

    assert use_case_sources_mentioning(sources, "temporalio") == []


def test_a_file_importing_the_forbidden_thing_is_reported() -> None:
    """Temporal coupling belongs in infrastructure, not in a use case."""
    sources = [("hcd", "get_story.py", "import temporalio\n")]

    assert use_case_sources_mentioning(sources, "temporalio") == ["hcd/get_story.py"]


def test_only_the_offending_file_is_named() -> None:
    """So that fixing it does not mean reading every file in the context."""
    sources = [
        ("hcd", "clean.py", "x = 1\n"),
        ("hcd", "dirty.py", "datetime.now()\n"),
    ]

    objections = use_case_sources_mentioning(sources, "datetime.now")

    assert objections == ["hcd/dirty.py"]


# =============================================================================
# Requests and responses are pydantic DTOs
#
# The rules format verdicts; the verdicts come from importing the class.
# Both halves are tested, the second against packages written to disk,
# because every way this leaked before was a way the AST read as fine.
# =============================================================================


def a_verdict(
    name: str = "GetStoryRequest",
    context: str = "hcd",
    reason: str | None = None,
) -> Verdict:
    """One resolved DTO name."""
    return Verdict(bounded_context=context, name=name, reason=reason)


def test_a_request_that_resolved_to_a_pydantic_model_is_allowed() -> None:
    """The ordinary case."""
    assert requests_that_are_not_pydantic([a_verdict()]) == []


def test_a_request_with_a_reason_is_reported() -> None:
    """A verdict carrying a reason is a violation."""
    assert requests_that_are_not_pydantic([a_verdict(reason="it is a str")]) == [
        "hcd.GetStoryRequest: a request is a pydantic DTO, but it is a str"
    ]


def test_a_response_with_a_reason_is_reported() -> None:
    """The other half, worded for a response."""
    assert responses_that_are_not_pydantic(
        [a_verdict(name="GetStoryResponse", reason="it is a str")]
    ) == ["hcd.GetStoryResponse: a response is a pydantic DTO, but it is a str"]


def test_the_dto_objection_names_the_context() -> None:
    """Two kits may both have a GetStoryRequest."""
    objection = requests_that_are_not_pydantic([a_verdict(reason="x")])[0]

    assert objection.startswith("hcd.GetStoryRequest:")


# =============================================================================
# The resolver, against packages written to disk
# =============================================================================

_UNIQUE = itertools.count()

PYDANTIC_REQUEST = (
    '"""Get a story."""\n\n'
    "from pydantic import BaseModel\n\n\n"
    "class GetStoryRequest(BaseModel):\n"
    '    """Which story."""\n\n'
    "    slug: str\n"
)


def a_context(tmp_path: Path, usecase_source: str, messages: str = "") -> Path:
    """Write an importable bounded context and put its root on sys.path."""
    root = tmp_path / f"root{next(_UNIQUE)}"
    context = root / "acme" / "stories"
    (context / "usecases").mkdir(parents=True)
    (root / "acme" / "__init__.py").write_text("")
    (context / "__init__.py").write_text('"""Stories."""\n')
    (context / "usecases" / "__init__.py").write_text("")
    (context / "usecases" / "get_story.py").write_text(usecase_source)
    if messages:
        (context / "messages.py").write_text(messages)
    sys.path.insert(0, str(root))
    return context


def reason_for(context: Path, name: str) -> str | None:
    """The verdict's reason for one name."""
    verdicts = dto_verdicts("stories", context, [name])
    return next(v.reason for v in verdicts if v.name == name)


def test_a_pydantic_model_resolves_clean(tmp_path: Path) -> None:
    """The ordinary case, end to end."""
    assert reason_for(a_context(tmp_path, PYDANTIC_REQUEST), "GetStoryRequest") is None


def test_a_local_class_named_BaseModel_does_not_satisfy_it(tmp_path: Path) -> None:
    """Reading bases out of the AST passed this."""
    context = a_context(
        tmp_path,
        '"""Get a story."""\n\n\n'
        "class BaseModel:\n"
        '    """Not pydantic\'s."""\n\n\n'
        "class GetStoryRequest(BaseModel):\n"
        '    """Which story."""\n',
    )

    assert reason_for(context, "GetStoryRequest") is not None


def test_a_base_from_an_unparsed_package_does_not_satisfy_it(tmp_path: Path) -> None:
    """An unseen base used to be trusted."""
    context = a_context(
        tmp_path,
        '"""Get a story."""\n\n'
        "from argparse import Namespace\n\n\n"
        "class GetStoryRequest(Namespace):\n"
        '    """Which story."""\n',
    )

    assert reason_for(context, "GetStoryRequest") is not None


def test_a_dto_defined_outside_usecases_is_still_checked(tmp_path: Path) -> None:
    """Moving it out and importing it back used to bypass the rule."""
    context = a_context(
        tmp_path,
        '"""Get a story."""\n\n'
        "from acme.stories.messages import GetStoryRequest\n\n"
        '__all__ = ["GetStoryRequest"]\n',
        messages='"""Messages."""\n\n\nclass GetStoryRequest:\n    """Not pydantic."""\n',
    )

    assert reason_for(context, "GetStoryRequest") is not None


def test_a_pydantic_dataclass_is_allowed(tmp_path: Path) -> None:
    """It validates, so it is a DTO. This used to be a false objection."""
    context = a_context(
        tmp_path,
        '"""Get a story."""\n\n'
        "from pydantic.dataclasses import dataclass\n\n\n"
        "@dataclass(frozen=True)\n"
        "class GetStoryRequest:\n"
        '    """Which story."""\n\n'
        "    slug: str\n",
    )

    assert reason_for(context, "GetStoryRequest") is None


def test_a_stdlib_dataclass_is_reported(tmp_path: Path) -> None:
    """It does not validate, so it is not a DTO."""
    context = a_context(
        tmp_path,
        '"""Get a story."""\n\n'
        "from dataclasses import dataclass\n\n\n"
        "@dataclass(frozen=True)\n"
        "class GetStoryRequest:\n"
        '    """Which story."""\n\n'
        "    slug: str\n",
    )

    assert reason_for(context, "GetStoryRequest") is not None


def test_an_aliased_pydantic_import_is_allowed(tmp_path: Path) -> None:
    """How it was spelled is not what it is."""
    context = a_context(
        tmp_path,
        '"""Get a story."""\n\n'
        "from pydantic import BaseModel as BM\n\n\n"
        "class GetStoryRequest(BM):\n"
        '    """Which story."""\n\n'
        "    slug: str\n",
    )

    assert reason_for(context, "GetStoryRequest") is None


def test_a_file_that_does_not_parse_is_reported(tmp_path: Path) -> None:
    """It contributes no classes, so every other rule passes over it."""
    context = a_context(tmp_path, '"""Broken."""\n\nclass R:\n    x: int =\n')

    assert [v.reason for v in dto_verdicts("stories", context, [])] != []


def test_a_name_that_resolves_to_nothing_is_reported(tmp_path: Path) -> None:
    """Doctrine saw it and could not reach it. That is not compliance."""
    context = a_context(tmp_path, PYDANTIC_REQUEST)

    assert reason_for(context, "VanishedRequest") is not None


def test_a_context_with_no_usecases_directory_yields_nothing(tmp_path: Path) -> None:
    """Nothing to import is not a failure."""
    assert dto_verdicts("stories", tmp_path / "nowhere", []) == []

"""Tests for the use case rules.

Each rule gets something that should offend it and something that should
not. The second half matters as much: a rule that fires on everything
passes its own test suite just as happily as one that fires on nothing.
"""

import pytest

from julee.core.doctrine.rules.use_case import (
    requests_not_extending_BaseModel,
    responses_not_extending_BaseModel,
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
# julee declares bounded_contexts = "none", so the doctrine test over the
# estate has no subject here and skips. These are the only evidence the
# rules work, which is the whole reason they are this thorough.
# =============================================================================


def a_dto(
    name: str = "GetStoryRequest",
    context: str = "hcd",
    bases: tuple[str, ...] = ("BaseModel",),
    file: str = "usecases/get_story.py",
    decorators: tuple[str, ...] = (),
) -> CodeArtifactWithContext:
    """A request or response class, compliant unless told otherwise.

    ``file`` is set because the parser sets it on every class it reads,
    and its absence means something specific the rules act on.
    """
    return CodeArtifactWithContext(
        bounded_context=context,
        artifact=ClassInfo(
            name=name,
            bases=list(bases),
            file=file,
            decorators=list(decorators),
        ),
    )


def test_a_request_deriving_from_BaseModel_is_allowed() -> None:
    """The ordinary case."""
    assert requests_not_extending_BaseModel([a_dto()]) == []


def test_a_request_with_no_base_class_is_reported() -> None:
    """A bare class validates nothing."""
    assert requests_not_extending_BaseModel([a_dto(bases=())]) != []


def test_a_request_that_is_a_dataclass_is_reported() -> None:
    """A frozen dataclass is the right answer in the domain, not here.

    This is the one worth being explicit about while the migration is
    on: a dataclass everywhere is the direction of travel, and the
    driving port is the exception it must not swallow.
    """
    objections = requests_not_extending_BaseModel(
        [a_dto(bases=(), decorators=("dataclasses.dataclass",))]
    )

    assert objections == [
        "hcd.GetStoryRequest: a request is a pydantic DTO, but it is a dataclass"
    ]


def test_a_dataclass_request_is_reported_even_with_a_base() -> None:
    """The decorator decides the shape whatever the class inherits."""
    assert (
        requests_not_extending_BaseModel(
            [a_dto(bases=("Mixin",), decorators=("dataclasses.dataclass",))]
        )
        != []
    )


def test_a_TypedDict_request_is_reported() -> None:
    """A base doctrine does not need to see to rule out.

    Trusting every unseen base is what the other inheritance rules do,
    and it would have let this through.
    """
    assert requests_not_extending_BaseModel([a_dto(bases=("TypedDict",))]) != []


@pytest.mark.parametrize("base", ["NamedTuple", "Protocol", "object", "Enum"])
def test_the_other_settled_bases_are_reported(base: str) -> None:
    """Each for the same reason: none of them is a BaseModel."""
    assert requests_not_extending_BaseModel([a_dto(bases=(base,))]) != []


def test_a_request_extending_another_request_is_allowed() -> None:
    """Compliance is followed through bases within the context."""
    assert (
        requests_not_extending_BaseModel(
            [
                a_dto(name="ListStoriesRequest", bases=("PagedRequest",)),
                a_dto(name="PagedRequest", bases=("BaseModel",)),
            ]
        )
        == []
    )


def test_a_chain_of_requests_reaching_nothing_is_reported() -> None:
    """Following bases has to be able to end in a failure, not just a stop."""
    objections = requests_not_extending_BaseModel(
        [
            a_dto(name="ListStoriesRequest", bases=("PagedRequest",)),
            a_dto(name="PagedRequest", bases=()),
        ]
    )

    assert len(objections) == 2


def test_a_cycle_in_the_dto_bases_does_not_hang() -> None:
    """Two classes naming each other is not a real hierarchy, but it parses."""
    assert (
        requests_not_extending_BaseModel(
            [
                a_dto(name="ARequest", bases=("BRequest",)),
                a_dto(name="BRequest", bases=("ARequest",)),
            ]
        )
        != []
    )


def test_a_base_from_outside_the_context_is_trusted() -> None:
    """The same trust every inheritance rule here extends.

    julee's own ListCodeArtifactsRequest is a BaseModel, and a kit
    deriving from it cannot show doctrine that.
    """
    assert (
        requests_not_extending_BaseModel([a_dto(bases=("ListCodeArtifactsRequest",))])
        == []
    )


def test_a_qualified_pydantic_BaseModel_is_read() -> None:
    """``pydantic.BaseModel`` and ``BaseModel`` are the same class."""
    assert (
        requests_not_extending_BaseModel([a_dto(bases=("pydantic.BaseModel",))]) == []
    )


def test_a_subscripted_base_is_read() -> None:
    """``BaseRequest[Story]`` names BaseRequest."""
    assert (
        requests_not_extending_BaseModel(
            [
                a_dto(name="GetStoryRequest", bases=("BaseRequest[Story]",)),
                a_dto(name="BaseRequest", bases=("BaseModel",)),
            ]
        )
        == []
    )


def test_a_name_doctrine_only_saw_imported_is_not_reported() -> None:
    """The parser records a re-exported DTO as a name and nothing else.

    It has no bases because none were read. Reporting it would be
    objecting to what doctrine failed to look at, which is a false
    objection — it tells an author their correct work is wrong.
    """
    assert requests_not_extending_BaseModel([a_dto(bases=(), file="")]) == []


def test_a_name_only_base_does_not_condemn_what_derives_from_it() -> None:
    """The same blind spot, reached through a base rather than directly."""
    assert (
        requests_not_extending_BaseModel(
            [
                a_dto(name="GetStoryRequest", bases=("GeneratedRequest",)),
                a_dto(name="GeneratedRequest", bases=(), file=""),
            ]
        )
        == []
    )


def test_a_dto_objection_names_the_context_and_the_class() -> None:
    """Two kits may both have a GetStoryRequest."""
    objection = requests_not_extending_BaseModel([a_dto(bases=())])[0]

    assert objection.startswith("hcd.GetStoryRequest:")


def test_the_objection_says_which_bases_it_followed() -> None:
    """So an author can see what doctrine read, not just that it refused."""
    objection = requests_not_extending_BaseModel(
        [
            a_dto(name="GetStoryRequest", bases=("PagedRequest",)),
            a_dto(name="PagedRequest", bases=()),
        ]
    )[0]

    assert "PagedRequest" in objection


def test_a_response_deriving_from_BaseModel_is_allowed() -> None:
    """The ordinary case, on the other half."""
    assert responses_not_extending_BaseModel([a_dto(name="GetStoryResponse")]) == []


def test_a_response_with_no_base_class_is_reported() -> None:
    """An adapter has to serialise it."""
    objections = responses_not_extending_BaseModel(
        [a_dto(name="GetStoryResponse", bases=())]
    )

    assert objections == [
        "hcd.GetStoryResponse: a response is a pydantic DTO, but it has no base class"
    ]


def test_each_rule_resolves_only_within_its_own_half() -> None:
    """Where the trust boundary sits, asserted rather than assumed.

    Each rule is handed only its own half of the DTOs, so a base that
    is a response is a base this rule cannot see, and unseen means
    trusted. Pinning it here because it is a limit rather than a
    property: widening the pool later should break this test and make
    someone decide, instead of silently changing what the rule checks.
    """
    assert (
        requests_not_extending_BaseModel(
            [a_dto(name="GetStoryRequest", bases=("GetStoryResponse",))]
        )
        == []
    )

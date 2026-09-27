"""What the use case rules object to.

Each function takes the code artifacts a codebase has and returns its
objections, as sentences someone can act on. Nothing here reads a file
or imports a module: what a class is called, whether it has a docstring
and what methods it declares all come from ClassInfo, which the AST
parser already fills in.

All ten are here now. The ones that used to import a class and inspect
its signature read what the parser already recorded instead: MethodInfo
carries parameters, their annotations and the return type. The two that
look for an import or a call are given the file's text, since neither is
a member and so neither appears in ClassInfo.
"""

from collections.abc import Iterable

from julee.core.doctrine_constants import (
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
    USE_CASE_SUFFIX,
)
from julee.core.entities.code_info import ClassInfo, MethodInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

__all__ = [
    "GENERIC_BASE_CLASSES",
    "NOT_PYDANTIC_BASES",
    "PYDANTIC_BASE",
    "requests_not_extending_BaseModel",
    "responses_not_extending_BaseModel",
    "use_case_sources_mentioning",
    "use_cases_whose_execute_returns_the_wrong_response",
    "use_cases_whose_execute_takes_the_wrong_request",
    "use_cases_without_execute",
    "use_cases_defining_next_action",
    "use_cases_not_named_UseCase",
    "use_cases_without_docstring",
    "use_cases_without_request",
    "use_cases_without_response",
]

GENERIC_BASE_CLASSES = {
    "FilterableListUseCase",
}
"""Bases that exist to be subclassed, so have no request or response."""


def _named(found: CodeArtifactWithContext) -> str:
    """How to name one in an objection."""
    return f"{found.bounded_context}.{found.artifact.name}"


def use_cases_not_named_UseCase(
    use_cases: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases whose name does not end in UseCase.

    The suffix is how everything else finds them: doctrine, the CRUD
    generator, and anyone reading the directory.

    Args:
        use_cases: The use case classes a codebase has

    Returns:
        One name per offender
    """
    return [
        _named(found)
        for found in use_cases
        if not found.artifact.name.endswith(USE_CASE_SUFFIX)
    ]


def use_cases_without_docstring(
    use_cases: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases that do not say what they do.

    A use case is a unit of what the solution is for. One that does not
    explain itself leaves the next reader to infer it from the code.

    Args:
        use_cases: The use case classes a codebase has

    Returns:
        One name per offender
    """
    return [_named(found) for found in use_cases if not found.artifact.docstring]


def _missing_counterpart(
    use_cases: Iterable[CodeArtifactWithContext],
    counterparts: Iterable[CodeArtifactWithContext],
    suffix: str,
) -> list[str]:
    """Use cases with no matching class of the given suffix."""
    available: dict[str, set[str]] = {}
    for found in counterparts:
        available.setdefault(found.bounded_context, set()).add(found.artifact.name)

    objections = []
    for found in use_cases:
        name = found.artifact.name
        if name in GENERIC_BASE_CLASSES or not name.endswith(USE_CASE_SUFFIX):
            continue
        expected = f"{name[: -len(USE_CASE_SUFFIX)]}{suffix}"
        if expected not in available.get(found.bounded_context, set()):
            objections.append(f"{_named(found)}: missing {expected}")
    return objections


def use_cases_without_request(
    use_cases: Iterable[CodeArtifactWithContext],
    requests: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases with no matching Request class.

    A use case takes one object and returns one object, so that what it
    needs and what it produces are named rather than implied by a
    parameter list.

    Args:
        use_cases: The use case classes a codebase has
        requests: The request classes a codebase has

    Returns:
        One sentence per use case with nothing to take
    """
    return _missing_counterpart(use_cases, requests, REQUEST_SUFFIX)


def use_cases_without_response(
    use_cases: Iterable[CodeArtifactWithContext],
    responses: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases with no matching Response class.

    Args:
        use_cases: The use case classes a codebase has
        responses: The response classes a codebase has

    Returns:
        One sentence per use case with nothing to return
    """
    return _missing_counterpart(use_cases, responses, RESPONSE_SUFFIX)


def use_cases_defining_next_action(
    use_cases: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases that decide what happens after them.

    next_action() is the orchestration pattern ADR 003 superseded. A use
    case hands a domain condition to an injected handler; deciding the
    next step itself makes it know about a workflow it is only part of.

    Args:
        use_cases: The use case classes a codebase has

    Returns:
        One name per offender
    """
    return [
        _named(found)
        for found in use_cases
        if any(method.name == "next_action" for method in found.artifact.methods)
    ]


def _execute_of(artifact: CodeArtifactWithContext) -> "MethodInfo | None":
    """The execute method a class declares itself, if it declares one."""
    return next(
        (method for method in artifact.artifact.methods if method.name == "execute"),
        None,
    )


def use_cases_without_execute(
    use_cases: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases with no way to run them.

    execute() is the one entry point: it takes a Request and returns a
    Response. A use case without one cannot be called.

    Inheritance counts, and is worked out from the bases the codebase can
    see. A base it cannot see — one of julee's generic CRUD classes, say
    — is trusted to provide execute, the same way an entity extending an
    unseen base is trusted to be frozen.

    Args:
        use_cases: The use case classes a codebase has

    Returns:
        One name per use case that cannot be run
    """
    use_cases = list(use_cases)
    by_name = {found.artifact.name: found for found in use_cases}

    def has_execute(name: str, visiting: frozenset[str]) -> bool:
        found = by_name.get(name)
        if found is None:
            return True
        if _execute_of(found) is not None:
            return True
        if name in visiting:
            return False
        return any(
            has_execute(base, visiting | {name}) for base in found.artifact.bases
        )

    return [
        _named(found)
        for found in use_cases
        if not has_execute(found.artifact.name, frozenset())
    ]


def _counterpart_of(name: str, suffix: str) -> str:
    """What a use case's request or response should be called."""
    return f"{name[: -len(USE_CASE_SUFFIX)]}{suffix}"


def use_cases_whose_execute_takes_the_wrong_request(
    use_cases: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases whose execute() does not take their own Request.

    Having a matching Request class nearby is not the same as execute()
    accepting it. This is the rule that notices the two drifting apart.

    A use case that declares no execute() of its own is left to
    use_cases_without_execute, and a generic base is skipped entirely.

    Args:
        use_cases: The use case classes a codebase has

    Returns:
        One sentence per use case taking the wrong thing
    """
    objections = []
    for found in use_cases:
        name = found.artifact.name
        if name in GENERIC_BASE_CLASSES or not name.endswith(USE_CASE_SUFFIX):
            continue
        execute = _execute_of(found)
        if execute is None:
            continue

        expected = _counterpart_of(name, REQUEST_SUFFIX)
        taken = [p for p in execute.parameters if p.name != "self"]
        if not taken:
            objections.append(f"{_named(found)}: execute() has no request parameter")
            continue
        actual = taken[0].type_annotation.strip("\"'").rsplit(".", 1)[-1]
        if actual != expected:
            objections.append(
                f"{_named(found)}: execute() first parameter is {actual!r}, "
                f"expected {expected!r}"
            )
    return objections


def use_cases_whose_execute_returns_the_wrong_response(
    use_cases: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Use cases whose execute() does not return their own Response.

    Args:
        use_cases: The use case classes a codebase has

    Returns:
        One sentence per use case returning the wrong thing
    """
    objections = []
    for found in use_cases:
        name = found.artifact.name
        if name in GENERIC_BASE_CLASSES or not name.endswith(USE_CASE_SUFFIX):
            continue
        execute = _execute_of(found)
        if execute is None:
            continue

        expected = _counterpart_of(name, RESPONSE_SUFFIX)
        actual = execute.return_type.strip("\"'").rsplit(".", 1)[-1]
        if not actual:
            objections.append(f"{_named(found)}: execute() declares no return type")
        elif actual != expected:
            objections.append(
                f"{_named(found)}: execute() returns {actual!r}, expected {expected!r}"
            )
    return objections


def use_case_sources_mentioning(
    sources: Iterable[tuple[str, str, str]], forbidden: str
) -> list[str]:
    """Use case files containing something they should not.

    Reading the text rather than the parsed class, because what is being
    looked for is an import or a call rather than a member: neither
    appears in ClassInfo.

    Args:
        sources: Bounded context slug, file path and contents
        forbidden: The text that should not appear

    Returns:
        One sentence per file containing it
    """
    return [f"{slug}/{path}" for slug, path, text in sources if forbidden in text]


PYDANTIC_BASE = "BaseModel"
"""What a request or a response must reach through its bases."""

NOT_PYDANTIC_BASES = frozenset(
    {
        "ABC",
        "Enum",
        "IntEnum",
        "NamedTuple",
        "object",
        "Protocol",
        "StrEnum",
        "TypedDict",
    }
)
"""Bases that settle the question the other way.

A base doctrine cannot see is trusted, which is how every inheritance
rule here works. These are the ones it does not need to see to know:
none of them is a ``BaseModel``, and a request deriving from one is a
message the driving port cannot validate, whatever else it inherits.

Without this set they would all have been trusted — a ``TypedDict``
request would have satisfied a rule written to forbid exactly that.
"""


def _base_name(base: str) -> str:
    """The class a base expression names.

    Bases are recorded as they were written, so the same class arrives
    as ``BaseModel``, ``pydantic.BaseModel`` or ``BaseRequest[Story]``
    depending on the author. The module path and the subscript are how
    it was spelled; the last segment is what it is.

    Args:
        base: A base as the parser recorded it

    Returns:
        The bare class name
    """
    return base.split("[", 1)[0].strip().rsplit(".", 1)[-1]


def _is_a_name_doctrine_only_saw_imported(artifact: ClassInfo) -> bool:
    """Whether the parser recorded a name rather than a class.

    A request re-exported into ``usecases/`` from somewhere the parser
    does not read — ``_generated/`` is the case it was built for —
    reaches the rules as a ClassInfo holding a name and nothing else.
    It has no bases because none were read, not because it has none,
    and reporting it would be objecting to what doctrine failed to
    look at rather than to anything an author wrote.

    ``file`` is the discriminator: the parser sets it on every class it
    actually read, and leaves it empty on these.
    """
    return not artifact.file


def _why_it_is_not_pydantic(
    artifact: ClassInfo, by_name: dict[str, ClassInfo]
) -> str | None:
    """What to tell an author about a DTO that does not reach BaseModel.

    Returns None when it does reach it. Otherwise a clause naming the
    reason, because the four ways to fail this want four different
    edits and an objection that does not say which leaves the author to
    diff their class against a rule they cannot read.

    Args:
        artifact: The request or response class to judge
        by_name: The DTOs of its bounded context, for following bases

    Returns:
        A clause, or None if the class complies
    """

    def reaches_BaseModel(name: str, visiting: frozenset[str]) -> bool:
        if name == PYDANTIC_BASE:
            return True
        if name in NOT_PYDANTIC_BASES or name in visiting:
            return False
        found = by_name.get(name)
        if found is None or _is_a_name_doctrine_only_saw_imported(found):
            return True
        if found.decorated_with("dataclass"):
            return False
        return any(
            reaches_BaseModel(_base_name(base), visiting | {name})
            for base in found.bases
        )

    if artifact.decorated_with("dataclass"):
        return "it is a dataclass"
    if not artifact.bases:
        return "it has no base class"

    named = [_base_name(base) for base in artifact.bases]
    settled = sorted(set(named) & NOT_PYDANTIC_BASES)
    if settled:
        return f"it derives from {', '.join(settled)}"

    if any(reaches_BaseModel(name, frozenset({artifact.name})) for name in named):
        return None
    return f"nothing in its bases reaches it ({', '.join(named)})"


def _dtos_not_extending_BaseModel(
    dtos: Iterable[CodeArtifactWithContext], what: str
) -> list[str]:
    """The shared half of the request and response rules."""
    dtos = list(dtos)
    by_name = {found.artifact.name: found.artifact for found in dtos}

    objections = []
    for found in dtos:
        artifact = found.artifact
        if _is_a_name_doctrine_only_saw_imported(artifact):
            continue
        reason = _why_it_is_not_pydantic(artifact, by_name)
        if reason is not None:
            objections.append(
                f"{_named(found)}: a {what} is a pydantic DTO, but {reason}"
            )
    return objections


def requests_not_extending_BaseModel(
    requests: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Requests that are not pydantic DTOs.

    A request is the message a driving adapter hands in, so it arrives
    from outside as JSON, form fields or a queue payload and has to be
    validated before anything reads it. ``BaseModel`` is what does the
    validating, and a request that does not derive from it is a shape
    nothing checked.

    This is the driving half of the rule that pydantic belongs at the
    edges. It says nothing about what a use case does with the request
    once it has one, and nothing about the domain behind it; both are
    rules of their own.

    Compliance is followed through bases, so a request extending another
    request in the same bounded context is fine. A base doctrine cannot
    see is trusted, the way every inheritance rule here trusts one —
    except for the handful in :data:`NOT_PYDANTIC_BASES`, which need no
    looking at.

    Args:
        requests: The request classes a codebase has

    Returns:
        One sentence per request that nothing validates
    """
    return _dtos_not_extending_BaseModel(requests, "request")


def responses_not_extending_BaseModel(
    responses: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Responses that are not pydantic DTOs.

    The mirror of :func:`requests_not_extending_BaseModel`, and the
    reason it is a separate rule rather than the same one run twice is
    that the two fail for opposite reasons. A request is unvalidated
    input; a response is output a driving adapter has to serialise, and
    one that is not a ``BaseModel`` leaves every adapter to work out how
    on its own.

    Args:
        responses: The response classes a codebase has

    Returns:
        One sentence per response an adapter cannot serialise
    """
    return _dtos_not_extending_BaseModel(responses, "response")

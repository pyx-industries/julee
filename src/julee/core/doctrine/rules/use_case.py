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
from julee.core.entities.code_info import MethodInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

__all__ = [
    "GENERIC_BASE_CLASSES",
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
                f"{_named(found)}: execute() returns {actual!r}, "
                f"expected {expected!r}"
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

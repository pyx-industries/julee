"""What the use case rules object to.

Each function takes the code artifacts a codebase has and returns its
objections, as sentences someone can act on. Nothing here reads a file
or imports a module: what a class is called, whether it has a docstring
and what methods it declares all come from ClassInfo, which the AST
parser already fills in.

Four of the ten use case rules are not here yet. They inspect execute()'s
signature at runtime, or read a file's source, because ClassInfo does not
carry enough to answer them. That is a gap in the parser rather than a
reason for a rule to import things (see #206).
"""

from collections.abc import Iterable

from julee.core.doctrine_constants import (
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
    USE_CASE_SUFFIX,
)
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

__all__ = [
    "GENERIC_BASE_CLASSES",
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

"""Objections about messages: what dtos/ holds, and what a message is called."""

from collections.abc import Iterable

from julee.core.doctrine.resolution import Verdict
from julee.core.parsers.declarations import CLASS
from julee.core.values.census import ContextCensus


def classes_in_dtos_that_are_not_messages(verdicts: Iterable[Verdict]) -> list[str]:
    """Classes in dtos/ that are neither a pydantic model nor an enum.

    dtos/ is the one place in a bounded context where pydantic lives
    (ADR 001), and every class there is found by the directory (ADR 022).
    The verdicts come from
    :func:`julee.core.doctrine.resolution.message_verdicts`, which
    imports each class rather than reading its bases.

    Args:
        verdicts: One per class declared in dtos/, from message_verdicts

    Returns:
        One sentence per class that does not belong there
    """
    return [
        f"{verdict.bounded_context}.{verdict.name}: a class in dtos/ is a "
        f"pydantic model, or an enum one of them uses, but {verdict.reason}"
        for verdict in verdicts
        if verdict.reason is not None
    ]


def ambiguous_message_names(contexts: Iterable[ContextCensus]) -> list[str]:
    """Name each message whose context holds more than one declaration.

    Doctrine matches messages to use cases by name within a bounded
    context. Several imports of one declaration are fine; several class
    declarations of that name are not distinguishable by those rules.
    External names, with no declaration in the context, are left to the
    existing resolution rules.

    Args:
        contexts: Declarations joined to the parser's families

    Returns:
        One objection per ambiguous message, including its source locations
    """
    violations = []
    for context in sorted(contexts, key=lambda found: found.path):
        message_names = {
            member.name
            for member in context.name_only
            if member.family in {"requests", "responses"}
        }
        message_names.update(
            membership.declaration.name
            for membership in context.memberships
            if {"requests", "responses"}.intersection(membership.families)
        )
        for name in sorted(message_names):
            declarations = [
                membership.declaration
                for membership in context.memberships
                if membership.declaration.kind == CLASS
                and membership.declaration.name == name
            ]
            if len(declarations) > 1:
                locations = ", ".join(
                    f"{found.file}:{found.line}"
                    for found in sorted(
                        declarations, key=lambda found: (found.file, found.line)
                    )
                )
                violations.append(
                    f"{context.slug}.{name} has multiple declarations: {locations}. "
                    "Request and response names MUST identify one declaration "
                    "within their bounded context."
                )
    return violations

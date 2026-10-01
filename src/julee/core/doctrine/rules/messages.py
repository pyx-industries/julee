"""Objections to request and response names with several declarations."""

from collections.abc import Iterable

from julee.core.parsers.declarations import CLASS
from julee.core.values.census import ContextCensus


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

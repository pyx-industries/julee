"""What `julee doctrine census` says, and how it exits.

The census is taken in :mod:`julee.core`. This turns one into text for
a person and JSON for a program, and decides the exit status. Nothing
here reads a file, so every line of the report can be tested against a
census written out by hand.

Both forms are ordered by path and line and carry no absolute path and
no time, so two runs over the same source give the same bytes.
"""

import json
import textwrap
from collections import Counter
from typing import Any

from julee.core.parsers.declarations import BINDING, CLASS, FUNCTION
from julee.core.values.census import (
    CANDIDATE,
    CLAIMED_AT_ITS_LOCATION,
    CLAIMED_BY_NAME,
    RESOLVED,
    UNCLAIMED,
    Census,
    ContextCensus,
    Declaration,
)

__all__ = ["STATEMENT", "as_json", "as_text", "exit_status"]

STATEMENT = (
    "This census reports which parser family holds each module-level "
    "declaration. It does not report which doctrine rules check a "
    "declaration. Unclaimed means in no family, not unchecked. Claimed "
    "means a member of a family, not compliant."
)
"""What the census is, said in both forms of the report.

The risk it guards against is being read as a list of what doctrine
checks. Family membership decides which declarations the rules that
take a family see; other rules read source another way.
"""

KINDS = (CLASS, FUNCTION, BINDING)
STATES = (CLAIMED_AT_ITS_LOCATION, CLAIMED_BY_NAME, CANDIDATE, UNCLAIMED)


def exit_status(census: Census) -> int:
    """How the command exits for a census that could be taken.

    0 when every file in scope was read and the two readers agree. An
    unclaimed declaration and an unresolved name are results, not
    failures: each is a fact about the source, and whether it is a
    fault is a rule's question. 1 when a file in scope could not be
    read or the readers disagree, because then the report is not one to
    rely on.

    Args:
        census: The census taken

    Returns:
        0 or 1
    """
    return 0 if census.is_complete and census.readers_agree else 1


def as_text(census: Census) -> str:
    """The census as a report for a person.

    Args:
        census: The census taken

    Returns:
        The report, ending in a newline
    """
    lines = [
        f"census: search_root {census.search_root}",
        "",
        textwrap.fill(STATEMENT, width=76),
        "",
    ]
    lines.append(
        f"Scope: {_count(census.files_read, 'file')} read, "
        f"{_count(census.test_files_excluded, 'test file')} excluded."
    )
    lines.extend(
        f"Excluded: {exclusion.path} ({exclusion.reason})"
        for exclusion in census.exclusions
    )
    lines.extend(
        f"Unreadable: {found.file}: {found.problem}" for found in census.unreadable
    )
    if not census.is_complete:
        lines.append(
            f"The census is incomplete: "
            f"{_count(len(census.unreadable), 'file')} in scope could not be read."
        )
    if not census.readers_agree:
        lines.append(
            "The readers disagree: the parser reports a class that the "
            "census did not find in the file named."
        )

    for context in census.contexts:
        lines.extend(["", *_context_lines(context)])

    if census.passed_over:
        lines.extend(["", "In no bounded context:"])
        for passed in census.passed_over:
            lines.append(f"  {passed.path} ({passed.reason})")
            lines.extend(f"    {_located(found)}" for found in passed.declarations)

    return "\n".join(lines) + "\n"


def _context_lines(context: ContextCensus) -> list[str]:
    lines = [f"{context.slug} ({context.path})"]

    states = Counter(
        (membership.declaration.kind, membership.state)
        for membership in context.memberships
    )
    for kind in KINDS:
        counted = [
            f"{states[(kind, state)]} {state}"
            for state in STATES
            if states[(kind, state)]
        ]
        if counted:
            lines.append(f"  {kind}: {', '.join(counted)}")

    for disagreement in context.disagreements:
        lines.append(
            f"  disagreement: {disagreement.family} holds {disagreement.name} "
            f"at {disagreement.file}, where no such class was found"
        )

    unresolved = [member for member in context.name_only if member.state != RESOLVED]
    if unresolved:
        lines.append("  Unresolved names:")
    for member in unresolved:
        lines.append(f"    {member.family} {member.name}: {member.state}")
        lines.extend(
            f"      {found.file}:{found.line}" for found in member.declarations
        )

    unclaimed = [
        membership
        for membership in context.memberships
        if membership.state == UNCLAIMED
    ]
    for heading, wanted in (
        ("Unclaimed in a family directory:", True),
        ("Unclaimed elsewhere:", False),
    ):
        found = [
            membership.declaration
            for membership in unclaimed
            if membership.in_family_directory is wanted
        ]
        if found:
            lines.append(f"  {heading}")
            lines.extend(f"    {_located(declaration)}" for declaration in found)

    return lines


def _located(declaration: Declaration) -> str:
    return (
        f"{declaration.file}:{declaration.line} {declaration.kind} {declaration.name}"
    )


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def as_json(census: Census) -> str:
    """The census as JSON, carrying every declaration.

    The shape is provisional: it is what this report holds today, and a
    program reading it should expect it to change. It is output only.
    Nothing reads it back.

    Args:
        census: The census taken

    Returns:
        The document, ending in a newline
    """
    document: dict[str, Any] = {
        "census": STATEMENT,
        "search_root": census.search_root,
        "complete": census.is_complete,
        "readers_agree": census.readers_agree,
        "scope": {
            "files_read": census.files_read,
            "test_files_excluded": census.test_files_excluded,
            "excluded": [
                {"path": exclusion.path, "reason": exclusion.reason}
                for exclusion in census.exclusions
            ],
            "unreadable": [
                {"file": found.file, "problem": found.problem}
                for found in census.unreadable
            ],
        },
        "contexts": [
            {
                "slug": context.slug,
                "path": context.path,
                "declarations": [
                    {
                        **_declaration(membership.declaration),
                        "state": membership.state,
                        "families": list(membership.families),
                        "in_family_directory": membership.in_family_directory,
                    }
                    for membership in context.memberships
                ],
                "name_only_members": [
                    {
                        "family": member.family,
                        "name": member.name,
                        "state": member.state,
                        "declarations": [
                            _declaration(found) for found in member.declarations
                        ],
                    }
                    for member in context.name_only
                ],
                "disagreements": [
                    {
                        "family": disagreement.family,
                        "name": disagreement.name,
                        "file": disagreement.file,
                    }
                    for disagreement in context.disagreements
                ],
            }
            for context in census.contexts
        ],
        "in_no_bounded_context": [
            {
                "path": passed.path,
                "reason": passed.reason,
                "declarations": [_declaration(found) for found in passed.declarations],
            }
            for passed in census.passed_over
        ],
    }
    return json.dumps(document, indent=2) + "\n"


def _declaration(declaration: Declaration) -> dict[str, Any]:
    return {
        "identity": declaration.identity,
        "kind": declaration.kind,
        "file": declaration.file,
        "line": declaration.line,
    }

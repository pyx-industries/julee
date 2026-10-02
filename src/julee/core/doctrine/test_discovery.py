"""Doctrine: that the search found what the codebase says is there.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

Every other module here takes the bounded contexts as given. This one is
about the search, and it is the last of a family: #175 found services by
a rule that could not see twenty of them, #231 missed seven repository
protocols, #238 read no entity package at all, and #256 lost handlers
that moved. Each looked green. This guards the level above all of those
— a codebase where the search itself returns nothing — and the level
below: a file the search reached and could not read.
"""

from pathlib import Path

from julee.core.doctrine.rules.discovery import (
    contexts_found_disagreeing_with_declaration,
    files_that_could_not_be_read,
)
from julee.core.parsers.ast import unreadable_python_files


class TestBoundedContextDiscovery:
    """Doctrine about what doctrine found to check."""

    def test_a_codebase_MUST_agree_with_what_discovery_found(
        self, search_root, solution_config, repo
    ) -> None:
        """Finding no bounded context MUST be declared, not merely true.

        A full doctrine run over a codebase with nothing in it passes
        every rule that iterates contexts, and its output is identical to
        a run over a codebase that complies. Green means "nothing
        objected", and with no subject there is nothing to object to.

        Two codebases are legitimately empty: ``julee``, whose domain
        code left for the kits in ADR 012, and ``julee-viewpoints``,
        which became a Sphinx projection over ``julee-hcd`` and
        ``julee-c4``. Neither is a fault. Both were, until this rule,
        indistinguishable from a solution whose ``search_root`` had a
        typo in it.

        So the emptiness is written down, in the file a reader meets
        first, with the reason next to it. ``bounded_contexts = "none"``
        is the difference between a silence and a statement, and the rule
        objects in both directions: undeclared emptiness, and a
        declaration overtaken by a context added since.
        """
        violations = contexts_found_disagreeing_with_declaration(
            search_root,
            (context.slug for context in repo.discover_all()),
            solution_config.bounded_contexts,
        )

        assert not violations, "\n".join(violations)


class TestSourceReading:
    """Doctrine about what doctrine could read."""

    def test_every_file_doctrine_reads_MUST_be_readable(
        self, project_root, repo
    ) -> None:
        """Every file doctrine reads in a bounded context MUST be readable.

        Doctrine finds what to check by reading source. A file that will
        not parse contributes no class, so no rule has it as a subject,
        and the run passes with the totals it would have had without the
        file. The parser says so in a log line and nowhere else.

        Something else usually notices, because a module that does not
        parse cannot be imported, and the rules that import say that.
        A file nothing imports yet has no such witness. That is the file
        a solution is in the middle of writing, which is when it matters
        most that green means read.

        The files are the ones the class parser reads under each bounded
        context, which is every module but a test. Doctrine does not read
        a test, so it does not ask one to parse.
        """
        unreadable = [
            found
            for context in repo.discover_all()
            for found in unreadable_python_files(
                Path(context.path), relative_to=project_root
            )
        ]

        violations = files_that_could_not_be_read(unreadable)

        assert not violations, "\n".join(violations)

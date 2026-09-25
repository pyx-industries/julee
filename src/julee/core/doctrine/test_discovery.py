"""Doctrine: that the search found what the codebase says is there.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

Every other module here takes the bounded contexts as given. This one is
about the search, and it is the last of a family: #175 found services by
a rule that could not see twenty of them, #231 missed seven repository
protocols, #238 read no entity package at all, and #256 lost handlers
that moved. Each looked green. This guards the level above all of those
— a codebase where the search itself returns nothing.
"""

from julee.core.doctrine.rules.discovery import (
    contexts_found_disagreeing_with_declaration,
)


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

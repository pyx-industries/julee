"""Tests for the discovery rule."""

import pytest

from julee.core.doctrine.rules.discovery import (
    NONE_DECLARED,
    contexts_found_disagreeing_with_declaration,
)

pytestmark = pytest.mark.unit


def objections(found: tuple[str, ...], declaration: str | None) -> list[str]:
    return contexts_found_disagreeing_with_declaration("src/acme", found, declaration)


class TestASolutionWithContexts:
    """The ordinary case: contexts found, nothing declared."""

    def test_finding_contexts_and_saying_nothing_is_fine(self) -> None:
        assert objections(("billing", "shipping"), None) == []

    def test_declaring_none_while_having_some_is_an_objection(self) -> None:
        """The declaration was true when written and has been overtaken."""
        assert objections(("billing",), NONE_DECLARED)

    def test_the_stale_declaration_objection_names_what_it_found(self) -> None:
        """So that the author can see what the line has been suppressing."""
        (objection,) = objections(("billing", "shipping"), NONE_DECLARED)

        assert "billing" in objection
        assert "shipping" in objection


class TestACodebaseWithNoContexts:
    """The case the rule exists for."""

    def test_finding_nothing_and_saying_nothing_is_an_objection(self) -> None:
        """Every context rule has just passed by having no subject."""
        assert objections((), None)

    def test_finding_nothing_and_saying_so_is_fine(self) -> None:
        """julee and julee-viewpoints: a framework and a projection."""
        assert objections((), NONE_DECLARED) == []

    def test_the_objection_names_the_search_root(self) -> None:
        """A typo in search_root is the other way to find nothing."""
        (objection,) = objections((), None)

        assert "src/acme" in objection

    def test_the_objection_says_how_to_declare_it(self) -> None:
        """An author reading it should not have to go looking."""
        (objection,) = objections((), None)

        assert f'bounded_contexts = "{NONE_DECLARED}"' in objection


class TestAMeaninglessDeclaration:
    """A value that is not "none" reads as silence, which is the disease."""

    @pytest.mark.parametrize("declaration", ["None", "NONE", "0", "false", "zero"])
    def test_anything_but_none_is_an_objection(self, declaration: str) -> None:
        assert objections((), declaration)

    def test_it_is_an_objection_even_where_the_census_would_agree(self) -> None:
        """Otherwise a misspelling would pass on an empty codebase."""
        assert objections((), "0")

    def test_the_objection_quotes_what_was_written(self) -> None:
        (objection,) = objections((), "0")

        assert '"0"' in objection

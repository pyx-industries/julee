"""Tests for the Deletable repository protocol.

Delete is opt-in rather than part of BaseRepository. The split across the
kits is clean: c4 and hcd delete everything, because documentation that
cannot forget goes stale; ceap and polling delete nothing, across nine
repository protocols, because deleting a processed document destroys the
record of having processed it.

Putting delete on BaseRepository would have forced those nine to
implement something they should refuse.
"""

import pytest
from pydantic import BaseModel

from julee.repositories.base import BaseRepository, Deletable, RepositoryOf

pytestmark = pytest.mark.unit


class Widget(BaseModel):
    """An entity keyed by a slug."""

    slug: str


class ReadOnlyWidgets:
    """A source that does not delete, the way ceap's repositories do not."""

    async def get(self, entity_id: str) -> Widget | None:
        """Return the widget, or None."""
        return None


class DeletableWidgets(ReadOnlyWidgets):
    """One that does."""

    async def delete(self, entity_id: str) -> bool:
        """Remove the widget, saying whether there was one."""
        return False


def test_a_repository_that_deletes_satisfies_the_protocol() -> None:
    assert isinstance(DeletableWidgets(), Deletable)


def test_a_repository_that_does_not_delete_does_not() -> None:
    """The check that makes the protocol worth having."""
    assert not isinstance(ReadOnlyWidgets(), Deletable)


def test_base_repository_does_not_require_delete() -> None:
    """The decision: a repository opts in rather than being conscripted.

    If delete were on BaseRepository, ceap's eight repository protocols
    and polling's one would each have to implement it or stop being
    repositories.
    """
    assert not hasattr(BaseRepository, "delete")


def test_deletable_declares_its_entity_like_any_repository() -> None:
    """ADR 009: a repository is bound to one entity type.

    Deletable inherits RepositoryOf so doctrine reads the entity off it
    the same way, rather than a deletable repository being exempt from
    the rule.

    Read off the MRO rather than with issubclass, because RepositoryOf
    is deliberately not runtime_checkable — it has no methods, so an
    isinstance against it would say yes to everything.
    """
    assert RepositoryOf in Deletable.__mro__


def test_a_repository_may_be_both() -> None:
    """Deleting is something a CRUD repository adds, not an alternative."""

    class Widgets(ReadOnlyWidgets):
        async def delete(self, entity_id: str) -> bool:
            return True

        async def save(self, entity: Widget) -> None: ...

        async def list_all(self) -> list[Widget]:
            return []

        async def get_many(self, entity_ids: list[str]) -> dict[str, Widget | None]:
            return {}

        async def generate_id(self) -> str:
            return "x"

    repo = Widgets()

    assert isinstance(repo, Deletable)
    assert isinstance(repo, BaseRepository)

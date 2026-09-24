"""Unit tests for MemoryRepositoryMixin."""

import logging

import pytest
from pydantic import BaseModel

from julee.repositories.memory import MemoryRepositoryMixin

pytestmark = pytest.mark.unit


class Widget(BaseModel):
    """An entity keyed by a slug its author chooses."""

    slug: str


class MemoryWidgetRepository(MemoryRepositoryMixin[Widget]):
    """A repository that stores widgets and mints nothing."""

    def __init__(self) -> None:
        """Start empty."""
        self.storage_dict: dict[str, Widget] = {}
        self.logger = logging.getLogger(__name__)
        self.entity_name = "Widget"
        self.id_field = "slug"


class MemoryTicketRepository(MemoryWidgetRepository):
    """A repository whose entities do need an ID minting."""

    async def generate_id(self) -> str:
        """Mint an ID the way a repository with surrogate keys would."""
        return self.generate_entity_id()


async def test_generating_an_id_says_which_repository_will_not() -> None:
    """A naturally-keyed repository should say so rather than invent an ID."""
    with pytest.raises(NotImplementedError, match="MemoryWidgetRepository"):
        await MemoryWidgetRepository().generate_id()


async def test_a_repository_that_mints_ids_overrides_it() -> None:
    """The default is a default, not a prohibition."""
    entity_id = await MemoryTicketRepository().generate_id()

    assert entity_id.startswith("widget-")


# =============================================================================
# delete
# =============================================================================


async def test_deleting_an_entity_removes_it() -> None:
    repo = MemoryWidgetRepository()
    repo.storage_dict["a"] = Widget(slug="a")

    assert await repo.delete("a") is True
    assert repo.storage_dict == {}


async def test_deleting_something_absent_reports_rather_than_raising() -> None:
    """The file mixin has always answered this way; now both do."""
    assert await MemoryWidgetRepository().delete("gone") is False


async def test_deleting_twice_is_not_an_error() -> None:
    repo = MemoryWidgetRepository()
    repo.storage_dict["a"] = Widget(slug="a")

    assert (await repo.delete("a"), await repo.delete("a")) == (True, False)


async def test_deleting_one_leaves_the_others() -> None:
    repo = MemoryWidgetRepository()
    repo.storage_dict["a"] = Widget(slug="a")
    repo.storage_dict["b"] = Widget(slug="b")

    await repo.delete("a")

    assert list(repo.storage_dict) == ["b"]

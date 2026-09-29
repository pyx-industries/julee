"""Unit tests for generic CRUD base classes.

These are the public API for downstream projects generating use cases
via ADR 008. Tests use a fake entity and in-memory repo.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import BaseModel

from julee.core.usecases.generic_crud import (
    CreateUseCase,
    EntityNotFoundError,
    GetUseCase,
    ListUseCase,
    UpdateUseCase,
)

pytestmark = pytest.mark.unit


# =============================================================================
# Fakes
# =============================================================================


class FakeEntity(BaseModel):
    """Minimal entity for testing."""

    entity_id: str
    name: str = ""
    value: int = 0


@dataclass(frozen=True)
class Note:
    """An entity as the estate writes one: a frozen dataclass.

    One field forbids None and one admits it, which is the difference
    the update base class has to see.
    """

    note_id: str
    title: str = ""
    body: str | None = None


class NoteRepo:
    """In-memory notes, remembering every save so a test can count them."""

    def __init__(self) -> None:
        self.stored: dict[str, Note] = {}
        self.saves = 0

    async def get(self, entity_id: str) -> Note | None:
        return self.stored.get(entity_id)

    async def save(self, entity: Note) -> None:
        self.saves += 1
        self.stored[entity.note_id] = entity


class FakeRepo:
    """In-memory repository implementing the BaseRepository interface."""

    def __init__(self):
        self._store: dict[str, FakeEntity] = {}
        self._id_counter = 0

    async def get(self, entity_id: str) -> FakeEntity | None:
        return self._store.get(entity_id)

    async def save(self, entity: FakeEntity) -> None:
        self._store[entity.entity_id] = entity

    async def list_all(self) -> list[FakeEntity]:
        return list(self._store.values())

    async def generate_id(self) -> str:
        self._id_counter += 1
        return f"id-{self._id_counter}"


# =============================================================================
# Concrete subclasses for testing (mimics generated code)
# =============================================================================


class GetFakeUseCase(GetUseCase[FakeEntity, FakeRepo]):
    async def execute(self, entity_id: str) -> FakeEntity:
        return await self._get_by_id(entity_id)


class ListFakeUseCase(ListUseCase[FakeEntity, FakeRepo]):
    async def execute(self) -> list[FakeEntity]:
        return await self._list_all()


class CreateFakeUseCase(CreateUseCase[FakeEntity, FakeRepo]):
    def _build_entity(self, entity_id: str, **kwargs: Any) -> FakeEntity:
        return FakeEntity(entity_id=entity_id, **kwargs)

    async def execute(self, name: str, value: int = 0) -> FakeEntity:
        return await self._create(name=name, value=value)


class UpdateFakeUseCase(UpdateUseCase[FakeEntity, FakeRepo]):
    async def execute(self, entity_id: str, **updates: Any) -> FakeEntity:
        return await self._update_by_id(entity_id, updates)


# =============================================================================
# GetUseCase
# =============================================================================


class TestGetUseCase:
    """Tests for get-by-ID base class."""

    async def test_returns_entity_when_found(self):
        repo = FakeRepo()
        entity = FakeEntity(entity_id="abc", name="found")
        await repo.save(entity)

        uc = GetFakeUseCase(repo)
        result = await uc.execute("abc")
        assert result.entity_id == "abc"
        assert result.name == "found"

    async def test_raises_entity_not_found_error(self):
        repo = FakeRepo()
        uc = GetFakeUseCase(repo)

        with pytest.raises(EntityNotFoundError) as exc_info:
            await uc.execute("missing")
        assert "missing" in str(exc_info.value)
        assert exc_info.value.entity_id == "missing"


# =============================================================================
# ListUseCase
# =============================================================================


class TestListUseCase:
    """Tests for list-all base class."""

    async def test_returns_all_entities(self):
        repo = FakeRepo()
        await repo.save(FakeEntity(entity_id="1", name="a"))
        await repo.save(FakeEntity(entity_id="2", name="b"))

        uc = ListFakeUseCase(repo)
        result = await uc.execute()
        assert len(result) == 2

    async def test_returns_empty_list_when_no_entities(self):
        repo = FakeRepo()
        uc = ListFakeUseCase(repo)
        result = await uc.execute()
        assert result == []


# =============================================================================
# CreateUseCase
# =============================================================================


class TestCreateUseCase:
    """Tests for create base class."""

    async def test_generates_id_builds_and_saves(self):
        repo = FakeRepo()
        uc = CreateFakeUseCase(repo)

        result = await uc.execute(name="new", value=42)
        assert result.entity_id == "id-1"
        assert result.name == "new"
        assert result.value == 42

        # Verify it was persisted
        stored = await repo.get("id-1")
        assert stored is not None
        assert stored.name == "new"

    async def test_sequential_creates_get_unique_ids(self):
        repo = FakeRepo()
        uc = CreateFakeUseCase(repo)

        first = await uc.execute(name="first")
        second = await uc.execute(name="second")
        assert first.entity_id != second.entity_id


# =============================================================================
# UpdateUseCase
# =============================================================================


class TestUpdateUseCase:
    """Tests for update base class."""

    async def test_applies_updates_via_model_copy(self):
        repo = FakeRepo()
        await repo.save(FakeEntity(entity_id="abc", name="old", value=1))

        uc = UpdateFakeUseCase(repo)
        result = await uc.execute("abc", name="new", value=99)
        assert result.name == "new"
        assert result.value == 99

        # Verify persisted
        stored = await repo.get("abc")
        assert stored is not None
        assert stored.name == "new"

    async def test_partial_update_preserves_other_fields(self):
        repo = FakeRepo()
        await repo.save(FakeEntity(entity_id="abc", name="keep", value=42))

        uc = UpdateFakeUseCase(repo)
        result = await uc.execute("abc", value=99)
        assert result.name == "keep"
        assert result.value == 99

    async def test_raises_entity_not_found_error(self):
        repo = FakeRepo()
        uc = UpdateFakeUseCase(repo)

        with pytest.raises(EntityNotFoundError):
            await uc.execute("missing", name="x")


class UpdateNoteUseCase(UpdateUseCase[Note, NoteRepo]):
    """The shape the generator emits, over a frozen dataclass."""

    async def execute(self, note_id: str, **changes: Any) -> Note:
        return await self._update_by_id(note_id, changes)


class TestUpdateRefusesWhatTheTypeForbids:
    """None reaches a field only if the field's type admits it.

    An update request widens every field to ``T | None`` so that "not
    mentioned" and "clear it" can be told apart. That left None free to
    reach a field declared ``str``: replace() stored it, the entity was
    quietly wrong, and the response carried the entity so nothing
    looked. This is the check the request cannot make, because the
    request is what widened the type.
    """

    async def test_clearing_a_field_that_forbids_none_is_refused(self) -> None:
        """A str field cannot hold None, whatever the request allowed."""
        repo = NoteRepo()
        await repo.save(Note(note_id="n-1", title="Kept"))

        with pytest.raises(ValueError, match="title.*does not admit None"):
            await UpdateNoteUseCase(repo).execute("n-1", title=None)

    async def test_nothing_is_saved_when_it_is_refused(self) -> None:
        """Refused before the save, not after: the store is untouched."""
        repo = NoteRepo()
        await repo.save(Note(note_id="n-1", title="Kept"))
        saves_before = repo.saves

        with pytest.raises(ValueError):
            await UpdateNoteUseCase(repo).execute("n-1", title=None)

        assert repo.saves == saves_before
        assert repo.stored["n-1"].title == "Kept"

    async def test_clearing_a_field_that_admits_none_is_stored(self) -> None:
        """Which is what None on an update is for."""
        repo = NoteRepo()
        await repo.save(Note(note_id="n-1", title="Kept", body="scratched"))

        updated = await UpdateNoteUseCase(repo).execute("n-1", body=None)

        assert updated.body is None
        assert updated.title == "Kept"

    async def test_a_real_value_is_still_stored_as_before(self) -> None:
        """The check is about None and nothing else."""
        repo = NoteRepo()
        await repo.save(Note(note_id="n-1", title="Old"))

        updated = await UpdateNoteUseCase(repo).execute("n-1", title="New")

        assert updated.title == "New"

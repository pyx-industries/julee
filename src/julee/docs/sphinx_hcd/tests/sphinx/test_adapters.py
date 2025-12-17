"""Tests for SyncRepositoryAdapter."""

import pytest
from pydantic import BaseModel

from julee.docs.sphinx_hcd.repositories.memory.base import MemoryRepositoryMixin
from julee.docs.sphinx_hcd.sphinx.adapters import SyncRepositoryAdapter


class SampleEntity(BaseModel):
    """Simple entity for adapter tests."""

    id: str
    name: str
    value: int = 0


class SampleMemoryRepository(MemoryRepositoryMixin[SampleEntity]):
    """Sample repository implementation for testing."""

    def __init__(self) -> None:
        self.storage: dict[str, SampleEntity] = {}
        self.entity_name = "SampleEntity"
        self.id_field = "id"

    async def find_by_name(self, name: str) -> list[SampleEntity]:
        """Custom query method for testing run_async."""
        return [e for e in self.storage.values() if e.name == name]


class TestSyncRepositoryAdapter:
    """Test suite for SyncRepositoryAdapter."""

    @pytest.fixture
    def async_repo(self) -> SampleMemoryRepository:
        """Create a fresh test repository."""
        return SampleMemoryRepository()

    @pytest.fixture
    def sync_repo(self, async_repo: SampleMemoryRepository) -> SyncRepositoryAdapter[SampleEntity]:
        """Create a sync adapter wrapping the async repo."""
        return SyncRepositoryAdapter(async_repo)

    @pytest.fixture
    def sample_entity(self) -> SampleEntity:
        """Create a sample test entity."""
        return SampleEntity(id="test-1", name="Test One", value=42)

    def test_save_and_get(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
        sample_entity: SampleEntity,
    ) -> None:
        """Test saving and retrieving an entity."""
        # Save
        sync_repo.save(sample_entity)

        # Get
        retrieved = sync_repo.get("test-1")
        assert retrieved is not None
        assert retrieved.id == "test-1"
        assert retrieved.name == "Test One"
        assert retrieved.value == 42

    def test_get_nonexistent(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
    ) -> None:
        """Test getting a nonexistent entity returns None."""
        result = sync_repo.get("nonexistent")
        assert result is None

    def test_get_many(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
    ) -> None:
        """Test retrieving multiple entities."""
        # Save some entities
        sync_repo.save(SampleEntity(id="a", name="A"))
        sync_repo.save(SampleEntity(id="b", name="B"))
        sync_repo.save(SampleEntity(id="c", name="C"))

        # Get many
        result = sync_repo.get_many(["a", "c", "nonexistent"])
        assert result["a"] is not None
        assert result["a"].name == "A"
        assert result["c"] is not None
        assert result["c"].name == "C"
        assert result["nonexistent"] is None

    def test_list_all(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
    ) -> None:
        """Test listing all entities."""
        # Initially empty
        assert sync_repo.list_all() == []

        # Add some entities
        sync_repo.save(SampleEntity(id="1", name="First"))
        sync_repo.save(SampleEntity(id="2", name="Second"))

        # List all
        all_entities = sync_repo.list_all()
        assert len(all_entities) == 2
        names = {e.name for e in all_entities}
        assert names == {"First", "Second"}

    def test_delete(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
        sample_entity: SampleEntity,
    ) -> None:
        """Test deleting an entity."""
        sync_repo.save(sample_entity)
        assert sync_repo.get("test-1") is not None

        # Delete
        result = sync_repo.delete("test-1")
        assert result is True
        assert sync_repo.get("test-1") is None

        # Delete nonexistent
        result = sync_repo.delete("test-1")
        assert result is False

    def test_clear(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
    ) -> None:
        """Test clearing all entities."""
        sync_repo.save(SampleEntity(id="1", name="One"))
        sync_repo.save(SampleEntity(id="2", name="Two"))
        assert len(sync_repo.list_all()) == 2

        sync_repo.clear()
        assert len(sync_repo.list_all()) == 0

    def test_async_repo_property(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
        async_repo: SampleMemoryRepository,
    ) -> None:
        """Test accessing the underlying async repo."""
        assert sync_repo.async_repo is async_repo

    def test_run_async_custom_method(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
        async_repo: SampleMemoryRepository,
    ) -> None:
        """Test running a custom async method via run_async."""
        sync_repo.save(SampleEntity(id="1", name="Alice", value=1))
        sync_repo.save(SampleEntity(id="2", name="Bob", value=2))
        sync_repo.save(SampleEntity(id="3", name="Alice", value=3))

        # Use run_async for custom query
        result = sync_repo.run_async(async_repo.find_by_name("Alice"))
        assert len(result) == 2
        assert all(e.name == "Alice" for e in result)

    def test_save_overwrites_existing(
        self,
        sync_repo: SyncRepositoryAdapter[SampleEntity],
    ) -> None:
        """Test that saving with same ID overwrites."""
        sync_repo.save(SampleEntity(id="x", name="Original", value=1))
        sync_repo.save(SampleEntity(id="x", name="Updated", value=2))

        retrieved = sync_repo.get("x")
        assert retrieved is not None
        assert retrieved.name == "Updated"
        assert retrieved.value == 2
        assert len(sync_repo.list_all()) == 1

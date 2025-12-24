"""Tests for MemoryCodeInfoRepository."""

import pytest
import pytest_asyncio

from julee.hcd.entities.code_info import (
    BoundedContextInfo,
    ClassInfo,
)
from julee.hcd.repositories.memory.code_info import (
    MemoryCodeInfoRepository,
)


def create_class_info(name: str, file: str = "test.py") -> ClassInfo:
    """Helper to create ClassInfo."""
    return ClassInfo(name=name, docstring=f"{name} class", file=file)


def create_context_info(
    slug: str = "test-context",
    entities: list[ClassInfo] | None = None,
    use_cases: list[ClassInfo] | None = None,
    repository_protocols: list[ClassInfo] | None = None,
    service_protocols: list[ClassInfo] | None = None,
    has_infrastructure: bool = False,
    code_dir: str = "",
) -> BoundedContextInfo:
    """Helper to create test context info."""
    return BoundedContextInfo(
        slug=slug,
        entities=entities or [],
        use_cases=use_cases or [],
        repository_protocols=repository_protocols or [],
        service_protocols=service_protocols or [],
        has_infrastructure=has_infrastructure,
        code_dir=code_dir or slug,
    )


class TestMemoryCodeInfoRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryCodeInfoRepository:
        """Create a fresh repository."""
        return MemoryCodeInfoRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryCodeInfoRepository) -> None:
        """Test saving and retrieving context info."""
        info = create_context_info(slug="vocabulary")
        await repo.save(info)

        retrieved = await repo.get("vocabulary")
        assert retrieved is not None
        assert retrieved.slug == "vocabulary"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryCodeInfoRepository) -> None:
        """Test getting nonexistent context info returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryCodeInfoRepository) -> None:
        """Test listing all context infos."""
        await repo.save(create_context_info(slug="context-1"))
        await repo.save(create_context_info(slug="context-2"))
        await repo.save(create_context_info(slug="context-3"))

        all_infos = await repo.list_all()
        assert len(all_infos) == 3
        slugs = {i.slug for i in all_infos}
        assert slugs == {"context-1", "context-2", "context-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryCodeInfoRepository) -> None:
        """Test deleting context info."""
        await repo.save(create_context_info(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo: MemoryCodeInfoRepository) -> None:
        """Test deleting nonexistent context info."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryCodeInfoRepository) -> None:
        """Test clearing all context infos."""
        await repo.save(create_context_info(slug="context-1"))
        await repo.save(create_context_info(slug="context-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryCodeInfoRepositoryQueries:
    """Test code info-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryCodeInfoRepository:
        """Create a repository."""
        return MemoryCodeInfoRepository()

    @pytest_asyncio.fixture
    async def populated_repo(
        self, repo: MemoryCodeInfoRepository
    ) -> MemoryCodeInfoRepository:
        """Create a repository with sample context infos."""
        contexts = [
            create_context_info(
                slug="vocabulary",
                entities=[
                    create_class_info("Vocabulary", "vocabulary.py"),
                    create_class_info("Term", "term.py"),
                ],
                use_cases=[
                    create_class_info("CreateVocabulary", "create.py"),
                    create_class_info("PublishVocabulary", "publish.py"),
                ],
                repository_protocols=[
                    create_class_info("VocabularyRepository", "vocabulary.py"),
                ],
                has_infrastructure=True,
                code_dir="vocabulary",
            ),
            create_context_info(
                slug="traceability",
                entities=[
                    create_class_info("TraceLink", "trace_link.py"),
                ],
                use_cases=[
                    create_class_info("CreateTraceLink", "create.py"),
                ],
                has_infrastructure=True,
                code_dir="traceability",
            ),
            create_context_info(
                slug="conformity",
                entities=[
                    create_class_info("Assessment", "assessment.py"),
                ],
                # No use cases
                has_infrastructure=False,
                code_dir="conformity",
            ),
            create_context_info(
                slug="empty-context",
                # No entities, no use cases
                has_infrastructure=False,
                code_dir="empty_context",
            ),
        ]
        for ctx in contexts:
            await repo.save(ctx)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_code_dir(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting context info by code directory."""
        info = await populated_repo.get_by_code_dir("vocabulary")
        assert info is not None
        assert info.slug == "vocabulary"

    @pytest.mark.asyncio
    async def test_get_by_code_dir_different_name(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting context info where code_dir differs from slug."""
        info = await populated_repo.get_by_code_dir("empty_context")
        assert info is not None
        assert info.slug == "empty-context"

    @pytest.mark.asyncio
    async def test_get_by_code_dir_not_found(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting context info for unknown code directory."""
        info = await populated_repo.get_by_code_dir("unknown")
        assert info is None

    @pytest.mark.asyncio
    async def test_get_with_entities(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting contexts with entities."""
        contexts = await populated_repo.get_with_entities()
        assert len(contexts) == 3
        slugs = {c.slug for c in contexts}
        assert slugs == {"vocabulary", "traceability", "conformity"}

    @pytest.mark.asyncio
    async def test_get_with_use_cases(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting contexts with use cases."""
        contexts = await populated_repo.get_with_use_cases()
        assert len(contexts) == 2
        slugs = {c.slug for c in contexts}
        assert slugs == {"vocabulary", "traceability"}

    @pytest.mark.asyncio
    async def test_get_with_infrastructure(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting contexts with infrastructure."""
        contexts = await populated_repo.get_with_infrastructure()
        assert len(contexts) == 2
        slugs = {c.slug for c in contexts}
        assert slugs == {"vocabulary", "traceability"}

    @pytest.mark.asyncio
    async def test_get_all_entity_names(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting all unique entity names."""
        names = await populated_repo.get_all_entity_names()
        expected = {"Vocabulary", "Term", "TraceLink", "Assessment"}
        assert names == expected

    @pytest.mark.asyncio
    async def test_get_all_entity_names_empty_repo(
        self, repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting entity names from empty repository."""
        names = await repo.get_all_entity_names()
        assert names == set()

    @pytest.mark.asyncio
    async def test_get_all_use_case_names(
        self, populated_repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting all unique use case names."""
        names = await populated_repo.get_all_use_case_names()
        expected = {"CreateVocabulary", "PublishVocabulary", "CreateTraceLink"}
        assert names == expected

    @pytest.mark.asyncio
    async def test_get_all_use_case_names_empty_repo(
        self, repo: MemoryCodeInfoRepository
    ) -> None:
        """Test getting use case names from empty repository."""
        names = await repo.get_all_use_case_names()
        assert names == set()

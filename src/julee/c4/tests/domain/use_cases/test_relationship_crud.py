"""Tests for Relationship CRUD use cases."""

import pytest

from julee.c4.entities.relationship import (
    ElementType,
    Relationship,
)
from julee.c4.infrastructure.repositories.memory.relationship import (
    MemoryRelationshipRepository,
)
from julee.c4.use_cases.relationship import (
    CreateRelationshipRequest,
    CreateRelationshipUseCase,
    DeleteRelationshipRequest,
    DeleteRelationshipUseCase,
    GetRelationshipRequest,
    GetRelationshipUseCase,
    ListRelationshipsRequest,
    ListRelationshipsUseCase,
    UpdateRelationshipRequest,
    UpdateRelationshipUseCase,
)


class TestCreateRelationshipUseCase:
    """Test creating relationships."""

    @pytest.fixture
    def repo(self) -> MemoryRelationshipRepository:
        """Create a fresh repository."""
        return MemoryRelationshipRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryRelationshipRepository) -> CreateRelationshipUseCase:
        """Create the use case with repository."""
        return CreateRelationshipUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_relationship_success(
        self,
        use_case: CreateRelationshipUseCase,
        repo: MemoryRelationshipRepository,
    ) -> None:
        """Test successfully creating a relationship."""
        request = CreateRelationshipRequest(
            slug="api-to-db",
            source_type="container",
            source_slug="api-app",
            destination_type="container",
            destination_slug="database",
            description="Reads/writes data",
            technology="SQL/TCP",
            tags=["data"],
        )

        response = await use_case.execute(request)

        assert response.relationship is not None
        assert response.relationship.slug == "api-to-db"
        assert response.relationship.source_type == ElementType.CONTAINER
        assert response.relationship.source_slug == "api-app"
        assert response.relationship.destination_slug == "database"
        assert response.relationship.description == "Reads/writes data"

        # Verify it's persisted
        stored = await repo.get("api-to-db")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_relationship_auto_slug(
        self,
        use_case: CreateRelationshipUseCase,
        repo: MemoryRelationshipRepository,
    ) -> None:
        """Test creating relationship with auto-generated slug."""
        request = CreateRelationshipRequest(
            source_type="container",
            source_slug="api-app",
            destination_type="container",
            destination_slug="database",
        )

        response = await use_case.execute(request)

        assert response.relationship is not None
        assert response.relationship.slug == "api-app-to-database"

    @pytest.mark.asyncio
    async def test_create_relationship_with_defaults(
        self, use_case: CreateRelationshipUseCase
    ) -> None:
        """Test creating with minimal required fields uses defaults."""
        request = CreateRelationshipRequest(
            source_type="person",
            source_slug="customer",
            destination_type="software_system",
            destination_slug="banking-system",
        )

        response = await use_case.execute(request)

        assert response.relationship.description == "Uses"
        assert response.relationship.technology == ""
        assert response.relationship.bidirectional is False
        assert response.relationship.tags == []


class TestGetRelationshipUseCase:
    """Test getting relationships."""

    @pytest.fixture
    def repo(self) -> MemoryRelationshipRepository:
        """Create a fresh repository."""
        return MemoryRelationshipRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryRelationshipRepository
    ) -> MemoryRelationshipRepository:
        """Create repository with sample data."""
        await repo.save(
            Relationship(
                slug="api-to-db",
                source_type=ElementType.CONTAINER,
                source_slug="api-app",
                destination_type=ElementType.CONTAINER,
                destination_slug="database",
                description="Reads data",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryRelationshipRepository
    ) -> GetRelationshipUseCase:
        """Create the use case with populated repository."""
        return GetRelationshipUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_relationship(
        self, use_case: GetRelationshipUseCase
    ) -> None:
        """Test getting an existing relationship."""
        request = GetRelationshipRequest(slug="api-to-db")

        response = await use_case.execute(request)

        assert response.relationship is not None
        assert response.relationship.slug == "api-to-db"
        assert response.relationship.source_slug == "api-app"

    @pytest.mark.asyncio
    async def test_get_nonexistent_relationship(
        self, use_case: GetRelationshipUseCase
    ) -> None:
        """Test getting a nonexistent relationship returns None."""
        request = GetRelationshipRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.relationship is None


class TestListRelationshipsUseCase:
    """Test listing relationships."""

    @pytest.fixture
    def repo(self) -> MemoryRelationshipRepository:
        """Create a fresh repository."""
        return MemoryRelationshipRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryRelationshipRepository
    ) -> MemoryRelationshipRepository:
        """Create repository with sample data."""
        relationships = [
            Relationship(
                slug="rel-1",
                source_type=ElementType.CONTAINER,
                source_slug="a",
                destination_type=ElementType.CONTAINER,
                destination_slug="b",
            ),
            Relationship(
                slug="rel-2",
                source_type=ElementType.CONTAINER,
                source_slug="b",
                destination_type=ElementType.CONTAINER,
                destination_slug="c",
            ),
            Relationship(
                slug="rel-3",
                source_type=ElementType.PERSON,
                source_slug="user",
                destination_type=ElementType.SOFTWARE_SYSTEM,
                destination_slug="system",
            ),
        ]
        for r in relationships:
            await repo.save(r)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryRelationshipRepository
    ) -> ListRelationshipsUseCase:
        """Create the use case with populated repository."""
        return ListRelationshipsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_relationships(
        self, use_case: ListRelationshipsUseCase
    ) -> None:
        """Test listing all relationships."""
        request = ListRelationshipsRequest()

        response = await use_case.execute(request)

        assert len(response.relationships) == 3
        slugs = {r.slug for r in response.relationships}
        assert slugs == {"rel-1", "rel-2", "rel-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryRelationshipRepository) -> None:
        """Test listing returns empty list when no relationships."""
        use_case = ListRelationshipsUseCase(repo)
        request = ListRelationshipsRequest()

        response = await use_case.execute(request)

        assert response.relationships == []


class TestUpdateRelationshipUseCase:
    """Test updating relationships."""

    @pytest.fixture
    def repo(self) -> MemoryRelationshipRepository:
        """Create a fresh repository."""
        return MemoryRelationshipRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryRelationshipRepository
    ) -> MemoryRelationshipRepository:
        """Create repository with sample data."""
        await repo.save(
            Relationship(
                slug="api-to-db",
                source_type=ElementType.CONTAINER,
                source_slug="api-app",
                destination_type=ElementType.CONTAINER,
                destination_slug="database",
                description="Original description",
                technology="SQL",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryRelationshipRepository
    ) -> UpdateRelationshipUseCase:
        """Create the use case with populated repository."""
        return UpdateRelationshipUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(
        self,
        use_case: UpdateRelationshipUseCase,
        populated_repo: MemoryRelationshipRepository,
    ) -> None:
        """Test updating a single field."""
        request = UpdateRelationshipRequest(
            slug="api-to-db",
            description="Updated description",
        )

        response = await use_case.execute(request)

        assert response.relationship is not None
        assert response.relationship.description == "Updated description"
        # Other fields unchanged
        assert response.relationship.technology == "SQL"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateRelationshipUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateRelationshipRequest(
            slug="api-to-db",
            description="New description",
            technology="PostgreSQL/TCP",
            bidirectional=True,
        )

        response = await use_case.execute(request)

        assert response.relationship.description == "New description"
        assert response.relationship.technology == "PostgreSQL/TCP"
        assert response.relationship.bidirectional is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_relationship(
        self, use_case: UpdateRelationshipUseCase
    ) -> None:
        """Test updating nonexistent relationship returns None."""
        request = UpdateRelationshipRequest(
            slug="nonexistent",
            description="New description",
        )

        response = await use_case.execute(request)

        assert response.relationship is None


class TestDeleteRelationshipUseCase:
    """Test deleting relationships."""

    @pytest.fixture
    def repo(self) -> MemoryRelationshipRepository:
        """Create a fresh repository."""
        return MemoryRelationshipRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryRelationshipRepository
    ) -> MemoryRelationshipRepository:
        """Create repository with sample data."""
        await repo.save(
            Relationship(
                slug="to-delete",
                source_type=ElementType.CONTAINER,
                source_slug="a",
                destination_type=ElementType.CONTAINER,
                destination_slug="b",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryRelationshipRepository
    ) -> DeleteRelationshipUseCase:
        """Create the use case with populated repository."""
        return DeleteRelationshipUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_relationship(
        self,
        use_case: DeleteRelationshipUseCase,
        populated_repo: MemoryRelationshipRepository,
    ) -> None:
        """Test successfully deleting a relationship."""
        request = DeleteRelationshipRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_relationship(
        self, use_case: DeleteRelationshipUseCase
    ) -> None:
        """Test deleting nonexistent relationship returns False."""
        request = DeleteRelationshipRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False

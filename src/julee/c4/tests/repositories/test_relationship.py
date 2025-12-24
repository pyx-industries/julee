"""Tests for MemoryRelationshipRepository."""

import pytest

from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.infrastructure.repositories.memory.relationship import (
    MemoryRelationshipRepository,
)


def create_relationship(
    source_type: ElementType = ElementType.CONTAINER,
    source_slug: str = "source",
    destination_type: ElementType = ElementType.CONTAINER,
    destination_slug: str = "destination",
    description: str = "Uses",
    technology: str = "",
    docname: str = "",
) -> Relationship:
    """Helper to create test relationships."""
    return Relationship(
        source_type=source_type,
        source_slug=source_slug,
        destination_type=destination_type,
        destination_slug=destination_slug,
        description=description,
        technology=technology,
        docname=docname,
    )


class TestMemoryRelationshipRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryRelationshipRepository:
        """Create a fresh repository."""
        return MemoryRelationshipRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryRelationshipRepository) -> None:
        """Test saving and retrieving a relationship."""
        rel = create_relationship(
            source_slug="api-app",
            destination_slug="database",
            description="Reads from",
        )
        await repo.save(rel)

        retrieved = await repo.get(rel.slug)
        assert retrieved is not None
        assert retrieved.source_slug == "api-app"
        assert retrieved.destination_slug == "database"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryRelationshipRepository) -> None:
        """Test getting a nonexistent relationship returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryRelationshipRepository) -> None:
        """Test listing all relationships."""
        await repo.save(create_relationship(source_slug="a", destination_slug="b"))
        await repo.save(create_relationship(source_slug="b", destination_slug="c"))
        await repo.save(create_relationship(source_slug="c", destination_slug="d"))

        all_rels = await repo.list_all()
        assert len(all_rels) == 3

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryRelationshipRepository) -> None:
        """Test deleting a relationship."""
        rel = create_relationship(source_slug="x", destination_slug="y")
        await repo.save(rel)
        assert await repo.get(rel.slug) is not None

        result = await repo.delete(rel.slug)
        assert result is True
        assert await repo.get(rel.slug) is None

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryRelationshipRepository) -> None:
        """Test clearing all relationships."""
        await repo.save(create_relationship(source_slug="a", destination_slug="b"))
        await repo.save(create_relationship(source_slug="c", destination_slug="d"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryRelationshipRepositoryQueries:
    """Test relationship-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryRelationshipRepository:
        """Create a repository."""
        return MemoryRelationshipRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryRelationshipRepository
    ) -> MemoryRelationshipRepository:
        """Create a repository with sample data."""
        relationships = [
            # Person to system
            create_relationship(
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.SOFTWARE_SYSTEM,
                destination_slug="banking-system",
                description="Uses for banking",
                docname="rels/person",
            ),
            # Container to container (within banking system)
            create_relationship(
                source_type=ElementType.CONTAINER,
                source_slug="api-app",
                destination_type=ElementType.CONTAINER,
                destination_slug="database",
                description="Reads/writes data",
                technology="SQL/TCP",
                docname="rels/api",
            ),
            # Container to container
            create_relationship(
                source_type=ElementType.CONTAINER,
                source_slug="web-app",
                destination_type=ElementType.CONTAINER,
                destination_slug="api-app",
                description="Makes API calls",
                technology="HTTPS/JSON",
                docname="rels/web",
            ),
            # System to system
            create_relationship(
                source_type=ElementType.SOFTWARE_SYSTEM,
                source_slug="banking-system",
                destination_type=ElementType.SOFTWARE_SYSTEM,
                destination_slug="email-system",
                description="Sends notifications",
                docname="rels/systems",
            ),
            # Component to component
            create_relationship(
                source_type=ElementType.COMPONENT,
                source_slug="auth-controller",
                destination_type=ElementType.COMPONENT,
                destination_slug="user-service",
                description="Validates users",
                docname="rels/components",
            ),
        ]
        for rel in relationships:
            await repo.save(rel)
        return repo

    @pytest.mark.asyncio
    async def test_get_for_element(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting relationships for an element."""
        api_rels = await populated_repo.get_for_element(
            ElementType.CONTAINER, "api-app"
        )
        assert len(api_rels) == 2  # api->db and web->api

    @pytest.mark.asyncio
    async def test_get_outgoing(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting outgoing relationships."""
        outgoing = await populated_repo.get_outgoing(ElementType.CONTAINER, "api-app")
        assert len(outgoing) == 1
        assert outgoing[0].destination_slug == "database"

    @pytest.mark.asyncio
    async def test_get_incoming(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting incoming relationships."""
        incoming = await populated_repo.get_incoming(ElementType.CONTAINER, "api-app")
        assert len(incoming) == 1
        assert incoming[0].source_slug == "web-app"

    @pytest.mark.asyncio
    async def test_get_person_relationships(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting person relationships."""
        person_rels = await populated_repo.get_person_relationships()
        assert len(person_rels) == 1
        assert person_rels[0].source_slug == "customer"

    @pytest.mark.asyncio
    async def test_get_cross_system_relationships(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting cross-system relationships."""
        cross_system = await populated_repo.get_cross_system_relationships()
        assert len(cross_system) == 2  # Person->System and System->System

    @pytest.mark.asyncio
    async def test_get_between_containers(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting container-to-container relationships."""
        container_rels = await populated_repo.get_between_containers("")
        assert len(container_rels) == 2
        assert all(
            r.source_type == ElementType.CONTAINER
            and r.destination_type == ElementType.CONTAINER
            for r in container_rels
        )

    @pytest.mark.asyncio
    async def test_get_between_components(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting component-to-component relationships."""
        component_rels = await populated_repo.get_between_components("")
        assert len(component_rels) == 1
        assert component_rels[0].source_slug == "auth-controller"

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test getting relationships by docname."""
        rels = await populated_repo.get_by_docname("rels/api")
        assert len(rels) == 1
        assert rels[0].source_slug == "api-app"

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemoryRelationshipRepository
    ) -> None:
        """Test clearing relationships by docname."""
        count = await populated_repo.clear_by_docname("rels/api")
        assert count == 1

        remaining = await populated_repo.list_all()
        assert len(remaining) == 4

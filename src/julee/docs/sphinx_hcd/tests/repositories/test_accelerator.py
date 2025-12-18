"""Tests for MemoryAcceleratorRepository."""

import pytest
import pytest_asyncio

from julee.docs.sphinx_hcd.domain.models.accelerator import (
    Accelerator,
    IntegrationReference,
)
from julee.docs.sphinx_hcd.repositories.memory.accelerator import (
    MemoryAcceleratorRepository,
)


def create_accelerator(
    slug: str = "test-accelerator",
    status: str = "alpha",
    docname: str = "accelerators/test",
    sources_from: list[IntegrationReference] | None = None,
    publishes_to: list[IntegrationReference] | None = None,
    feeds_into: list[str] | None = None,
    depends_on: list[str] | None = None,
) -> Accelerator:
    """Helper to create test accelerators."""
    return Accelerator(
        slug=slug,
        status=status,
        docname=docname,
        sources_from=sources_from or [],
        publishes_to=publishes_to or [],
        feeds_into=feeds_into or [],
        depends_on=depends_on or [],
    )


class TestMemoryAcceleratorRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryAcceleratorRepository:
        """Create a fresh repository."""
        return MemoryAcceleratorRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryAcceleratorRepository) -> None:
        """Test saving and retrieving an accelerator."""
        accel = create_accelerator(slug="vocabulary")
        await repo.save(accel)

        retrieved = await repo.get("vocabulary")
        assert retrieved is not None
        assert retrieved.slug == "vocabulary"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: MemoryAcceleratorRepository) -> None:
        """Test getting a nonexistent accelerator returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryAcceleratorRepository) -> None:
        """Test listing all accelerators."""
        await repo.save(create_accelerator(slug="accel-1"))
        await repo.save(create_accelerator(slug="accel-2"))
        await repo.save(create_accelerator(slug="accel-3"))

        all_accels = await repo.list_all()
        assert len(all_accels) == 3
        slugs = {a.slug for a in all_accels}
        assert slugs == {"accel-1", "accel-2", "accel-3"}

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryAcceleratorRepository) -> None:
        """Test deleting an accelerator."""
        await repo.save(create_accelerator(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repo: MemoryAcceleratorRepository) -> None:
        """Test deleting a nonexistent accelerator."""
        result = await repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryAcceleratorRepository) -> None:
        """Test clearing all accelerators."""
        await repo.save(create_accelerator(slug="accel-1"))
        await repo.save(create_accelerator(slug="accel-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryAcceleratorRepositoryQueries:
    """Test accelerator-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryAcceleratorRepository:
        """Create a repository."""
        return MemoryAcceleratorRepository()

    @pytest_asyncio.fixture
    async def populated_repo(
        self, repo: MemoryAcceleratorRepository
    ) -> MemoryAcceleratorRepository:
        """Create a repository with sample accelerators."""
        accelerators = [
            create_accelerator(
                slug="vocabulary",
                status="alpha",
                docname="accelerators/vocabulary",
                sources_from=[
                    IntegrationReference(slug="pilot-data", description="Pilot data"),
                ],
                publishes_to=[
                    IntegrationReference(slug="reference-impl", description="SVC"),
                ],
                feeds_into=["traceability"],
                depends_on=["core-infrastructure"],
            ),
            create_accelerator(
                slug="traceability",
                status="alpha",
                docname="accelerators/traceability",
                sources_from=[
                    IntegrationReference(slug="pilot-data", description="Trace data"),
                ],
                depends_on=["vocabulary"],
            ),
            create_accelerator(
                slug="conformity",
                status="future",
                docname="accelerators/conformity",
                depends_on=["vocabulary", "traceability"],
            ),
            create_accelerator(
                slug="core-infrastructure",
                status="production",
                docname="accelerators/core",
            ),
            create_accelerator(
                slug="analytics",
                status="alpha",
                docname="accelerators/vocabulary",  # Same docname as vocabulary
            ),
        ]
        for accel in accelerators:
            await repo.save(accel)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_status(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators by status."""
        accels = await populated_repo.get_by_status("alpha")
        assert len(accels) == 3
        slugs = {a.slug for a in accels}
        assert slugs == {"vocabulary", "traceability", "analytics"}

    @pytest.mark.asyncio
    async def test_get_by_status_case_insensitive(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test status matching is case-insensitive."""
        accels = await populated_repo.get_by_status("ALPHA")
        assert len(accels) == 3

    @pytest.mark.asyncio
    async def test_get_by_status_no_results(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators with unknown status."""
        accels = await populated_repo.get_by_status("unknown")
        assert len(accels) == 0

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators by document name."""
        accels = await populated_repo.get_by_docname("accelerators/vocabulary")
        assert len(accels) == 2
        slugs = {a.slug for a in accels}
        assert slugs == {"vocabulary", "analytics"}

    @pytest.mark.asyncio
    async def test_get_by_docname_no_results(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators for unknown document."""
        accels = await populated_repo.get_by_docname("unknown/document")
        assert len(accels) == 0

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test clearing accelerators by document name."""
        count = await populated_repo.clear_by_docname("accelerators/vocabulary")
        assert count == 2
        assert await populated_repo.get("vocabulary") is None
        assert await populated_repo.get("analytics") is None
        # Other accelerators should remain
        assert len(await populated_repo.list_all()) == 3

    @pytest.mark.asyncio
    async def test_clear_by_docname_none_found(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test clearing non-existent document returns 0."""
        count = await populated_repo.clear_by_docname("unknown/document")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_by_integration_sources_from(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators that source from an integration."""
        accels = await populated_repo.get_by_integration("pilot-data", "sources_from")
        assert len(accels) == 2
        slugs = {a.slug for a in accels}
        assert slugs == {"vocabulary", "traceability"}

    @pytest.mark.asyncio
    async def test_get_by_integration_publishes_to(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators that publish to an integration."""
        accels = await populated_repo.get_by_integration(
            "reference-impl", "publishes_to"
        )
        assert len(accels) == 1
        assert accels[0].slug == "vocabulary"

    @pytest.mark.asyncio
    async def test_get_by_integration_no_results(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators with unknown integration."""
        accels = await populated_repo.get_by_integration("unknown", "sources_from")
        assert len(accels) == 0

    @pytest.mark.asyncio
    async def test_get_dependents(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators that depend on another."""
        dependents = await populated_repo.get_dependents("vocabulary")
        assert len(dependents) == 2
        slugs = {a.slug for a in dependents}
        assert slugs == {"traceability", "conformity"}

    @pytest.mark.asyncio
    async def test_get_dependents_none(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting dependents for accelerator with none."""
        dependents = await populated_repo.get_dependents("conformity")
        assert len(dependents) == 0

    @pytest.mark.asyncio
    async def test_get_fed_by(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting accelerators that feed into another."""
        fed_by = await populated_repo.get_fed_by("traceability")
        assert len(fed_by) == 1
        assert fed_by[0].slug == "vocabulary"

    @pytest.mark.asyncio
    async def test_get_fed_by_none(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting fed_by for accelerator with none."""
        fed_by = await populated_repo.get_fed_by("vocabulary")
        assert len(fed_by) == 0

    @pytest.mark.asyncio
    async def test_get_all_statuses(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting all unique statuses."""
        statuses = await populated_repo.get_all_statuses()
        assert statuses == {"alpha", "future", "production"}

    @pytest.mark.asyncio
    async def test_get_all_statuses_empty_repo(
        self, repo: MemoryAcceleratorRepository
    ) -> None:
        """Test getting statuses from empty repository."""
        statuses = await repo.get_all_statuses()
        assert statuses == set()

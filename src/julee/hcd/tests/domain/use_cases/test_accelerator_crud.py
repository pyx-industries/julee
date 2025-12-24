"""Tests for Accelerator CRUD use cases."""

import pytest

from julee.hcd.domain.use_cases.accelerator import (
    CreateAcceleratorRequest,
    CreateAcceleratorUseCase,
    DeleteAcceleratorRequest,
    DeleteAcceleratorUseCase,
    GetAcceleratorRequest,
    GetAcceleratorUseCase,
    IntegrationReferenceItem,
    ListAcceleratorsRequest,
    ListAcceleratorsUseCase,
    UpdateAcceleratorRequest,
    UpdateAcceleratorUseCase,
)
from julee.hcd.entities.accelerator import (
    Accelerator,
    IntegrationReference,
)
from julee.hcd.repositories.memory.accelerator import (
    MemoryAcceleratorRepository,
)


class TestCreateAcceleratorUseCase:
    """Test creating accelerators."""

    @pytest.fixture
    def repo(self) -> MemoryAcceleratorRepository:
        """Create a fresh repository."""
        return MemoryAcceleratorRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryAcceleratorRepository) -> CreateAcceleratorUseCase:
        """Create the use case with repository."""
        return CreateAcceleratorUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_accelerator_success(
        self,
        use_case: CreateAcceleratorUseCase,
        repo: MemoryAcceleratorRepository,
    ) -> None:
        """Test successfully creating an accelerator."""
        request = CreateAcceleratorRequest(
            slug="data-lake",
            status="production",
            milestone="Q1-2024",
            acceptance="All data sources integrated",
            objective="Centralize data storage",
            sources_from=[
                IntegrationReferenceItem(
                    slug="salesforce-api",
                    description="Customer data",
                ),
            ],
            feeds_into=["analytics-engine"],
            publishes_to=[
                IntegrationReferenceItem(
                    slug="reporting-db",
                    description="Aggregated metrics",
                ),
            ],
            depends_on=["auth-service"],
        )

        response = await use_case.execute(request)

        assert response.accelerator is not None
        assert response.accelerator.slug == "data-lake"
        assert response.accelerator.status == "production"
        assert response.accelerator.milestone == "Q1-2024"
        assert len(response.accelerator.sources_from) == 1
        assert response.accelerator.feeds_into == ["analytics-engine"]

        # Verify it's persisted
        stored = await repo.get("data-lake")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_accelerator_with_defaults(
        self, use_case: CreateAcceleratorUseCase
    ) -> None:
        """Test creating accelerator with default values."""
        request = CreateAcceleratorRequest(slug="minimal-accelerator")

        response = await use_case.execute(request)

        assert response.accelerator.status == ""
        assert response.accelerator.milestone is None
        assert response.accelerator.acceptance is None
        assert response.accelerator.objective == ""
        assert response.accelerator.sources_from == []
        assert response.accelerator.feeds_into == []
        assert response.accelerator.publishes_to == []
        assert response.accelerator.depends_on == []


class TestGetAcceleratorUseCase:
    """Test getting accelerators."""

    @pytest.fixture
    def repo(self) -> MemoryAcceleratorRepository:
        """Create a fresh repository."""
        return MemoryAcceleratorRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryAcceleratorRepository
    ) -> MemoryAcceleratorRepository:
        """Create repository with sample data."""
        await repo.save(
            Accelerator(
                slug="test-accelerator",
                status="beta",
                objective="Test objective",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> GetAcceleratorUseCase:
        """Create the use case with populated repository."""
        return GetAcceleratorUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_accelerator(
        self, use_case: GetAcceleratorUseCase
    ) -> None:
        """Test getting an existing accelerator."""
        request = GetAcceleratorRequest(slug="test-accelerator")

        response = await use_case.execute(request)

        assert response.accelerator is not None
        assert response.accelerator.slug == "test-accelerator"
        assert response.accelerator.status == "beta"

    @pytest.mark.asyncio
    async def test_get_nonexistent_accelerator(
        self, use_case: GetAcceleratorUseCase
    ) -> None:
        """Test getting a nonexistent accelerator returns None."""
        request = GetAcceleratorRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.accelerator is None


class TestListAcceleratorsUseCase:
    """Test listing accelerators."""

    @pytest.fixture
    def repo(self) -> MemoryAcceleratorRepository:
        """Create a fresh repository."""
        return MemoryAcceleratorRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryAcceleratorRepository
    ) -> MemoryAcceleratorRepository:
        """Create repository with sample data."""
        accelerators = [
            Accelerator(slug="accel-1", status="alpha"),
            Accelerator(slug="accel-2", status="beta"),
            Accelerator(slug="accel-3", status="production"),
        ]
        for accelerator in accelerators:
            await repo.save(accelerator)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> ListAcceleratorsUseCase:
        """Create the use case with populated repository."""
        return ListAcceleratorsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_accelerators(
        self, use_case: ListAcceleratorsUseCase
    ) -> None:
        """Test listing all accelerators."""
        request = ListAcceleratorsRequest()

        response = await use_case.execute(request)

        assert len(response.accelerators) == 3
        slugs = {a.slug for a in response.accelerators}
        assert slugs == {"accel-1", "accel-2", "accel-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryAcceleratorRepository) -> None:
        """Test listing returns empty list when no accelerators."""
        use_case = ListAcceleratorsUseCase(repo)
        request = ListAcceleratorsRequest()

        response = await use_case.execute(request)

        assert response.accelerators == []


class TestUpdateAcceleratorUseCase:
    """Test updating accelerators."""

    @pytest.fixture
    def repo(self) -> MemoryAcceleratorRepository:
        """Create a fresh repository."""
        return MemoryAcceleratorRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryAcceleratorRepository
    ) -> MemoryAcceleratorRepository:
        """Create repository with sample data."""
        await repo.save(
            Accelerator(
                slug="update-accelerator",
                status="alpha",
                objective="Original objective",
                sources_from=[
                    IntegrationReference(
                        slug="original-source",
                        description="Original data",
                    )
                ],
                depends_on=["original-dep"],
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> UpdateAcceleratorUseCase:
        """Create the use case with populated repository."""
        return UpdateAcceleratorUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_status(self, use_case: UpdateAcceleratorUseCase) -> None:
        """Test updating the status."""
        request = UpdateAcceleratorRequest(
            slug="update-accelerator",
            status="production",
        )

        response = await use_case.execute(request)

        assert response.accelerator is not None
        assert response.found is True
        assert response.accelerator.status == "production"
        # Other fields unchanged
        assert response.accelerator.objective == "Original objective"

    @pytest.mark.asyncio
    async def test_update_sources_from(
        self, use_case: UpdateAcceleratorUseCase
    ) -> None:
        """Test updating sources_from."""
        request = UpdateAcceleratorRequest(
            slug="update-accelerator",
            sources_from=[
                IntegrationReferenceItem(
                    slug="new-source",
                    description="New data source",
                ),
            ],
        )

        response = await use_case.execute(request)

        assert len(response.accelerator.sources_from) == 1
        assert response.accelerator.sources_from[0].slug == "new-source"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateAcceleratorUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateAcceleratorRequest(
            slug="update-accelerator",
            status="beta",
            milestone="Q2-2024",
            objective="Updated objective",
            feeds_into=["downstream-1", "downstream-2"],
        )

        response = await use_case.execute(request)

        assert response.accelerator.status == "beta"
        assert response.accelerator.milestone == "Q2-2024"
        assert response.accelerator.objective == "Updated objective"
        assert response.accelerator.feeds_into == ["downstream-1", "downstream-2"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_accelerator(
        self, use_case: UpdateAcceleratorUseCase
    ) -> None:
        """Test updating nonexistent accelerator returns None."""
        request = UpdateAcceleratorRequest(
            slug="nonexistent",
            status="production",
        )

        response = await use_case.execute(request)

        assert response.accelerator is None
        assert response.found is False


class TestDeleteAcceleratorUseCase:
    """Test deleting accelerators."""

    @pytest.fixture
    def repo(self) -> MemoryAcceleratorRepository:
        """Create a fresh repository."""
        return MemoryAcceleratorRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryAcceleratorRepository
    ) -> MemoryAcceleratorRepository:
        """Create repository with sample data."""
        await repo.save(Accelerator(slug="to-delete", status="deprecated"))
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryAcceleratorRepository
    ) -> DeleteAcceleratorUseCase:
        """Create the use case with populated repository."""
        return DeleteAcceleratorUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_accelerator(
        self,
        use_case: DeleteAcceleratorUseCase,
        populated_repo: MemoryAcceleratorRepository,
    ) -> None:
        """Test successfully deleting an accelerator."""
        request = DeleteAcceleratorRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_accelerator(
        self, use_case: DeleteAcceleratorUseCase
    ) -> None:
        """Test deleting nonexistent accelerator returns False."""
        request = DeleteAcceleratorRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False

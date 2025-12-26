"""Tests for DynamicStep CRUD use cases."""

import pytest

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType
from julee.c4.infrastructure.repositories.memory.dynamic_step import (
    MemoryDynamicStepRepository,
)
from julee.c4.use_cases.crud import (
    CreateDynamicStepRequest,
    CreateDynamicStepUseCase,
    DeleteDynamicStepRequest,
    DeleteDynamicStepUseCase,
    GetDynamicStepRequest,
    GetDynamicStepUseCase,
    ListDynamicStepsRequest,
    ListDynamicStepsUseCase,
    UpdateDynamicStepRequest,
    UpdateDynamicStepUseCase,
)


class TestCreateDynamicStepUseCase:
    """Test creating dynamic steps."""

    @pytest.fixture
    def repo(self) -> MemoryDynamicStepRepository:
        """Create a fresh repository."""
        return MemoryDynamicStepRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryDynamicStepRepository) -> CreateDynamicStepUseCase:
        """Create the use case with repository."""
        return CreateDynamicStepUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_dynamic_step_success(
        self,
        use_case: CreateDynamicStepUseCase,
        repo: MemoryDynamicStepRepository,
    ) -> None:
        """Test successfully creating a dynamic step."""
        request = CreateDynamicStepRequest(
            slug="login-step-1",
            sequence_name="user-login",
            step_number=1,
            source_type="person",
            source_slug="customer",
            destination_type="container",
            destination_slug="web-app",
            description="Enters credentials",
            technology="HTTPS",
        )

        response = await use_case.execute(request)

        assert response.dynamic_step is not None
        assert response.dynamic_step.slug == "login-step-1"
        assert response.dynamic_step.sequence_name == "user-login"
        assert response.dynamic_step.step_number == 1
        assert response.dynamic_step.source_type == ElementType.PERSON
        assert response.dynamic_step.description == "Enters credentials"

        # Verify it's persisted
        stored = await repo.get("login-step-1")
        assert stored is not None
        assert stored.sequence_name == "user-login"

    @pytest.mark.asyncio
    async def test_create_dynamic_step_auto_slug(
        self,
        use_case: CreateDynamicStepUseCase,
        repo: MemoryDynamicStepRepository,
    ) -> None:
        """Test creating dynamic step with auto-generated slug."""
        request = CreateDynamicStepRequest(
            sequence_name="checkout-flow",
            step_number=3,
            source_type="container",
            source_slug="api-app",
            destination_type="container",
            destination_slug="database",
        )

        response = await use_case.execute(request)

        assert response.dynamic_step is not None
        assert response.dynamic_step.slug == "checkout-flow-step-3"

    @pytest.mark.asyncio
    async def test_create_dynamic_step_with_defaults(
        self, use_case: CreateDynamicStepUseCase
    ) -> None:
        """Test creating with minimal required fields uses defaults."""
        request = CreateDynamicStepRequest(
            sequence_name="test-sequence",
            step_number=1,
            source_type="container",
            source_slug="app",
            destination_type="container",
            destination_slug="db",
        )

        response = await use_case.execute(request)

        assert response.dynamic_step.description == ""
        assert response.dynamic_step.technology == ""
        assert response.dynamic_step.is_async is False


class TestGetDynamicStepUseCase:
    """Test getting dynamic steps."""

    @pytest.fixture
    def repo(self) -> MemoryDynamicStepRepository:
        """Create a fresh repository."""
        return MemoryDynamicStepRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDynamicStepRepository
    ) -> MemoryDynamicStepRepository:
        """Create repository with sample data."""
        await repo.save(
            DynamicStep(
                slug="login-step-1",
                sequence_name="user-login",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="web-app",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> GetDynamicStepUseCase:
        """Create the use case with populated repository."""
        return GetDynamicStepUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_dynamic_step(
        self, use_case: GetDynamicStepUseCase
    ) -> None:
        """Test getting an existing dynamic step."""
        request = GetDynamicStepRequest(slug="login-step-1")

        response = await use_case.execute(request)

        assert response.dynamic_step is not None
        assert response.dynamic_step.slug == "login-step-1"
        assert response.dynamic_step.sequence_name == "user-login"

    @pytest.mark.asyncio
    async def test_get_nonexistent_dynamic_step(
        self, use_case: GetDynamicStepUseCase
    ) -> None:
        """Test getting a nonexistent dynamic step returns None."""
        request = GetDynamicStepRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.dynamic_step is None


class TestListDynamicStepsUseCase:
    """Test listing dynamic steps."""

    @pytest.fixture
    def repo(self) -> MemoryDynamicStepRepository:
        """Create a fresh repository."""
        return MemoryDynamicStepRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDynamicStepRepository
    ) -> MemoryDynamicStepRepository:
        """Create repository with sample data."""
        steps = [
            DynamicStep(
                slug="step-1",
                sequence_name="flow",
                step_number=1,
                source_type=ElementType.CONTAINER,
                source_slug="a",
                destination_type=ElementType.CONTAINER,
                destination_slug="b",
            ),
            DynamicStep(
                slug="step-2",
                sequence_name="flow",
                step_number=2,
                source_type=ElementType.CONTAINER,
                source_slug="b",
                destination_type=ElementType.CONTAINER,
                destination_slug="c",
            ),
            DynamicStep(
                slug="step-3",
                sequence_name="other-flow",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="user",
                destination_type=ElementType.CONTAINER,
                destination_slug="app",
            ),
        ]
        for s in steps:
            await repo.save(s)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> ListDynamicStepsUseCase:
        """Create the use case with populated repository."""
        return ListDynamicStepsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_dynamic_steps(
        self, use_case: ListDynamicStepsUseCase
    ) -> None:
        """Test listing all dynamic steps."""
        request = ListDynamicStepsRequest()

        response = await use_case.execute(request)

        assert len(response.dynamic_steps) == 3
        slugs = {s.slug for s in response.dynamic_steps}
        assert slugs == {"step-1", "step-2", "step-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryDynamicStepRepository) -> None:
        """Test listing returns empty list when no steps."""
        use_case = ListDynamicStepsUseCase(repo)
        request = ListDynamicStepsRequest()

        response = await use_case.execute(request)

        assert response.dynamic_steps == []


class TestUpdateDynamicStepUseCase:
    """Test updating dynamic steps."""

    @pytest.fixture
    def repo(self) -> MemoryDynamicStepRepository:
        """Create a fresh repository."""
        return MemoryDynamicStepRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDynamicStepRepository
    ) -> MemoryDynamicStepRepository:
        """Create repository with sample data."""
        await repo.save(
            DynamicStep(
                slug="login-step-1",
                sequence_name="user-login",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="web-app",
                description="Original description",
                technology="HTTP",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> UpdateDynamicStepUseCase:
        """Create the use case with populated repository."""
        return UpdateDynamicStepUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_single_field(
        self,
        use_case: UpdateDynamicStepUseCase,
        populated_repo: MemoryDynamicStepRepository,
    ) -> None:
        """Test updating a single field."""
        request = UpdateDynamicStepRequest(
            slug="login-step-1",
            description="Updated description",
        )

        response = await use_case.execute(request)

        assert response.dynamic_step is not None
        assert response.dynamic_step.description == "Updated description"
        # Other fields unchanged
        assert response.dynamic_step.technology == "HTTP"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateDynamicStepUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateDynamicStepRequest(
            slug="login-step-1",
            description="New description",
            technology="HTTPS/JSON",
            step_number=2,
        )

        response = await use_case.execute(request)

        assert response.dynamic_step.description == "New description"
        assert response.dynamic_step.technology == "HTTPS/JSON"
        assert response.dynamic_step.step_number == 2

    @pytest.mark.asyncio
    async def test_update_step_number_and_technology(
        self, use_case: UpdateDynamicStepUseCase
    ) -> None:
        """Test updating step number and technology together."""
        request = UpdateDynamicStepRequest(
            slug="login-step-1",
            step_number=5,
            technology="WebSocket",
        )

        response = await use_case.execute(request)

        assert response.dynamic_step is not None
        assert response.dynamic_step.step_number == 5
        assert response.dynamic_step.technology == "WebSocket"

    @pytest.mark.asyncio
    async def test_update_nonexistent_dynamic_step(
        self, use_case: UpdateDynamicStepUseCase
    ) -> None:
        """Test updating nonexistent dynamic step returns None."""
        request = UpdateDynamicStepRequest(
            slug="nonexistent",
            description="New description",
        )

        response = await use_case.execute(request)

        assert response.dynamic_step is None


class TestDeleteDynamicStepUseCase:
    """Test deleting dynamic steps."""

    @pytest.fixture
    def repo(self) -> MemoryDynamicStepRepository:
        """Create a fresh repository."""
        return MemoryDynamicStepRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDynamicStepRepository
    ) -> MemoryDynamicStepRepository:
        """Create repository with sample data."""
        await repo.save(
            DynamicStep(
                slug="to-delete",
                sequence_name="flow",
                step_number=1,
                source_type=ElementType.CONTAINER,
                source_slug="a",
                destination_type=ElementType.CONTAINER,
                destination_slug="b",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> DeleteDynamicStepUseCase:
        """Create the use case with populated repository."""
        return DeleteDynamicStepUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_dynamic_step(
        self,
        use_case: DeleteDynamicStepUseCase,
        populated_repo: MemoryDynamicStepRepository,
    ) -> None:
        """Test successfully deleting a dynamic step."""
        request = DeleteDynamicStepRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_dynamic_step(
        self, use_case: DeleteDynamicStepUseCase
    ) -> None:
        """Test deleting nonexistent dynamic step returns False."""
        request = DeleteDynamicStepRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False

"""Tests for Integration CRUD use cases."""

import pytest

from julee.hcd.domain.models.integration import (
    Direction,
    ExternalDependency,
    Integration,
)
from julee.hcd.domain.use_cases.integration import (
    CreateIntegrationUseCase,
    DeleteIntegrationUseCase,
    GetIntegrationUseCase,
    ListIntegrationsUseCase,
    UpdateIntegrationUseCase,
)
from julee.hcd.domain.use_cases.requests import (
    CreateIntegrationRequest,
    DeleteIntegrationRequest,
    ExternalDependencyInput,
    GetIntegrationRequest,
    ListIntegrationsRequest,
    UpdateIntegrationRequest,
)
from julee.hcd.repositories.memory.integration import (
    MemoryIntegrationRepository,
)


class TestCreateIntegrationUseCase:
    """Test creating integrations."""

    @pytest.fixture
    def repo(self) -> MemoryIntegrationRepository:
        """Create a fresh repository."""
        return MemoryIntegrationRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryIntegrationRepository) -> CreateIntegrationUseCase:
        """Create the use case with repository."""
        return CreateIntegrationUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_integration_success(
        self,
        use_case: CreateIntegrationUseCase,
        repo: MemoryIntegrationRepository,
    ) -> None:
        """Test successfully creating an integration."""
        request = CreateIntegrationRequest(
            slug="salesforce-api",
            module="julee.integrations.salesforce",
            name="Salesforce CRM API",
            description="Integration with Salesforce CRM",
            direction="inbound",
            depends_on=[
                ExternalDependencyInput(
                    name="Salesforce API",
                    url="https://salesforce.com/api",
                    description="External CRM system",
                ),
            ],
        )

        response = await use_case.execute(request)

        assert response.integration is not None
        assert response.integration.slug == "salesforce-api"
        assert response.integration.module == "julee.integrations.salesforce"
        assert response.integration.name == "Salesforce CRM API"
        assert response.integration.direction == Direction.INBOUND
        assert len(response.integration.depends_on) == 1

        # Verify it's persisted
        stored = await repo.get("salesforce-api")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_integration_with_defaults(
        self, use_case: CreateIntegrationUseCase
    ) -> None:
        """Test creating integration with default values."""
        request = CreateIntegrationRequest(
            slug="minimal-integration",
            module="minimal.module",
            name="Minimal Integration",
        )

        response = await use_case.execute(request)

        assert response.integration.description == ""
        assert response.integration.direction == Direction.BIDIRECTIONAL
        assert response.integration.depends_on == []

    @pytest.mark.asyncio
    async def test_create_outbound_integration(
        self, use_case: CreateIntegrationUseCase
    ) -> None:
        """Test creating an outbound integration."""
        request = CreateIntegrationRequest(
            slug="email-sender",
            module="integrations.email",
            name="Email Sender",
            direction="outbound",
        )

        response = await use_case.execute(request)

        assert response.integration.direction == Direction.OUTBOUND


class TestGetIntegrationUseCase:
    """Test getting integrations."""

    @pytest.fixture
    def repo(self) -> MemoryIntegrationRepository:
        """Create a fresh repository."""
        return MemoryIntegrationRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryIntegrationRepository
    ) -> MemoryIntegrationRepository:
        """Create repository with sample data."""
        await repo.save(
            Integration(
                slug="test-integration",
                module="test.module",
                name="Test Integration",
                direction=Direction.INBOUND,
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryIntegrationRepository
    ) -> GetIntegrationUseCase:
        """Create the use case with populated repository."""
        return GetIntegrationUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_integration(
        self, use_case: GetIntegrationUseCase
    ) -> None:
        """Test getting an existing integration."""
        request = GetIntegrationRequest(slug="test-integration")

        response = await use_case.execute(request)

        assert response.integration is not None
        assert response.integration.slug == "test-integration"
        assert response.integration.name == "Test Integration"

    @pytest.mark.asyncio
    async def test_get_nonexistent_integration(
        self, use_case: GetIntegrationUseCase
    ) -> None:
        """Test getting a nonexistent integration returns None."""
        request = GetIntegrationRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.integration is None


class TestListIntegrationsUseCase:
    """Test listing integrations."""

    @pytest.fixture
    def repo(self) -> MemoryIntegrationRepository:
        """Create a fresh repository."""
        return MemoryIntegrationRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryIntegrationRepository
    ) -> MemoryIntegrationRepository:
        """Create repository with sample data."""
        integrations = [
            Integration(
                slug="int-1",
                module="mod1",
                name="Integration 1",
                direction=Direction.INBOUND,
            ),
            Integration(
                slug="int-2",
                module="mod2",
                name="Integration 2",
                direction=Direction.OUTBOUND,
            ),
            Integration(
                slug="int-3",
                module="mod3",
                name="Integration 3",
                direction=Direction.BIDIRECTIONAL,
            ),
        ]
        for integration in integrations:
            await repo.save(integration)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryIntegrationRepository
    ) -> ListIntegrationsUseCase:
        """Create the use case with populated repository."""
        return ListIntegrationsUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_integrations(
        self, use_case: ListIntegrationsUseCase
    ) -> None:
        """Test listing all integrations."""
        request = ListIntegrationsRequest()

        response = await use_case.execute(request)

        assert len(response.integrations) == 3
        slugs = {i.slug for i in response.integrations}
        assert slugs == {"int-1", "int-2", "int-3"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryIntegrationRepository) -> None:
        """Test listing returns empty list when no integrations."""
        use_case = ListIntegrationsUseCase(repo)
        request = ListIntegrationsRequest()

        response = await use_case.execute(request)

        assert response.integrations == []


class TestUpdateIntegrationUseCase:
    """Test updating integrations."""

    @pytest.fixture
    def repo(self) -> MemoryIntegrationRepository:
        """Create a fresh repository."""
        return MemoryIntegrationRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryIntegrationRepository
    ) -> MemoryIntegrationRepository:
        """Create repository with sample data."""
        await repo.save(
            Integration(
                slug="update-integration",
                module="original.module",
                name="Original Name",
                description="Original description",
                direction=Direction.INBOUND,
                depends_on=[
                    ExternalDependency(
                        name="Original Dependency",
                        url="https://original.com",
                    )
                ],
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryIntegrationRepository
    ) -> UpdateIntegrationUseCase:
        """Create the use case with populated repository."""
        return UpdateIntegrationUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_name(self, use_case: UpdateIntegrationUseCase) -> None:
        """Test updating the name."""
        request = UpdateIntegrationRequest(
            slug="update-integration",
            name="Updated Name",
        )

        response = await use_case.execute(request)

        assert response.integration is not None
        assert response.found is True
        assert response.integration.name == "Updated Name"
        # Other fields unchanged
        assert response.integration.description == "Original description"

    @pytest.mark.asyncio
    async def test_update_direction(self, use_case: UpdateIntegrationUseCase) -> None:
        """Test updating the direction."""
        request = UpdateIntegrationRequest(
            slug="update-integration",
            direction="outbound",
        )

        response = await use_case.execute(request)

        assert response.integration.direction == Direction.OUTBOUND

    @pytest.mark.asyncio
    async def test_update_depends_on(self, use_case: UpdateIntegrationUseCase) -> None:
        """Test updating depends_on."""
        request = UpdateIntegrationRequest(
            slug="update-integration",
            depends_on=[
                ExternalDependencyInput(
                    name="New Dependency",
                    url="https://new.com",
                    description="New external system",
                ),
            ],
        )

        response = await use_case.execute(request)

        assert len(response.integration.depends_on) == 1
        assert response.integration.depends_on[0].name == "New Dependency"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(
        self, use_case: UpdateIntegrationUseCase
    ) -> None:
        """Test updating multiple fields."""
        request = UpdateIntegrationRequest(
            slug="update-integration",
            name="New Name",
            description="New description",
            direction="bidirectional",
        )

        response = await use_case.execute(request)

        assert response.integration.name == "New Name"
        assert response.integration.description == "New description"
        assert response.integration.direction == Direction.BIDIRECTIONAL

    @pytest.mark.asyncio
    async def test_update_nonexistent_integration(
        self, use_case: UpdateIntegrationUseCase
    ) -> None:
        """Test updating nonexistent integration returns None."""
        request = UpdateIntegrationRequest(
            slug="nonexistent",
            name="New Name",
        )

        response = await use_case.execute(request)

        assert response.integration is None
        assert response.found is False


class TestDeleteIntegrationUseCase:
    """Test deleting integrations."""

    @pytest.fixture
    def repo(self) -> MemoryIntegrationRepository:
        """Create a fresh repository."""
        return MemoryIntegrationRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryIntegrationRepository
    ) -> MemoryIntegrationRepository:
        """Create repository with sample data."""
        await repo.save(
            Integration(
                slug="to-delete",
                module="to.delete",
                name="To Delete",
            )
        )
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryIntegrationRepository
    ) -> DeleteIntegrationUseCase:
        """Create the use case with populated repository."""
        return DeleteIntegrationUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_integration(
        self,
        use_case: DeleteIntegrationUseCase,
        populated_repo: MemoryIntegrationRepository,
    ) -> None:
        """Test successfully deleting an integration."""
        request = DeleteIntegrationRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_integration(
        self, use_case: DeleteIntegrationUseCase
    ) -> None:
        """Test deleting nonexistent integration returns False."""
        request = DeleteIntegrationRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False

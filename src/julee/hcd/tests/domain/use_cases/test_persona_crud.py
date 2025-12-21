"""Tests for Persona CRUD use cases."""

import pytest

from julee.hcd.domain.use_cases.requests import (
    CreatePersonaRequest,
    DeletePersonaRequest,
    ListPersonasRequest,
    UpdatePersonaRequest,
)
from julee.hcd.domain.models.persona import Persona
from julee.hcd.domain.use_cases.persona import (
    CreatePersonaUseCase,
    DeletePersonaUseCase,
    GetPersonaBySlugRequest,
    GetPersonaBySlugUseCase,
    ListPersonasUseCase,
    UpdatePersonaUseCase,
)
from julee.hcd.repositories.memory.persona import MemoryPersonaRepository


class TestCreatePersonaUseCase:
    """Test creating personas."""

    @pytest.fixture
    def repo(self) -> MemoryPersonaRepository:
        """Create a fresh repository."""
        return MemoryPersonaRepository()

    @pytest.fixture
    def use_case(self, repo: MemoryPersonaRepository) -> CreatePersonaUseCase:
        """Create the use case with repository."""
        return CreatePersonaUseCase(repo)

    @pytest.mark.asyncio
    async def test_create_persona_success(
        self,
        use_case: CreatePersonaUseCase,
        repo: MemoryPersonaRepository,
    ) -> None:
        """Test successfully creating a persona."""
        request = CreatePersonaRequest(
            slug="new-employee",
            name="New Employee",
            goals=["Get set up quickly", "Understand company systems"],
            frustrations=["Complex onboarding", "Too many tools"],
            jobs_to_be_done=["Complete onboarding", "Learn team processes"],
            context="Recently hired staff member in first week",
        )

        response = await use_case.execute(request)

        assert response.persona is not None
        assert response.persona.slug == "new-employee"
        assert response.persona.name == "New Employee"
        assert len(response.persona.goals) == 2
        assert len(response.persona.frustrations) == 2
        assert "Complete onboarding" in response.persona.jobs_to_be_done
        assert response.persona.context == "Recently hired staff member in first week"

        # Verify it's persisted
        stored = await repo.get("new-employee")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_persona_with_defaults(
        self, use_case: CreatePersonaUseCase
    ) -> None:
        """Test creating persona with default values."""
        request = CreatePersonaRequest(
            slug="minimal-persona",
            name="Minimal Persona",
        )

        response = await use_case.execute(request)

        assert response.persona.goals == []
        assert response.persona.frustrations == []
        assert response.persona.jobs_to_be_done == []
        assert response.persona.context == ""


class TestGetPersonaBySlugUseCase:
    """Test getting personas by slug."""

    @pytest.fixture
    def repo(self) -> MemoryPersonaRepository:
        """Create a fresh repository."""
        return MemoryPersonaRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryPersonaRepository
    ) -> MemoryPersonaRepository:
        """Create repository with sample data."""
        persona = Persona.from_definition(
            slug="test-persona",
            name="Test Persona",
            goals=["Test goal"],
            context="Test context",
        )
        await repo.save(persona)
        return repo

    @pytest.fixture
    def use_case(
        self, populated_repo: MemoryPersonaRepository
    ) -> GetPersonaBySlugUseCase:
        """Create the use case with populated repository."""
        return GetPersonaBySlugUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_get_existing_persona(
        self, use_case: GetPersonaBySlugUseCase
    ) -> None:
        """Test getting an existing persona by slug."""
        request = GetPersonaBySlugRequest(slug="test-persona")

        response = await use_case.execute(request)

        assert response.persona is not None
        assert response.persona.name == "Test Persona"

    @pytest.mark.asyncio
    async def test_get_nonexistent_persona(
        self, use_case: GetPersonaBySlugUseCase
    ) -> None:
        """Test getting a nonexistent persona returns None."""
        request = GetPersonaBySlugRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.persona is None


class TestListPersonasUseCase:
    """Test listing personas."""

    @pytest.fixture
    def repo(self) -> MemoryPersonaRepository:
        """Create a fresh repository."""
        return MemoryPersonaRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryPersonaRepository
    ) -> MemoryPersonaRepository:
        """Create repository with sample data."""
        personas = [
            Persona.from_definition(slug="persona-1", name="Persona One"),
            Persona.from_definition(slug="persona-2", name="Persona Two"),
            Persona.from_definition(slug="persona-3", name="Persona Three"),
        ]
        for persona in personas:
            await repo.save(persona)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryPersonaRepository) -> ListPersonasUseCase:
        """Create the use case with populated repository."""
        return ListPersonasUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_list_all_personas(self, use_case: ListPersonasUseCase) -> None:
        """Test listing all personas."""
        request = ListPersonasRequest()

        response = await use_case.execute(request)

        assert len(response.personas) == 3
        names = {p.name for p in response.personas}
        assert names == {"Persona One", "Persona Two", "Persona Three"}

    @pytest.mark.asyncio
    async def test_list_empty_repo(self, repo: MemoryPersonaRepository) -> None:
        """Test listing returns empty list when no personas."""
        use_case = ListPersonasUseCase(repo)
        request = ListPersonasRequest()

        response = await use_case.execute(request)

        assert response.personas == []


class TestUpdatePersonaUseCase:
    """Test updating personas."""

    @pytest.fixture
    def repo(self) -> MemoryPersonaRepository:
        """Create a fresh repository."""
        return MemoryPersonaRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryPersonaRepository
    ) -> MemoryPersonaRepository:
        """Create repository with sample data."""
        persona = Persona.from_definition(
            slug="update-persona",
            name="Original Name",
            goals=["Original goal"],
            frustrations=["Original frustration"],
            context="Original context",
        )
        await repo.save(persona)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryPersonaRepository) -> UpdatePersonaUseCase:
        """Create the use case with populated repository."""
        return UpdatePersonaUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_update_name(self, use_case: UpdatePersonaUseCase) -> None:
        """Test updating the name."""
        request = UpdatePersonaRequest(
            slug="update-persona",
            name="Updated Name",
        )

        response = await use_case.execute(request)

        assert response.persona is not None
        assert response.found is True
        assert response.persona.name == "Updated Name"
        # Other fields unchanged
        assert response.persona.context == "Original context"

    @pytest.mark.asyncio
    async def test_update_goals(self, use_case: UpdatePersonaUseCase) -> None:
        """Test updating goals."""
        request = UpdatePersonaRequest(
            slug="update-persona",
            goals=["New goal 1", "New goal 2"],
        )

        response = await use_case.execute(request)

        assert response.persona.goals == ["New goal 1", "New goal 2"]

    @pytest.mark.asyncio
    async def test_update_frustrations(self, use_case: UpdatePersonaUseCase) -> None:
        """Test updating frustrations."""
        request = UpdatePersonaRequest(
            slug="update-persona",
            frustrations=["New frustration"],
        )

        response = await use_case.execute(request)

        assert response.persona.frustrations == ["New frustration"]

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, use_case: UpdatePersonaUseCase) -> None:
        """Test updating multiple fields."""
        request = UpdatePersonaRequest(
            slug="update-persona",
            name="New Name",
            context="New context",
            jobs_to_be_done=["Job 1", "Job 2"],
        )

        response = await use_case.execute(request)

        assert response.persona.name == "New Name"
        assert response.persona.context == "New context"
        assert response.persona.jobs_to_be_done == ["Job 1", "Job 2"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_persona(
        self, use_case: UpdatePersonaUseCase
    ) -> None:
        """Test updating nonexistent persona returns None."""
        request = UpdatePersonaRequest(
            slug="nonexistent",
            name="New Name",
        )

        response = await use_case.execute(request)

        assert response.persona is None
        assert response.found is False


class TestDeletePersonaUseCase:
    """Test deleting personas."""

    @pytest.fixture
    def repo(self) -> MemoryPersonaRepository:
        """Create a fresh repository."""
        return MemoryPersonaRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryPersonaRepository
    ) -> MemoryPersonaRepository:
        """Create repository with sample data."""
        persona = Persona.from_definition(
            slug="to-delete",
            name="To Delete",
        )
        await repo.save(persona)
        return repo

    @pytest.fixture
    def use_case(self, populated_repo: MemoryPersonaRepository) -> DeletePersonaUseCase:
        """Create the use case with populated repository."""
        return DeletePersonaUseCase(populated_repo)

    @pytest.mark.asyncio
    async def test_delete_existing_persona(
        self,
        use_case: DeletePersonaUseCase,
        populated_repo: MemoryPersonaRepository,
    ) -> None:
        """Test successfully deleting a persona."""
        request = DeletePersonaRequest(slug="to-delete")

        response = await use_case.execute(request)

        assert response.deleted is True

        # Verify it's removed
        stored = await populated_repo.get("to-delete")
        assert stored is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_persona(
        self, use_case: DeletePersonaUseCase
    ) -> None:
        """Test deleting nonexistent persona returns False."""
        request = DeletePersonaRequest(slug="nonexistent")

        response = await use_case.execute(request)

        assert response.deleted is False

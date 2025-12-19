"""Tests for MemoryDynamicStepRepository."""

import pytest

from julee.docs.sphinx_c4.domain.models.dynamic_step import DynamicStep
from julee.docs.sphinx_c4.domain.models.relationship import ElementType
from julee.docs.sphinx_c4.repositories.memory.dynamic_step import (
    MemoryDynamicStepRepository,
)


def create_step(
    slug: str = "test-step",
    sequence_name: str = "test-sequence",
    step_number: int = 1,
    source_type: ElementType = ElementType.CONTAINER,
    source_slug: str = "source",
    destination_type: ElementType = ElementType.CONTAINER,
    destination_slug: str = "destination",
    docname: str = "",
) -> DynamicStep:
    """Helper to create test dynamic steps."""
    return DynamicStep(
        slug=slug,
        sequence_name=sequence_name,
        step_number=step_number,
        source_type=source_type,
        source_slug=source_slug,
        destination_type=destination_type,
        destination_slug=destination_slug,
        docname=docname,
    )


class TestMemoryDynamicStepRepositoryBasicOperations:
    """Test basic CRUD operations."""

    @pytest.fixture
    def repo(self) -> MemoryDynamicStepRepository:
        """Create a fresh repository."""
        return MemoryDynamicStepRepository()

    @pytest.mark.asyncio
    async def test_save_and_get(self, repo: MemoryDynamicStepRepository) -> None:
        """Test saving and retrieving a dynamic step."""
        step = create_step(slug="login-step-1", sequence_name="user-login")
        await repo.save(step)

        retrieved = await repo.get("login-step-1")
        assert retrieved is not None
        assert retrieved.slug == "login-step-1"
        assert retrieved.sequence_name == "user-login"

    @pytest.mark.asyncio
    async def test_get_nonexistent(
        self, repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting a nonexistent step returns None."""
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo: MemoryDynamicStepRepository) -> None:
        """Test listing all steps."""
        await repo.save(create_step(slug="step-1"))
        await repo.save(create_step(slug="step-2"))
        await repo.save(create_step(slug="step-3"))

        all_steps = await repo.list_all()
        assert len(all_steps) == 3

    @pytest.mark.asyncio
    async def test_delete(self, repo: MemoryDynamicStepRepository) -> None:
        """Test deleting a step."""
        await repo.save(create_step(slug="to-delete"))
        assert await repo.get("to-delete") is not None

        result = await repo.delete("to-delete")
        assert result is True
        assert await repo.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_clear(self, repo: MemoryDynamicStepRepository) -> None:
        """Test clearing all steps."""
        await repo.save(create_step(slug="step-1"))
        await repo.save(create_step(slug="step-2"))
        assert len(await repo.list_all()) == 2

        await repo.clear()
        assert len(await repo.list_all()) == 0


class TestMemoryDynamicStepRepositoryQueries:
    """Test dynamic step-specific query methods."""

    @pytest.fixture
    def repo(self) -> MemoryDynamicStepRepository:
        """Create a repository."""
        return MemoryDynamicStepRepository()

    @pytest.fixture
    async def populated_repo(
        self, repo: MemoryDynamicStepRepository
    ) -> MemoryDynamicStepRepository:
        """Create a repository with sample data."""
        steps = [
            # Login sequence
            create_step(
                slug="login-1",
                sequence_name="user-login",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="web-app",
                docname="sequences/login",
            ),
            create_step(
                slug="login-2",
                sequence_name="user-login",
                step_number=2,
                source_type=ElementType.CONTAINER,
                source_slug="web-app",
                destination_type=ElementType.CONTAINER,
                destination_slug="api-app",
                docname="sequences/login",
            ),
            create_step(
                slug="login-3",
                sequence_name="user-login",
                step_number=3,
                source_type=ElementType.CONTAINER,
                source_slug="api-app",
                destination_type=ElementType.CONTAINER,
                destination_slug="database",
                docname="sequences/login",
            ),
            # Checkout sequence
            create_step(
                slug="checkout-1",
                sequence_name="checkout-flow",
                step_number=1,
                source_type=ElementType.PERSON,
                source_slug="customer",
                destination_type=ElementType.CONTAINER,
                destination_slug="web-app",
                docname="sequences/checkout",
            ),
            create_step(
                slug="checkout-2",
                sequence_name="checkout-flow",
                step_number=2,
                source_type=ElementType.CONTAINER,
                source_slug="web-app",
                destination_type=ElementType.CONTAINER,
                destination_slug="payment-service",
                docname="sequences/checkout",
            ),
        ]
        for step in steps:
            await repo.save(step)
        return repo

    @pytest.mark.asyncio
    async def test_get_by_sequence(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting steps by sequence name."""
        login_steps = await populated_repo.get_by_sequence("user-login")
        assert len(login_steps) == 3
        # Verify ordering
        assert [s.step_number for s in login_steps] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_get_by_sequence_returns_sorted(
        self, repo: MemoryDynamicStepRepository
    ) -> None:
        """Test that get_by_sequence returns steps in order."""
        # Add steps out of order
        await repo.save(create_step(slug="s3", sequence_name="test", step_number=3))
        await repo.save(create_step(slug="s1", sequence_name="test", step_number=1))
        await repo.save(create_step(slug="s2", sequence_name="test", step_number=2))

        steps = await repo.get_by_sequence("test")
        assert [s.step_number for s in steps] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_get_sequences(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting all unique sequence names."""
        sequences = await populated_repo.get_sequences()
        assert set(sequences) == {"user-login", "checkout-flow"}

    @pytest.mark.asyncio
    async def test_get_for_element(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting steps involving a specific element."""
        web_app_steps = await populated_repo.get_for_element(
            ElementType.CONTAINER, "web-app"
        )
        assert len(web_app_steps) == 4  # login-1, login-2, checkout-1, checkout-2

    @pytest.mark.asyncio
    async def test_get_for_element_person(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting steps involving a person."""
        customer_steps = await populated_repo.get_for_element(
            ElementType.PERSON, "customer"
        )
        assert len(customer_steps) == 2  # login-1 and checkout-1

    @pytest.mark.asyncio
    async def test_get_step(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting a specific step by sequence and number."""
        step = await populated_repo.get_step("user-login", 2)
        assert step is not None
        assert step.slug == "login-2"
        assert step.source_slug == "web-app"

    @pytest.mark.asyncio
    async def test_get_step_nonexistent(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting a nonexistent step returns None."""
        step = await populated_repo.get_step("user-login", 99)
        assert step is None

    @pytest.mark.asyncio
    async def test_get_by_docname(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test getting steps by docname."""
        steps = await populated_repo.get_by_docname("sequences/login")
        assert len(steps) == 3

    @pytest.mark.asyncio
    async def test_clear_by_docname(
        self, populated_repo: MemoryDynamicStepRepository
    ) -> None:
        """Test clearing steps by docname."""
        count = await populated_repo.clear_by_docname("sequences/login")
        assert count == 3

        remaining = await populated_repo.list_all()
        assert len(remaining) == 2

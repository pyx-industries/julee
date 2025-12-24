"""Tests for ListBoundedContextsUseCase."""

import pytest

from julee.core.entities.bounded_context import BoundedContext, StructuralMarkers
from julee.core.use_cases import (
    ListBoundedContextsRequest,
    ListBoundedContextsResponse,
    ListBoundedContextsUseCase,
)


class MockBoundedContextRepository:
    """Mock repository for testing."""

    def __init__(self, contexts: list[BoundedContext] | None = None):
        self._contexts = contexts or []

    async def list_all(self) -> list[BoundedContext]:
        return self._contexts

    async def get(self, slug: str) -> BoundedContext | None:
        for ctx in self._contexts:
            if ctx.slug == slug:
                return ctx
        return None


class TestListBoundedContextsUseCase:
    """Tests for ListBoundedContextsUseCase."""

    @pytest.mark.asyncio
    async def test_returns_all_contexts_from_repository(self):
        """Should return all contexts from repository."""
        contexts = [
            BoundedContext(
                slug="billing",
                path="/src/julee/billing",
                markers=StructuralMarkers(has_domain_models=True),
            ),
            BoundedContext(
                slug="inventory",
                path="/src/julee/inventory",
                markers=StructuralMarkers(has_domain_use_cases=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = ListBoundedContextsUseCase(repo)

        response = await use_case.execute(ListBoundedContextsRequest())

        assert len(response.bounded_contexts) == 2
        slugs = {c.slug for c in response.bounded_contexts}
        assert slugs == {"billing", "inventory"}

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_contexts(self):
        """Should return empty list when repository has no contexts."""
        repo = MockBoundedContextRepository([])
        use_case = ListBoundedContextsUseCase(repo)

        response = await use_case.execute(ListBoundedContextsRequest())

        assert response.bounded_contexts == []

    @pytest.mark.asyncio
    async def test_response_is_correct_type(self):
        """Should return ListBoundedContextsResponse."""
        repo = MockBoundedContextRepository([])
        use_case = ListBoundedContextsUseCase(repo)

        response = await use_case.execute(ListBoundedContextsRequest())

        assert isinstance(response, ListBoundedContextsResponse)

    @pytest.mark.asyncio
    async def test_preserves_context_metadata(self):
        """Should preserve all context metadata."""
        context = BoundedContext(
            slug="hcd",
            path="/src/julee/hcd",
            is_viewpoint=True,
            is_contrib=False,
            markers=StructuralMarkers(
                has_domain_models=True,
                has_domain_repositories=True,
                has_domain_use_cases=True,
            ),
        )
        repo = MockBoundedContextRepository([context])
        use_case = ListBoundedContextsUseCase(repo)

        response = await use_case.execute(ListBoundedContextsRequest())

        result = response.bounded_contexts[0]
        assert result.slug == "hcd"
        assert result.is_viewpoint is True
        assert result.markers.has_domain_models is True
        assert result.markers.has_domain_repositories is True
        assert result.markers.has_domain_use_cases is True

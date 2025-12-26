"""Tests for GetBoundedContextCodeUseCase."""

from pathlib import Path

import pytest

from julee.core.entities.bounded_context import BoundedContext, StructuralMarkers
from julee.core.use_cases.code_artifact.get_bounded_context_code import (
    GetBoundedContextCodeRequest,
    GetBoundedContextCodeResponse,
    GetBoundedContextCodeUseCase,
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


def create_bounded_context_files(tmp_path: Path, name: str) -> Path:
    """Create a bounded context directory structure with files."""
    ctx_dir = tmp_path / name
    ctx_dir.mkdir()

    # Create __init__.py with docstring
    (ctx_dir / "__init__.py").write_text(f'"""{name.title()} bounded context."""')

    # Create entities directory with entity
    entities_dir = ctx_dir / "entities"
    entities_dir.mkdir()
    (entities_dir / "document.py").write_text('''
class Document:
    """A document entity."""
    name: str
    content: str
''')

    # Create use_cases directory with use case
    use_cases_dir = ctx_dir / "use_cases"
    use_cases_dir.mkdir()
    (use_cases_dir / "create_document.py").write_text('''
class CreateDocumentRequest:
    """Request for creating a document."""
    name: str

class CreateDocumentResponse:
    """Response from creating a document."""
    document_id: str

class CreateDocumentUseCase:
    """Use case for creating documents."""
    async def execute(self, request: CreateDocumentRequest) -> CreateDocumentResponse:
        pass
''')

    # Create repositories directory
    repos_dir = ctx_dir / "repositories"
    repos_dir.mkdir()
    (repos_dir / "document.py").write_text('''
class DocumentRepository:
    """Repository protocol for documents."""
    async def save(self, document): pass
    async def get(self, id: str): pass
''')

    return ctx_dir


class TestGetBoundedContextCodeUseCase:
    """Tests for GetBoundedContextCodeUseCase."""

    @pytest.mark.asyncio
    async def test_returns_code_info_for_all_contexts(self, tmp_path: Path):
        """Should return code info for all bounded contexts."""
        # Create two bounded contexts
        ctx1_path = create_bounded_context_files(tmp_path, "billing")
        ctx2_path = create_bounded_context_files(tmp_path, "inventory")

        contexts = [
            BoundedContext(
                slug="billing",
                path=str(ctx1_path),
                markers=StructuralMarkers(has_domain_models=True),
            ),
            BoundedContext(
                slug="inventory",
                path=str(ctx2_path),
                markers=StructuralMarkers(has_domain_models=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(GetBoundedContextCodeRequest())

        assert response.context_count == 2
        slugs = {c.slug for c in response.contexts}
        assert slugs == {"billing", "inventory"}

    @pytest.mark.asyncio
    async def test_returns_code_info_for_specific_context(self, tmp_path: Path):
        """Should return code info for a specific bounded context."""
        ctx_path = create_bounded_context_files(tmp_path, "billing")

        contexts = [
            BoundedContext(
                slug="billing",
                path=str(ctx_path),
                markers=StructuralMarkers(has_domain_models=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(
            GetBoundedContextCodeRequest(bounded_context="billing")
        )

        assert response.context_count == 1
        assert response.contexts[0].slug == "billing"

    @pytest.mark.asyncio
    async def test_returns_empty_for_nonexistent_context(self, tmp_path: Path):
        """Should return empty response for nonexistent context."""
        repo = MockBoundedContextRepository([])
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(
            GetBoundedContextCodeRequest(bounded_context="nonexistent")
        )

        assert response.context_count == 0

    @pytest.mark.asyncio
    async def test_extracts_entities(self, tmp_path: Path):
        """Should extract entity classes from bounded context."""
        ctx_path = create_bounded_context_files(tmp_path, "documents")

        contexts = [
            BoundedContext(
                slug="documents",
                path=str(ctx_path),
                markers=StructuralMarkers(has_domain_models=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(GetBoundedContextCodeRequest())

        ctx_info = response.contexts[0]
        entity_names = [e.name for e in ctx_info.entities]
        assert "Document" in entity_names

    @pytest.mark.asyncio
    async def test_extracts_use_cases(self, tmp_path: Path):
        """Should extract use case classes from bounded context."""
        ctx_path = create_bounded_context_files(tmp_path, "documents")

        contexts = [
            BoundedContext(
                slug="documents",
                path=str(ctx_path),
                markers=StructuralMarkers(has_domain_use_cases=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(GetBoundedContextCodeRequest())

        ctx_info = response.contexts[0]
        use_case_names = [u.name for u in ctx_info.use_cases]
        assert "CreateDocumentUseCase" in use_case_names

    @pytest.mark.asyncio
    async def test_extracts_requests_and_responses(self, tmp_path: Path):
        """Should extract request and response classes from bounded context."""
        ctx_path = create_bounded_context_files(tmp_path, "documents")

        contexts = [
            BoundedContext(
                slug="documents",
                path=str(ctx_path),
                markers=StructuralMarkers(has_domain_use_cases=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(GetBoundedContextCodeRequest())

        ctx_info = response.contexts[0]
        request_names = [r.name for r in ctx_info.requests]
        response_names = [r.name for r in ctx_info.responses]
        assert "CreateDocumentRequest" in request_names
        assert "CreateDocumentResponse" in response_names

    @pytest.mark.asyncio
    async def test_extracts_repository_protocols(self, tmp_path: Path):
        """Should extract repository protocol classes from bounded context."""
        ctx_path = create_bounded_context_files(tmp_path, "documents")

        contexts = [
            BoundedContext(
                slug="documents",
                path=str(ctx_path),
                markers=StructuralMarkers(has_domain_repositories=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(GetBoundedContextCodeRequest())

        ctx_info = response.contexts[0]
        repo_names = [r.name for r in ctx_info.repository_protocols]
        assert "DocumentRepository" in repo_names

    @pytest.mark.asyncio
    async def test_response_get_context_helper(self, tmp_path: Path):
        """Should be able to get context by slug from response."""
        ctx_path = create_bounded_context_files(tmp_path, "billing")

        contexts = [
            BoundedContext(
                slug="billing",
                path=str(ctx_path),
                markers=StructuralMarkers(has_domain_models=True),
            ),
        ]
        repo = MockBoundedContextRepository(contexts)
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(GetBoundedContextCodeRequest())

        ctx_info = response.get_context("billing")
        assert ctx_info is not None
        assert ctx_info.slug == "billing"

        missing = response.get_context("nonexistent")
        assert missing is None

    @pytest.mark.asyncio
    async def test_response_is_correct_type(self, tmp_path: Path):
        """Should return GetBoundedContextCodeResponse."""
        repo = MockBoundedContextRepository([])
        use_case = GetBoundedContextCodeUseCase(repo)

        response = await use_case.execute(GetBoundedContextCodeRequest())

        assert isinstance(response, GetBoundedContextCodeResponse)

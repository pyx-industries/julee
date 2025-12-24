"""Request/Response doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.shared.domain.use_cases import (
    ListCodeArtifactsRequest,
    ListRequestsUseCase,
    ListResponsesUseCase,
)
from julee.shared.repositories.introspection import FilesystemBoundedContextRepository


def create_bounded_context(base_path: Path, name: str, layers: list[str] | None = None):
    """Helper to create a bounded context directory structure."""
    ctx_path = base_path / name
    ctx_path.mkdir(parents=True)
    (ctx_path / "__init__.py").touch()
    for layer in (layers or ["models", "use_cases"]):
        layer_path = ctx_path / "domain" / layer
        layer_path.mkdir(parents=True)
    return ctx_path


def create_solution(tmp_path: Path) -> Path:
    """Create a solution root with standard structure."""
    root = tmp_path / "src" / "julee"
    root.mkdir(parents=True)
    return root


def write_requests_file(ctx_path: Path, requests: list[tuple[str, list[str]]]) -> None:
    """Write request classes to requests.py.

    Args:
        ctx_path: Path to bounded context
        requests: List of (class_name, field_names) tuples
    """
    use_cases_dir = ctx_path / "domain" / "use_cases"
    use_cases_dir.mkdir(parents=True, exist_ok=True)

    content = '''"""Request models."""

from pydantic import BaseModel

'''
    for class_name, fields in requests:
        field_defs = "\n".join(f"    {f}: str" for f in fields) if fields else "    pass"
        content += f'''
class {class_name}(BaseModel):
    """{class_name} request."""
{field_defs}

'''
    (use_cases_dir / "requests.py").write_text(content)


def write_responses_file(ctx_path: Path, responses: list[tuple[str, list[str]]]) -> None:
    """Write response classes to responses.py.

    Args:
        ctx_path: Path to bounded context
        responses: List of (class_name, field_names) tuples
    """
    use_cases_dir = ctx_path / "domain" / "use_cases"
    use_cases_dir.mkdir(parents=True, exist_ok=True)

    content = '''"""Response models."""

from pydantic import BaseModel

'''
    for class_name, fields in responses:
        field_defs = "\n".join(f"    {f}: str" for f in fields) if fields else "    pass"
        content += f'''
class {class_name}(BaseModel):
    """{class_name} response."""
{field_defs}

'''
    (use_cases_dir / "responses.py").write_text(content)


# =============================================================================
# DOCTRINE: Request Naming
# =============================================================================


class TestRequestNaming:
    """Doctrine about request naming conventions."""

    @pytest.mark.asyncio
    async def test_request_MUST_end_with_Request_suffix(self, tmp_path: Path):
        """A top-level request class MUST end with 'Request' suffix."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_requests_file(ctx, [("CreateInvoiceRequest", ["invoice_id"])])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.name.endswith("Request"), \
                f"'{artifact.artifact.name}' MUST end with 'Request'"

    @pytest.mark.asyncio
    async def test_nested_compound_type_MUST_end_with_Item_suffix(self, tmp_path: Path):
        """A nested compound type in requests.py MUST end with 'Item' suffix."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")

        # Write a request with a nested Item type
        use_cases_dir = ctx / "domain" / "use_cases"
        use_cases_dir.mkdir(parents=True, exist_ok=True)
        content = '''"""Request models."""

from pydantic import BaseModel


class LineItem(BaseModel):
    """Nested item representing an invoice line."""
    product_id: str
    quantity: int


class CreateInvoiceRequest(BaseModel):
    """CreateInvoiceRequest request."""
    customer_id: str
    items: list[LineItem]

'''
        (use_cases_dir / "requests.py").write_text(content)

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            name = artifact.artifact.name
            assert name.endswith("Request") or name.endswith("Item"), \
                f"'{name}' MUST end with 'Request' or 'Item'"

    @pytest.mark.asyncio
    async def test_request_MUST_have_docstring(self, tmp_path: Path):
        """A request class MUST have a docstring."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_requests_file(ctx, [("CreateInvoiceRequest", [])])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.docstring, \
                f"'{artifact.artifact.name}' MUST have a docstring"


# =============================================================================
# DOCTRINE: Response Naming
# =============================================================================


class TestResponseNaming:
    """Doctrine about response naming conventions."""

    @pytest.mark.asyncio
    async def test_response_MUST_end_with_Response_suffix(self, tmp_path: Path):
        """A response class MUST end with 'Response' suffix."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_responses_file(ctx, [("CreateInvoiceResponse", ["invoice"])])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.name.endswith("Response"), \
                f"'{artifact.artifact.name}' MUST end with 'Response'"

    @pytest.mark.asyncio
    async def test_response_MUST_have_docstring(self, tmp_path: Path):
        """A response class MUST have a docstring."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_responses_file(ctx, [("CreateInvoiceResponse", [])])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.docstring, \
                f"'{artifact.artifact.name}' MUST have a docstring"


# =============================================================================
# DOCTRINE: Request Structure
# =============================================================================


class TestRequestStructure:
    """Doctrine about request structure."""

    @pytest.mark.asyncio
    async def test_request_MUST_inherit_from_BaseModel(self, tmp_path: Path):
        """A request class MUST inherit from BaseModel."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_requests_file(ctx, [("CreateInvoiceRequest", [])])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert "BaseModel" in artifact.artifact.bases, \
                f"'{artifact.artifact.name}' MUST inherit from BaseModel"

    @pytest.mark.asyncio
    async def test_request_fields_MUST_have_type_annotations(self, tmp_path: Path):
        """Request fields MUST have type annotations."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_requests_file(ctx, [("CreateInvoiceRequest", ["customer_id", "amount"])])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            for field in artifact.artifact.fields:
                assert field.type_annotation, \
                    f"Field '{field.name}' in '{artifact.artifact.name}' MUST have type annotation"


# =============================================================================
# DOCTRINE: Response Structure
# =============================================================================


class TestResponseStructure:
    """Doctrine about response structure."""

    @pytest.mark.asyncio
    async def test_response_MUST_inherit_from_BaseModel(self, tmp_path: Path):
        """A response class MUST inherit from BaseModel."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_responses_file(ctx, [("CreateInvoiceResponse", [])])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert "BaseModel" in artifact.artifact.bases, \
                f"'{artifact.artifact.name}' MUST inherit from BaseModel"

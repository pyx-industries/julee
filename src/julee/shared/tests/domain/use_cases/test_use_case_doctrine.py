"""Use case doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.shared.domain.use_cases import (
    ListCodeArtifactsRequest,
    ListRequestsUseCase,
    ListUseCasesUseCase,
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


def write_use_case(ctx_path: Path, name: str, has_execute: bool = True) -> None:
    """Write a use case class to the context."""
    use_cases_dir = ctx_path / "domain" / "use_cases"
    use_cases_dir.mkdir(parents=True, exist_ok=True)

    execute_method = """
    async def execute(self, request):
        pass
""" if has_execute else ""

    content = f'''"""Use case module."""


class {name}:
    """{name} use case."""
{execute_method}
'''
    (use_cases_dir / f"{name.lower()}.py").write_text(content)


def write_request(ctx_path: Path, name: str) -> None:
    """Write a request class to the context."""
    use_cases_dir = ctx_path / "domain" / "use_cases"
    use_cases_dir.mkdir(parents=True, exist_ok=True)

    requests_file = use_cases_dir / "requests.py"
    existing = requests_file.read_text() if requests_file.exists() else '"""Request models."""\n\nfrom pydantic import BaseModel\n\n'

    content = existing + f'''
class {name}(BaseModel):
    """{name} request."""
    pass
'''
    requests_file.write_text(content)


# =============================================================================
# DOCTRINE: Use Case Naming
# =============================================================================


class TestUseCaseNaming:
    """Doctrine about use case naming conventions."""

    @pytest.mark.asyncio
    async def test_use_case_MUST_end_with_UseCase_suffix(self, tmp_path: Path):
        """A use case class MUST end with 'UseCase' suffix."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_use_case(ctx, "CreateInvoiceUseCase")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.name.endswith("UseCase"), \
                f"'{artifact.artifact.name}' MUST end with 'UseCase'"

    @pytest.mark.asyncio
    async def test_use_case_MUST_have_docstring(self, tmp_path: Path):
        """A use case class MUST have a docstring."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_use_case(ctx, "CreateInvoiceUseCase")

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.docstring, \
                f"'{artifact.artifact.name}' MUST have a docstring"


# =============================================================================
# DOCTRINE: Use Case Contracts
# =============================================================================


class TestUseCaseContracts:
    """Doctrine about use case contracts (request/response pairing)."""

    @pytest.mark.asyncio
    async def test_use_case_MUST_have_matching_request(self, tmp_path: Path):
        """A use case MUST have a matching {Prefix}Request class."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_use_case(ctx, "CreateInvoiceUseCase")
        write_request(ctx, "CreateInvoiceRequest")

        repo = FilesystemBoundedContextRepository(tmp_path)

        # Get use cases
        uc_use_case = ListUseCasesUseCase(repo)
        uc_response = await uc_use_case.execute(ListCodeArtifactsRequest())

        # Get requests
        req_use_case = ListRequestsUseCase(repo)
        req_response = await req_use_case.execute(ListCodeArtifactsRequest())

        request_names = {a.artifact.name for a in req_response.artifacts}

        for artifact in uc_response.artifacts:
            if artifact.artifact.name.endswith("UseCase"):
                prefix = artifact.artifact.name[:-7]  # Strip "UseCase"
                expected_request = f"{prefix}Request"
                assert expected_request in request_names, \
                    f"'{artifact.artifact.name}' MUST have matching '{expected_request}'"

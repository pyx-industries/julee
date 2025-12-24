"""Protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.shared.domain.use_cases import (
    ListCodeArtifactsRequest,
    ListRepositoryProtocolsUseCase,
    ListServiceProtocolsUseCase,
)
from julee.shared.repositories.introspection import FilesystemBoundedContextRepository


def create_bounded_context(base_path: Path, name: str, layers: list[str] | None = None):
    """Helper to create a bounded context directory structure."""
    ctx_path = base_path / name
    ctx_path.mkdir(parents=True)
    (ctx_path / "__init__.py").touch()
    for layer in (layers or ["models", "use_cases", "repositories", "services"]):
        layer_path = ctx_path / "domain" / layer
        layer_path.mkdir(parents=True)
    return ctx_path


def create_solution(tmp_path: Path) -> Path:
    """Create a solution root with standard structure."""
    root = tmp_path / "src" / "julee"
    root.mkdir(parents=True)
    return root


def write_repository_protocol(ctx_path: Path, name: str, methods: list[str] | None = None) -> None:
    """Write a repository protocol to the context.

    Args:
        ctx_path: Path to bounded context
        name: Protocol class name
        methods: List of method names
    """
    repos_dir = ctx_path / "domain" / "repositories"
    repos_dir.mkdir(parents=True, exist_ok=True)

    method_defs = ""
    for method in (methods or []):
        method_defs += f"""
    async def {method}(self) -> None:
        \"\"\"Abstract method.\"\"\"
        ...
"""

    content = f'''"""Repository protocol module."""

from typing import Protocol


class {name}(Protocol):
    """{name} protocol."""
{method_defs if method_defs else "    pass"}
'''
    (repos_dir / f"{name.lower()}.py").write_text(content)


def write_service_protocol(ctx_path: Path, name: str, methods: list[str] | None = None) -> None:
    """Write a service protocol to the context.

    Args:
        ctx_path: Path to bounded context
        name: Protocol class name
        methods: List of method names
    """
    services_dir = ctx_path / "domain" / "services"
    services_dir.mkdir(parents=True, exist_ok=True)

    method_defs = ""
    for method in (methods or []):
        method_defs += f"""
    async def {method}(self) -> None:
        \"\"\"Abstract method.\"\"\"
        ...
"""

    content = f'''"""Service protocol module."""

from typing import Protocol


class {name}(Protocol):
    """{name} protocol."""
{method_defs if method_defs else "    pass"}
'''
    (services_dir / f"{name.lower()}.py").write_text(content)


# =============================================================================
# DOCTRINE: Repository Protocol Naming
# =============================================================================


class TestRepositoryProtocolNaming:
    """Doctrine about repository protocol naming conventions."""

    @pytest.mark.asyncio
    async def test_repository_protocol_MUST_end_with_Repository(self, tmp_path: Path):
        """A repository protocol MUST end with 'Repository' suffix."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_repository_protocol(ctx, "InvoiceRepository", ["get", "save"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.name.endswith("Repository"), \
                f"'{artifact.artifact.name}' MUST end with 'Repository'"

    @pytest.mark.asyncio
    async def test_repository_protocol_MUST_have_docstring(self, tmp_path: Path):
        """A repository protocol MUST have a docstring."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_repository_protocol(ctx, "InvoiceRepository", ["get"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.docstring, \
                f"'{artifact.artifact.name}' MUST have a docstring"


# =============================================================================
# DOCTRINE: Repository Protocol Structure
# =============================================================================


class TestRepositoryProtocolStructure:
    """Doctrine about repository protocol structure."""

    @pytest.mark.asyncio
    async def test_repository_protocol_MUST_inherit_from_Protocol(self, tmp_path: Path):
        """A repository protocol MUST inherit from Protocol."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_repository_protocol(ctx, "InvoiceRepository", ["get"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert "Protocol" in artifact.artifact.bases, \
                f"'{artifact.artifact.name}' MUST inherit from Protocol"


# =============================================================================
# DOCTRINE: Service Protocol Naming
# =============================================================================


class TestServiceProtocolNaming:
    """Doctrine about service protocol naming conventions."""

    @pytest.mark.asyncio
    async def test_service_protocol_MUST_end_with_Service(self, tmp_path: Path):
        """A service protocol MUST end with 'Service' suffix."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_service_protocol(ctx, "PaymentService", ["process_payment"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.name.endswith("Service"), \
                f"'{artifact.artifact.name}' MUST end with 'Service'"

    @pytest.mark.asyncio
    async def test_service_protocol_MUST_have_docstring(self, tmp_path: Path):
        """A service protocol MUST have a docstring."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_service_protocol(ctx, "PaymentService", ["process_payment"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.docstring, \
                f"'{artifact.artifact.name}' MUST have a docstring"


# =============================================================================
# DOCTRINE: Service Protocol Structure
# =============================================================================


class TestServiceProtocolStructure:
    """Doctrine about service protocol structure."""

    @pytest.mark.asyncio
    async def test_service_protocol_MUST_inherit_from_Protocol(self, tmp_path: Path):
        """A service protocol MUST inherit from Protocol."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_service_protocol(ctx, "PaymentService", ["process_payment"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert "Protocol" in artifact.artifact.bases, \
                f"'{artifact.artifact.name}' MUST inherit from Protocol"

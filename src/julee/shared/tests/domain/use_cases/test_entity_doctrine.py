"""Entity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.shared.domain.use_cases import (
    ListCodeArtifactsRequest,
    ListEntitiesUseCase,
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


def write_entity(ctx_path: Path, name: str, fields: list[str] | None = None) -> None:
    """Write an entity class to the context.

    Args:
        ctx_path: Path to bounded context
        name: Entity class name
        fields: List of field names (all typed as str)
    """
    models_dir = ctx_path / "domain" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    field_defs = "\n".join(f"    {f}: str" for f in (fields or [])) if fields else "    pass"

    content = f'''"""Entity module."""

from pydantic import BaseModel


class {name}(BaseModel):
    """{name} entity."""
{field_defs}
'''
    (models_dir / f"{name.lower()}.py").write_text(content)


# =============================================================================
# DOCTRINE: Entity Naming
# =============================================================================


class TestEntityNaming:
    """Doctrine about entity naming conventions."""

    @pytest.mark.asyncio
    async def test_entity_MUST_be_PascalCase(self, tmp_path: Path):
        """An entity class name MUST be PascalCase."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id", "amount"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            name = artifact.artifact.name
            # PascalCase: starts with uppercase, no underscores
            assert name[0].isupper(), \
                f"'{name}' MUST start with uppercase letter"
            assert "_" not in name, \
                f"'{name}' MUST NOT contain underscores (use PascalCase)"

    @pytest.mark.asyncio
    async def test_entity_MUST_NOT_end_with_UseCase(self, tmp_path: Path):
        """An entity class name MUST NOT end with 'UseCase'."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert not artifact.artifact.name.endswith("UseCase"), \
                f"'{artifact.artifact.name}' MUST NOT end with 'UseCase'"

    @pytest.mark.asyncio
    async def test_entity_MUST_NOT_end_with_Request(self, tmp_path: Path):
        """An entity class name MUST NOT end with 'Request'."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert not artifact.artifact.name.endswith("Request"), \
                f"'{artifact.artifact.name}' MUST NOT end with 'Request'"

    @pytest.mark.asyncio
    async def test_entity_MUST_NOT_end_with_Response(self, tmp_path: Path):
        """An entity class name MUST NOT end with 'Response'."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert not artifact.artifact.name.endswith("Response"), \
                f"'{artifact.artifact.name}' MUST NOT end with 'Response'"


# =============================================================================
# DOCTRINE: Entity Structure
# =============================================================================


class TestEntityStructure:
    """Doctrine about entity structure."""

    @pytest.mark.asyncio
    async def test_entity_MUST_have_docstring(self, tmp_path: Path):
        """An entity class MUST have a docstring."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert artifact.artifact.docstring, \
                f"'{artifact.artifact.name}' MUST have a docstring"

    @pytest.mark.asyncio
    async def test_entity_MUST_inherit_from_BaseModel(self, tmp_path: Path):
        """An entity class MUST inherit from BaseModel."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert "BaseModel" in artifact.artifact.bases, \
                f"'{artifact.artifact.name}' MUST inherit from BaseModel"

    @pytest.mark.asyncio
    async def test_entity_SHOULD_have_at_least_one_field(self, tmp_path: Path):
        """An entity class SHOULD have at least one field."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id", "amount"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            assert len(artifact.artifact.fields) >= 1, \
                f"'{artifact.artifact.name}' SHOULD have at least one field"

    @pytest.mark.asyncio
    async def test_entity_fields_MUST_have_type_annotations(self, tmp_path: Path):
        """Entity fields MUST have type annotations."""
        root = create_solution(tmp_path)
        ctx = create_bounded_context(root, "billing")
        write_entity(ctx, "Invoice", ["invoice_id", "amount"])

        repo = FilesystemBoundedContextRepository(tmp_path)
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        for artifact in response.artifacts:
            for field in artifact.artifact.fields:
                assert field.type_annotation, \
                    f"Field '{field.name}' in '{artifact.artifact.name}' MUST have type annotation"

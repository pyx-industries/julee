"""Request doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

Naming conventions for classes in requests.py:
  - *Request: Top-level use case input (e.g., CreateJourneyRequest)
  - *Item: Nested compound type for complex attributes (e.g., JourneyStepItem)

Item types are used for list attributes within requests that need their own
validation and to_domain_model() conversion. They are NOT top-level requests.
"""

import importlib

import pytest
from pydantic import BaseModel

from julee.core.doctrine_constants import (
    ITEM_SUFFIX,
    REQUEST_BASE,
    REQUEST_SUFFIX,
)
from julee.core.use_cases import (
    ListCodeArtifactsRequest,
    ListRequestsUseCase,
)


def _resolve_class(import_path: str, file_path: str, class_name: str) -> type | None:
    """Resolve a class by importing its module at runtime.

    Args:
        import_path: BC's Python import path (e.g., 'julee.hcd', 'julee.contrib.ceap')
        file_path: Relative file path within use_cases (e.g., 'crud.py', 'story/get.py')
        class_name: Name of the class to resolve

    Returns None if the class cannot be resolved (import error, etc).
    """
    try:
        # Convert file path to module suffix: story/get.py -> story.get
        file_module = file_path.replace(".py", "").replace("/", ".")

        # Build full module path: {import_path}.use_cases.{file_module}
        module_path = f"{import_path}.use_cases.{file_module}"

        module = importlib.import_module(module_path)
        return getattr(module, class_name, None)
    except Exception:
        return None


class TestRequestNaming:
    """Doctrine about request naming conventions."""

    @pytest.mark.asyncio
    async def test_all_requests_MUST_end_with_Request_or_Item(self, repo):
        """All request class names MUST end with 'Request' or 'Item'.

        - *Request: Top-level use case input
        - *Item: Nested compound type for complex list attributes
        """
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning requests
        assert len(response.artifacts) > 0, "No requests found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            if not (name.endswith(REQUEST_SUFFIX) or name.endswith(ITEM_SUFFIX)):
                violations.append(f"{artifact.bounded_context}.{name}")

        assert not violations, (
            f"Classes in requests.py must end with '{REQUEST_SUFFIX}' or '{ITEM_SUFFIX}':\n"
            + "\n".join(violations)
        )


class TestRequestDocumentation:
    """Doctrine about request documentation."""

    @pytest.mark.asyncio
    async def test_all_requests_MUST_have_docstring(self, repo):
        """All request classes MUST have a docstring."""
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Requests missing docstrings:\n" + "\n".join(violations)


class TestRequestInheritance:
    """Doctrine about request inheritance."""

    @pytest.mark.asyncio
    async def test_all_requests_MUST_inherit_from_BaseModel(self, repo):
        """All request classes MUST inherit from BaseModel.

        Uses runtime inspection (issubclass) to support inherited classes from
        generic base classes like generic_crud.GetRequest.
        """
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Build slug -> import_path mapping from repo
        bounded_contexts = await repo.list_all()
        import_paths = {bc.slug: bc.import_path for bc in bounded_contexts}

        violations = []
        for artifact in response.artifacts:
            # Try runtime inspection first (supports inherited classes)
            bc_import_path = import_paths.get(artifact.bounded_context)
            if bc_import_path:
                cls = _resolve_class(
                    bc_import_path, artifact.artifact.file, artifact.artifact.name
                )
            else:
                cls = None

            if cls is not None:
                inherits_basemodel = issubclass(cls, BaseModel)
            else:
                # Fall back to AST-parsed bases if class can't be resolved
                inherits_basemodel = REQUEST_BASE in artifact.artifact.bases

            if not inherits_basemodel:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), f"Requests not inheriting from {REQUEST_BASE}:\n" + "\n".join(violations)


class TestRequestTypeAnnotations:
    """Doctrine about request type annotations."""

    @pytest.mark.asyncio
    async def test_all_request_fields_MUST_have_type_annotations(self, repo):
        """All request fields MUST have type annotations."""
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            for field in artifact.artifact.fields:
                if not field.type_annotation:
                    violations.append(
                        f"{artifact.bounded_context}.{artifact.artifact.name}.{field.name}"
                    )

        assert not violations, "Request fields missing type annotations:\n" + "\n".join(
            violations
        )

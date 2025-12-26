"""Response doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import importlib

import pytest
from pydantic import BaseModel

from julee.core.doctrine_constants import (
    ITEM_SUFFIX,
    RESPONSE_BASE,
    RESPONSE_SUFFIX,
)
from julee.core.use_cases import (
    ListCodeArtifactsRequest,
    ListResponsesUseCase,
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


class TestResponseNaming:
    """Doctrine about response naming conventions."""

    @pytest.mark.asyncio
    async def test_all_responses_MUST_end_with_Response_or_Item(self, repo):
        """All response class names MUST end with 'Response' or 'Item'."""
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning responses
        assert (
            len(response.artifacts) > 0
        ), "No responses found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            if not (name.endswith(RESPONSE_SUFFIX) or name.endswith(ITEM_SUFFIX)):
                violations.append(f"{artifact.bounded_context}.{name}")

        assert not violations, (
            f"Classes in responses.py must end with '{RESPONSE_SUFFIX}' or '{ITEM_SUFFIX}':\n"
            + "\n".join(violations)
        )


class TestResponseDocumentation:
    """Doctrine about response documentation."""

    @pytest.mark.asyncio
    async def test_all_responses_MUST_have_docstring(self, repo):
        """All response classes MUST have a docstring."""
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Responses missing docstrings:\n" + "\n".join(violations)


class TestResponseInheritance:
    """Doctrine about response inheritance."""

    @pytest.mark.asyncio
    async def test_all_responses_MUST_inherit_from_BaseModel(self, repo):
        """All response classes MUST inherit from BaseModel.

        Uses runtime inspection (issubclass) to support inherited classes from
        generic base classes like generic_crud.GetResponse.
        """
        use_case = ListResponsesUseCase(repo)
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
                inherits_basemodel = RESPONSE_BASE in artifact.artifact.bases

            if not inherits_basemodel:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), f"Responses not inheriting from {RESPONSE_BASE}:\n" + "\n".join(violations)

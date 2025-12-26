"""UseCase doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import importlib

import pytest

from julee.core.doctrine_constants import (
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
    USE_CASE_SUFFIX,
)

# Generic/abstract base classes that don't require matching Request/Response
GENERIC_BASE_CLASSES = {
    "FilterableListUseCase",  # Generic base for list use cases with filtering
}

from julee.core.use_cases.code_artifact.list_requests import ListRequestsUseCase
from julee.core.use_cases.code_artifact.list_responses import ListResponsesUseCase
from julee.core.use_cases.code_artifact.list_use_cases import ListUseCasesUseCase
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest


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


class TestUseCaseNaming:
    """Doctrine about use case naming conventions."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_end_with_UseCase(self, repo):
        """All use case class names MUST end with 'UseCase'."""
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning use cases
        assert (
            len(response.artifacts) > 0
        ), "No use cases found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.name.endswith(USE_CASE_SUFFIX):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert (
            not violations
        ), f"Use cases not ending with '{USE_CASE_SUFFIX}':\n" + "\n".join(violations)


class TestUseCaseDocumentation:
    """Doctrine about use case documentation."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_docstring(self, repo):
        """All use case classes MUST have a docstring."""
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Use cases missing docstrings:\n" + "\n".join(violations)


class TestUseCaseStructure:
    """Doctrine about use case structure."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_execute_method(self, repo):
        """All use cases MUST have an execute() method.

        The execute() method is the single entry point for use case invocation.
        It accepts a Request and returns a Response.

        Uses runtime inspection (hasattr) to support inherited methods from
        generic base classes like generic_crud.GetUseCase.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Build slug -> import_path mapping from repo
        bounded_contexts = await repo.list_all()
        import_paths = {bc.slug: bc.import_path for bc in bounded_contexts}

        violations = []
        for artifact in response.artifacts:
            # Try runtime inspection first (supports inherited methods)
            bc_import_path = import_paths.get(artifact.bounded_context)
            if bc_import_path:
                cls = _resolve_class(
                    bc_import_path, artifact.artifact.file, artifact.artifact.name
                )
            else:
                cls = None

            if cls is not None:
                has_execute = hasattr(cls, "execute") and callable(
                    getattr(cls, "execute", None)
                )
            else:
                # Fall back to AST-parsed methods if class can't be resolved
                method_names = [m.name for m in artifact.artifact.methods]
                has_execute = "execute" in method_names

            if not has_execute:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}: missing execute() method"
                )

        assert not violations, "Use cases missing execute() method:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_matching_request(self, repo):
        """All use cases MUST have a matching {Prefix}Request class."""
        uc_use_case = ListUseCasesUseCase(repo)
        uc_response = await uc_use_case.execute(ListCodeArtifactsRequest())

        req_use_case = ListRequestsUseCase(repo)
        req_response = await req_use_case.execute(ListCodeArtifactsRequest())

        # Build set of available requests per context
        requests_by_context: dict[str, set[str]] = {}
        for artifact in req_response.artifacts:
            ctx = artifact.bounded_context
            if ctx not in requests_by_context:
                requests_by_context[ctx] = set()
            requests_by_context[ctx].add(artifact.artifact.name)

        violations = []
        suffix_len = len(USE_CASE_SUFFIX)
        for artifact in uc_response.artifacts:
            name = artifact.artifact.name
            ctx = artifact.bounded_context
            # Skip generic base classes
            if name in GENERIC_BASE_CLASSES:
                continue
            if name.endswith(USE_CASE_SUFFIX):
                prefix = name[:-suffix_len]
                expected_request = f"{prefix}{REQUEST_SUFFIX}"
                available = requests_by_context.get(ctx, set())
                if expected_request not in available:
                    violations.append(f"{ctx}.{name}: missing {expected_request}")

        assert not violations, "Use cases missing matching requests:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_matching_response(self, repo):
        """All use cases MUST have a matching {Prefix}Response class.

        Use cases that return data MUST have a corresponding Response class
        in the same bounded context.
        """
        uc_use_case = ListUseCasesUseCase(repo)
        uc_response = await uc_use_case.execute(ListCodeArtifactsRequest())

        resp_use_case = ListResponsesUseCase(repo)
        resp_response = await resp_use_case.execute(ListCodeArtifactsRequest())

        # Build set of available responses per context
        responses_by_context: dict[str, set[str]] = {}
        for artifact in resp_response.artifacts:
            ctx = artifact.bounded_context
            if ctx not in responses_by_context:
                responses_by_context[ctx] = set()
            responses_by_context[ctx].add(artifact.artifact.name)

        violations = []
        suffix_len = len(USE_CASE_SUFFIX)
        for artifact in uc_response.artifacts:
            name = artifact.artifact.name
            ctx = artifact.bounded_context
            # Skip generic base classes
            if name in GENERIC_BASE_CLASSES:
                continue
            if name.endswith(USE_CASE_SUFFIX):
                prefix = name[:-suffix_len]
                expected_response = f"{prefix}{RESPONSE_SUFFIX}"
                available = responses_by_context.get(ctx, set())
                if expected_response not in available:
                    violations.append(f"{ctx}.{name}: missing {expected_response}")

        assert not violations, "Use cases missing matching responses:\n" + "\n".join(
            violations
        )

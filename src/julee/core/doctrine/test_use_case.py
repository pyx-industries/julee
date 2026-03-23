"""UseCase doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import importlib
import inspect
from pathlib import Path

import pytest

from julee.core.doctrine_constants import (
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
    USE_CASE_SUFFIX,
)
from julee.core.use_cases.code_artifact.list_requests import ListRequestsUseCase
from julee.core.use_cases.code_artifact.list_responses import ListResponsesUseCase
from julee.core.use_cases.code_artifact.list_use_cases import ListUseCasesUseCase
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest

# Generic/abstract base classes that don't require matching Request/Response
GENERIC_BASE_CLASSES = {
    "FilterableListUseCase",  # Generic base for list use cases with filtering
}


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

    @pytest.mark.asyncio
    async def test_execute_MUST_accept_matching_request(self, repo):
        """execute() MUST declare its first parameter as {Prefix}Request.

        Ensures the request class is part of the method's contract, not
        just present in the module.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        bounded_contexts = await repo.list_all()
        import_paths = {bc.slug: bc.import_path for bc in bounded_contexts}

        violations = []
        suffix_len = len(USE_CASE_SUFFIX)
        for artifact in response.artifacts:
            name = artifact.artifact.name
            ctx = artifact.bounded_context
            if name in GENERIC_BASE_CLASSES:
                continue
            if not name.endswith(USE_CASE_SUFFIX):
                continue

            prefix = name[:-suffix_len]
            expected_request = f"{prefix}{REQUEST_SUFFIX}"

            bc_import_path = import_paths.get(ctx)
            cls = (
                _resolve_class(bc_import_path, artifact.artifact.file, name)
                if bc_import_path
                else None
            )

            if cls is not None:
                execute = getattr(cls, "execute", None)
                if not callable(execute):
                    continue
                sig = inspect.signature(execute)
                params = [p for p in sig.parameters.values() if p.name != "self"]
                if not params:
                    violations.append(
                        f"{ctx}.{name}: execute() has no request parameter"
                    )
                    continue
                annotation = params[0].annotation
                actual_name = (
                    annotation.__name__
                    if hasattr(annotation, "__name__")
                    else str(annotation)
                )
            else:
                # Fall back to AST-parsed signature
                execute_method = next(
                    (m for m in artifact.artifact.methods if m.name == "execute"),
                    None,
                )
                if execute_method is None:
                    continue
                if not execute_method.parameters:
                    violations.append(
                        f"{ctx}.{name}: execute() has no request parameter"
                    )
                    continue
                actual_name = execute_method.parameters[0].type_annotation

            if actual_name != expected_request:
                violations.append(
                    f"{ctx}.{name}: execute() first parameter is '{actual_name}'"
                    f", expected '{expected_request}'"
                )

        assert not violations, "Use cases with wrong request type:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_use_cases_MUST_NOT_define_next_action(self, repo):
        """Use case classes MUST NOT define a next_action() method.

        next_action() is the superseded orchestration pattern (pre-ADR 003).
        Use cases should hand off domain conditions to injected handler
        services instead of computing what happens next themselves.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            method_names = [m.name for m in artifact.artifact.methods]
            if "next_action" in method_names:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert (
            not violations
        ), "Use cases defining forbidden next_action() method:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_execute_MUST_return_matching_response(self, repo):
        """execute() MUST declare its return type as {Prefix}Response.

        Ensures the response class is actually wired into execute(), not
        just present in the module.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        bounded_contexts = await repo.list_all()
        import_paths = {bc.slug: bc.import_path for bc in bounded_contexts}

        violations = []
        suffix_len = len(USE_CASE_SUFFIX)
        for artifact in response.artifacts:
            name = artifact.artifact.name
            ctx = artifact.bounded_context
            if name in GENERIC_BASE_CLASSES:
                continue
            if not name.endswith(USE_CASE_SUFFIX):
                continue

            prefix = name[:-suffix_len]
            expected_response = f"{prefix}{RESPONSE_SUFFIX}"

            bc_import_path = import_paths.get(ctx)
            cls = (
                _resolve_class(bc_import_path, artifact.artifact.file, name)
                if bc_import_path
                else None
            )

            if cls is not None:
                execute = getattr(cls, "execute", None)
                if not callable(execute):
                    continue
                sig = inspect.signature(execute)
                return_annotation = sig.return_annotation
                if return_annotation is inspect.Parameter.empty:
                    violations.append(
                        f"{ctx}.{name}: execute() has no return annotation"
                    )
                    continue
                actual_name = (
                    return_annotation.__name__
                    if hasattr(return_annotation, "__name__")
                    else str(return_annotation)
                )
            else:
                # Fall back to AST-parsed signature
                execute_method = next(
                    (m for m in artifact.artifact.methods if m.name == "execute"),
                    None,
                )
                if execute_method is None:
                    continue
                if not execute_method.return_type:
                    violations.append(
                        f"{ctx}.{name}: execute() has no return annotation"
                    )
                    continue
                actual_name = execute_method.return_type

            if actual_name != expected_response:
                violations.append(
                    f"{ctx}.{name}: execute() returns '{actual_name}'"
                    f", expected '{expected_response}'"
                )

        assert not violations, "Use cases with wrong return type:\n" + "\n".join(
            violations
        )


class TestExecutionAgnosticism:
    """Doctrine about execution-agnosticism in use cases (ADR 004).

    Use cases must not couple to specific execution frameworks like Temporal.
    Time and execution identity must be injected via service protocols
    instead of being accessed directly.
    """

    @pytest.mark.asyncio
    async def test_use_case_files_MUST_NOT_call_datetime_now(self, repo):
        """Use case files MUST NOT call datetime.now(), datetime.utcnow(), or datetime.today().

        Use cases needing the current time MUST inject ClockService and call
        clock_service.now() instead. Direct datetime calls couple the use case
        to system time, making deterministic testing impossible and breaking
        Temporal's replay guarantee.
        """
        contexts = await repo.list_all()

        forbidden_patterns = ["datetime.now(", "datetime.utcnow(", "datetime.today("]
        violations = []

        for ctx in contexts:
            for py_file in Path(ctx.path).rglob("*.py"):
                parts = py_file.parts
                if any(part == "tests" for part in parts):
                    continue
                if not any(part == "use_cases" for part in parts):
                    continue
                content = py_file.read_text()
                for pattern in forbidden_patterns:
                    if pattern in content:
                        violations.append(
                            f"{ctx.slug}/{py_file.relative_to(ctx.path)}: contains '{pattern}'"
                        )
                        break

        assert not violations, (
            "Use case files calling datetime directly (use ClockService instead):\n"
            + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_use_case_files_MUST_NOT_import_temporalio(self, repo):
        """Use case files MUST NOT import from temporalio.

        Temporal coupling belongs in the infrastructure layer (worker/pipelines),
        not use cases. Use cases must remain framework-agnostic so they can run
        in any execution context.
        """
        contexts = await repo.list_all()

        violations = []
        for ctx in contexts:
            for py_file in Path(ctx.path).rglob("*.py"):
                parts = py_file.parts
                if any(part == "tests" for part in parts):
                    continue
                if not any(part == "use_cases" for part in parts):
                    continue
                content = py_file.read_text()
                if "import temporalio" in content or "from temporalio" in content:
                    violations.append(
                        f"{ctx.slug}/{py_file.relative_to(ctx.path)}"
                    )

        assert (
            not violations
        ), "Use case files importing from temporalio:\n" + "\n".join(violations)

"""UseCase doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import warnings

import pytest

from julee.core.doctrine_constants import (
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
    USE_CASE_SUFFIX,
)
from julee.core.use_cases import (
    ListCodeArtifactsRequest,
    ListRequestsUseCase,
    ListResponsesUseCase,
    ListUseCasesUseCase,
)


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
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            method_names = [m.name for m in artifact.artifact.methods]
            if "execute" not in method_names:
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
    async def test_all_use_cases_SHOULD_have_matching_response(self, repo):
        """All use cases SHOULD have a matching {Prefix}Response class.

        Use cases that return data should have a corresponding Response class
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

        missing = []
        suffix_len = len(USE_CASE_SUFFIX)
        for artifact in uc_response.artifacts:
            name = artifact.artifact.name
            ctx = artifact.bounded_context
            if name.endswith(USE_CASE_SUFFIX):
                prefix = name[:-suffix_len]
                expected_response = f"{prefix}{RESPONSE_SUFFIX}"
                available = responses_by_context.get(ctx, set())
                if expected_response not in available:
                    missing.append(f"{ctx}.{name}: missing {expected_response}")

        # This is a SHOULD rule - log but don't fail
        if missing:
            warnings.warn(
                "Use cases missing matching Response classes (SHOULD have):\n"
                + "\n".join(missing),
                stacklevel=2,
            )

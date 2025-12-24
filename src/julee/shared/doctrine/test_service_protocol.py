"""ServiceProtocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import pytest

from julee.shared.doctrine_constants import (
    PROTOCOL_BASES,
    SERVICE_SUFFIX,
)
from julee.shared.parsers.ast import parse_python_classes
from julee.shared.use_cases import (
    ListCodeArtifactsRequest,
    ListRequestsUseCase,
    ListServiceProtocolsUseCase,
)


class TestServiceProtocolNaming:
    """Doctrine about service protocol naming conventions."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_end_with_Service(self, repo):
        """All service protocol names MUST end with 'Service'."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning service protocols
        assert (
            len(response.artifacts) > 0
        ), "No service protocols found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.name.endswith(SERVICE_SUFFIX):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert (
            not violations
        ), f"Service protocols not ending with '{SERVICE_SUFFIX}':\n" + "\n".join(
            violations
        )


class TestServiceProtocolDocumentation:
    """Doctrine about service protocol documentation."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_have_docstring(self, repo):
        """All service protocol classes MUST have a docstring."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Service protocols missing docstrings:\n" + "\n".join(
            violations
        )


class TestServiceProtocolInheritance:
    """Doctrine about service protocol inheritance."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_inherit_from_Protocol(self, repo):
        """All service protocols MUST inherit from Protocol."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            # Explicit check for Protocol or Protocol[T] generic
            has_protocol = any(
                base in PROTOCOL_BASES for base in artifact.artifact.bases
            )
            if not has_protocol:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), "Service protocols not inheriting from Protocol:\n" + "\n".join(violations)


# Service protocols exempt from the matching Request class rule.
# These are internal query/utility services that don't follow the formal use case pattern.
EXEMPT_SERVICE_PROTOCOLS = {
    "SuggestionContextService",  # Internal query service for suggestions
    "SemanticEvaluationService",  # Internal evaluation service
}


class TestServiceProtocolMethods:
    """Doctrine about service protocol methods."""

    @pytest.mark.asyncio
    async def test_all_service_protocol_methods_MUST_have_matching_request(
        self, repo, project_root
    ):
        """All service protocol methods MUST have a matching {MethodName}Request class.

        For each public method in a service protocol, there must be a corresponding
        Request class in the same bounded context's requests.py.

        Example: method `evaluate_docstring_quality` -> `EvaluateDocstringQualityRequest`

        Note: Some internal query/utility services are exempt (see EXEMPT_SERVICE_PROTOCOLS).
        """
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        req_use_case = ListRequestsUseCase(repo)
        req_response = await req_use_case.execute(ListCodeArtifactsRequest())

        # Also check shared bounded context (which is reserved but still has services)
        shared_services_dir = (
            project_root / "src" / "julee" / "shared" / "domain" / "services"
        )
        shared_requests_dir = (
            project_root / "src" / "julee" / "shared" / "domain" / "use_cases"
        )

        # Create artifact-like structures for shared services
        class ArtifactLike:
            def __init__(self, artifact, bounded_context):
                self.artifact = artifact
                self.bounded_context = bounded_context

        shared_services = (
            parse_python_classes(shared_services_dir)
            if shared_services_dir.exists()
            else []
        )
        shared_requests = (
            parse_python_classes(shared_requests_dir, exclude_files=["responses.py"])
            if shared_requests_dir.exists()
            else []
        )

        # Add shared artifacts to the response
        all_service_artifacts = list(response.artifacts) + [
            ArtifactLike(svc, "shared")
            for svc in shared_services
            if svc.name.endswith("Service")
        ]
        all_request_artifacts = list(req_response.artifacts) + [
            ArtifactLike(req, "shared")
            for req in shared_requests
            if req.name.endswith("Request")
        ]

        # Build set of available requests per context
        requests_by_context: dict[str, set[str]] = {}
        for artifact in all_request_artifacts:
            ctx = artifact.bounded_context
            if ctx not in requests_by_context:
                requests_by_context[ctx] = set()
            requests_by_context[ctx].add(artifact.artifact.name)

        def snake_to_pascal(name: str) -> str:
            """Convert snake_case to PascalCase."""
            return "".join(word.capitalize() for word in name.split("_"))

        violations = []
        for artifact in all_service_artifacts:
            service_name = artifact.artifact.name
            # Skip exempt services
            if service_name in EXEMPT_SERVICE_PROTOCOLS:
                continue

            ctx = artifact.bounded_context
            available = requests_by_context.get(ctx, set())

            for method in artifact.artifact.methods:
                expected_request = f"{snake_to_pascal(method.name)}Request"
                if expected_request not in available:
                    violations.append(
                        f"{ctx}.{service_name}.{method.name}(): missing {expected_request}"
                    )

        assert (
            not violations
        ), "Service protocol methods missing matching Request classes:\n" + "\n".join(
            violations
        )

"""Request doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

Naming conventions for classes in requests.py:
  - *Request: Top-level use case input (e.g., CreateJourneyRequest)
  - *Item: Nested compound type for complex attributes (e.g., JourneyStepItem)

Item types are used for list attributes within requests that need their own
validation and to_domain_model() conversion. They are NOT top-level requests.
"""

import pytest

from julee.shared.doctrine_constants import (
    ITEM_SUFFIX,
    REQUEST_BASE,
    REQUEST_SUFFIX,
)
from julee.shared.use_cases import (
    ListCodeArtifactsRequest,
    ListRequestsUseCase,
)


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
        """All request classes MUST inherit from BaseModel."""
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if REQUEST_BASE not in artifact.artifact.bases:
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

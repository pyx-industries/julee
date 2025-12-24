"""Response doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import pytest

from julee.shared.domain.doctrine_constants import (
    ITEM_SUFFIX,
    RESPONSE_BASE,
    RESPONSE_SUFFIX,
)
from julee.shared.domain.use_cases import (
    ListCodeArtifactsRequest,
    ListResponsesUseCase,
)


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
        """All response classes MUST inherit from BaseModel."""
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if RESPONSE_BASE not in artifact.artifact.bases:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), f"Responses not inheriting from {RESPONSE_BASE}:\n" + "\n".join(violations)

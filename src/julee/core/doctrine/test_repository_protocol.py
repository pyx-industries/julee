"""RepositoryProtocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import pytest

from julee.core.doctrine_constants import (
    PROTOCOL_BASES,
    REPOSITORY_SUFFIX,
)
from julee.core.use_cases.code_artifact.list_repository_protocols import (
    ListRepositoryProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest


class TestRepositoryProtocolNaming:
    """Doctrine about repository protocol naming conventions."""

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_end_with_Repository(self, repo):
        """All repository protocol names MUST end with 'Repository'."""
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning repository protocols
        assert (
            len(response.artifacts) > 0
        ), "No repository protocols found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.name.endswith(REPOSITORY_SUFFIX):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, (
            f"Repository protocols not ending with '{REPOSITORY_SUFFIX}':\n"
            + "\n".join(violations)
        )


class TestRepositoryProtocolDocumentation:
    """Doctrine about repository protocol documentation."""

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_have_docstring(self, repo):
        """All repository protocol classes MUST have a docstring."""
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Repository protocols missing docstrings:\n" + "\n".join(
            violations
        )


class TestRepositoryProtocolInheritance:
    """Doctrine about repository protocol inheritance."""

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_inherit_from_Protocol(self, repo):
        """All repository protocols MUST inherit from Protocol."""
        use_case = ListRepositoryProtocolsUseCase(repo)
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
        ), "Repository protocols not inheriting from Protocol:\n" + "\n".join(
            violations
        )

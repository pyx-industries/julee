"""Handler protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import pytest

from julee.core.use_cases.code_artifact.list_handler_protocols import (
    ListHandlerProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest


class TestHandlerProtocolStructure:
    """Doctrine about handler protocol structure."""

    @pytest.mark.asyncio
    async def test_handler_methods_MUST_return_Acknowledgement(self, repo):
        """Handler protocol methods MUST declare Acknowledgement as their return type.

        Handlers are the "green-dotted-egg" dispatchers of ADR 003. Returning
        Acknowledgement (wilco/unable/roger) gives use cases a uniform signal
        about whether the handoff was accepted, without knowing what the handler
        does internally.
        """
        use_case = ListHandlerProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning handler protocols
        assert (
            len(response.artifacts) > 0
        ), "No handler protocols found — detector may be broken"

        violations = []
        for artifact in response.artifacts:
            for method in artifact.artifact.methods:
                if method.return_type != "Acknowledgement":
                    violations.append(
                        f"{artifact.bounded_context}.{artifact.artifact.name}"
                        f".{method.name}(): return type is '{method.return_type}'"
                        f", expected 'Acknowledgement'"
                    )

        assert (
            not violations
        ), "Handler protocol methods not returning Acknowledgement:\n" + "\n".join(
            violations
        )

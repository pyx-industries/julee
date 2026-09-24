"""Handler protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.rules.protocol import (
    handler_methods_not_returning_Acknowledgement,
    handler_protocols_outside_singular_files,
    handlers_outside_infrastructure_handlers,
)
from julee.core.parsers.ast import parse_python_classes
from julee.core.usecases.code_artifact.list_handler_protocols import (
    ListHandlerProtocolsRequest,
    ListHandlerProtocolsUseCase,
)


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
        response = await use_case.execute(ListHandlerProtocolsRequest())

        if not response.artifacts:
            pytest.skip("No handler protocols in target codebase — nothing to check")

        violations = handler_methods_not_returning_Acknowledgement(response.artifacts)

        assert (
            not violations
        ), "Handler protocol methods not returning Acknowledgement:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_handler_protocols_MUST_be_in_singular_handler_file(self, repo):
        """Handler protocol classes MUST be defined in files named *_handler.py.

        One handler protocol per file, with the filename reflecting the handler's
        role (e.g. polling_result_handler.py). The singular form signals that
        each file defines a single protocol — not a collection of unrelated handlers.
        """
        use_case = ListHandlerProtocolsUseCase(repo)
        response = await use_case.execute(ListHandlerProtocolsRequest())

        violations = handler_protocols_outside_singular_files(response.artifacts)

        assert (
            not violations
        ), "Handler protocols not in singular *_handler.py files:\n" + "\n".join(
            violations
        )


class TestHandlerImplementationPlacement:
    """Doctrine about handler implementation placement."""

    @pytest.mark.asyncio
    async def test_handler_implementations_MUST_be_in_infrastructure_handlers(
        self, repo
    ):
        """Handler implementation classes MUST be in infrastructure/handlers/.

        Keeping concrete handler implementations in a dedicated subdirectory
        makes them easy to locate and keeps them separate from other infrastructure
        concerns (temporal wrappers, proxies, repositories). Temporal layer wrappers
        in infrastructure/temporal/ are exempt — they follow the three-layer pattern
        established for Temporal workflows.
        """
        found = [
            (ctx.slug, cls)
            for ctx in await repo.list_all()
            if (Path(ctx.path) / "infrastructure").exists()
            for cls in parse_python_classes(Path(ctx.path) / "infrastructure")
        ]

        violations = handlers_outside_infrastructure_handlers(found)

        assert (
            not violations
        ), "Handler implementations outside infrastructure/handlers/:\n" + "\n".join(
            violations
        )

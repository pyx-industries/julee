"""Handler protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.parsers.ast import parse_python_classes
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

        if not response.artifacts:
            pytest.skip("No handler protocols in target codebase — nothing to check")

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

    @pytest.mark.asyncio
    async def test_handler_protocols_MUST_be_in_singular_handler_file(self, repo):
        """Handler protocol classes MUST be defined in files named *_handler.py.

        One handler protocol per file, with the filename reflecting the handler's
        role (e.g. polling_result_handler.py). The singular form signals that
        each file defines a single protocol — not a collection of unrelated handlers.
        """
        use_case = ListHandlerProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            file = artifact.artifact.file
            if not file.endswith("_handler.py"):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                    f": defined in '{file}', expected a file named '*_handler.py'"
                )

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
        contexts = await repo.list_all()

        violations = []
        for ctx in contexts:
            infra_dir = Path(ctx.path) / "infrastructure"
            if not infra_dir.exists():
                continue

            for cls in parse_python_classes(infra_dir):
                if not cls.name.endswith("Handler"):
                    continue
                # Temporal layer wrappers are exempt (three-layer Temporal pattern)
                file_parts = Path(cls.file).parts
                if file_parts and file_parts[0] == "temporal":
                    continue
                if file_parts and file_parts[0] != "handlers":
                    violations.append(
                        f"{ctx.slug}.{cls.name}: found in"
                        f" infrastructure/{cls.file},"
                        f" expected infrastructure/handlers/"
                    )

        assert (
            not violations
        ), "Handler implementations outside infrastructure/handlers/:\n" + "\n".join(
            violations
        )

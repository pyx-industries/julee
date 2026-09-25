"""Service protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.rules.service import (
    contexts_whose_services_doctrine_cannot_see,
    services_not_named_for_their_role,
)
from julee.core.doctrine_constants import SERVICES_PATH
from julee.core.parsers.ast import parse_bounded_context
from julee.core.usecases.code_artifact.list_service_protocols import (
    ListServiceProtocolsRequest,
    ListServiceProtocolsUseCase,
)


class TestServiceProtocolNaming:
    """Doctrine about what a service protocol calls itself."""

    @pytest.mark.asyncio
    async def test_protocols_in_domain_services_MUST_claim_a_role(self, repo):
        """Protocols in domain/services/ MUST be named *Service or *Handler.

        A service protocol is found by its directory, the way a repository
        protocol is, rather than by its name. That is a deliberate change:
        keeping only classes named *Service meant anything else was dropped
        with nothing reported, so a solution whose protocols used a
        different suffix was told it had no services at all (#175).

        With the filter gone, the name becomes a claim doctrine can check.
        *Service says the protocol is a service; *Handler says it is a
        dispatcher and brings ADR 003's rules with it. A protocol claiming
        neither is a question worth answering, and there are only two
        answers: the name drifted, or the protocol is not a service and
        should not be in this directory.
        """
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListServiceProtocolsRequest())

        violations = services_not_named_for_their_role(response.artifacts)

        assert not violations, "Protocols in domain/services/ claiming no role:\n" + (
            "\n".join(violations)
        )


class TestServiceProtocolVisibility:
    """Doctrine about doctrine: that it can see what it claims to check."""

    @pytest.mark.asyncio
    async def test_a_services_package_MUST_yield_protocols_to_doctrine(self, repo):
        """A domain/services/ package with modules MUST parse to protocols.

        The canary. A rule that finds nothing passes, and so does a rule
        finding nothing because it was looking in the wrong way — which is
        how twenty service protocols went unseen in #175 and seven
        repository protocols in #231. Both looked green.

        So a bounded context with a populated services package, out of
        which doctrine reads neither a service nor a handler, fails here
        rather than passing everywhere else.
        """
        contexts_with_services = []
        for ctx in await repo.list_all():
            services_dir = Path(ctx.path)
            for part in SERVICES_PATH:
                services_dir = services_dir / part
            modules = [
                path for path in services_dir.glob("*.py") if path.name != "__init__.py"
            ]
            if not modules:
                continue
            info = parse_bounded_context(Path(ctx.path))
            found = (
                0
                if info is None
                else len(info.service_protocols) + len(info.handler_protocols)
            )
            contexts_with_services.append((ctx.slug, found))

        if not contexts_with_services:
            pytest.skip("No bounded context has a services package — nothing to check")

        violations = contexts_whose_services_doctrine_cannot_see(contexts_with_services)

        assert not violations, "Service packages doctrine cannot read:\n" + "\n".join(
            violations
        )

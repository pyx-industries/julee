"""Repository protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import re
from pathlib import Path

import pytest

from julee.core.entities.code_info import ClassInfo
from julee.core.parsers.ast import parse_bounded_context
from julee.core.use_cases.code_artifact.list_repository_protocols import (
    ListRepositoryProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest


def _extract_base_entity_type(class_info: ClassInfo) -> str | None:
    """Extract T from BaseRepository[T] in class bases.

    Returns the primary entity type name, or None if the class does not
    inherit from BaseRepository (and therefore has no declared primary type).
    """
    for base in class_info.bases:
        match = re.search(r"BaseRepository\[([A-Z][a-zA-Z0-9]*)\]", base)
        if match:
            return match.group(1)
    return None


class TestRepositoryProtocolBinding:
    """Doctrine about repository protocol entity binding."""

    @pytest.mark.asyncio
    async def test_repository_SHOULD_reference_at_most_one_entity_type(self, repo):
        """A repository protocol SHOULD reference at most one domain entity type.

        Repository protocols encapsulate persistence operations for a single
        aggregate root. Referencing multiple entity types blurs aggregate
        boundaries and couples persistence concerns that should remain separate.

        The primary entity is declared via the BaseRepository[T] generic
        parameter. Method signatures SHOULD NOT introduce additional domain
        entity types from other aggregates — doing so means the repository is
        doing two jobs.

        Incidental references to Enums, Status classes, and primitive types
        are excluded automatically: only types that appear in the bounded
        context's entity list are checked.

        Repositories that do not inherit from BaseRepository[T] are exempt —
        their primary entity type cannot be determined structurally.
        """
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning repository protocols
        assert (
            len(response.artifacts) > 0
        ), "No repository protocols found — detector may be broken"

        # Build entity name sets per bounded context
        contexts = await repo.list_all()
        entity_names_by_ctx: dict[str, set[str]] = {}
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info:
                entity_names_by_ctx[ctx.slug] = {e.name for e in info.entities}

        violations = []
        for artifact in response.artifacts:
            protocol = artifact.artifact
            ctx = artifact.bounded_context

            primary = _extract_base_entity_type(protocol)
            if primary is None:
                # No BaseRepository[T] — primary type undeclared, skip
                continue

            entity_names = entity_names_by_ctx.get(ctx, set())
            foreign_entities = (protocol.referenced_types & entity_names) - {primary}

            if foreign_entities:
                violations.append(
                    f"{ctx}.{protocol.name}: primary entity '{primary}' but "
                    f"also references {sorted(foreign_entities)}"
                )

        assert (
            not violations
        ), "Repository protocols referencing multiple entity types:\n" + "\n".join(
            violations
        )

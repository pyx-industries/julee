"""Repository protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import re
from pathlib import Path

import pytest

from julee.core.entities.code_info import ClassInfo
from julee.core.parsers.ast import parse_bounded_context
from julee.core.usecases.code_artifact.list_repository_protocols import (
    ListRepositoryProtocolsRequest,
    ListRepositoryProtocolsUseCase,
)


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


def _is_enum(entity: object) -> bool:
    """Whether a scanned class is an Enum rather than an entity.

    An Enum defined in domain/models is a value a repository method may
    take or return without binding the repository to a second entity, as
    the docstring on the binding test says. test_entity exempts them the
    same way.
    """
    bases = getattr(entity, "bases", None) or ()
    return any(b in {"str", "int"} or b.endswith("Enum") for b in bases)


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
        response = await use_case.execute(ListRepositoryProtocolsRequest())

        # A solution may legitimately have no repositories: a kit of pure
        # services, for example. Skip rather than fail, as the handler
        # protocol doctrine does.
        if not response.artifacts:
            pytest.skip("No repository protocols in target codebase — nothing to check")

        # Build entity name sets per bounded context by scanning domain/models/
        # (ADR 001 nested structure) and entities/ (flat structure).
        contexts = await repo.list_all()
        entity_names_by_ctx: dict[str, set[str]] = {}
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info:
                entity_names_by_ctx[ctx.slug] = {
                    e.name for e in info.entities if not _is_enum(e)
                }

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

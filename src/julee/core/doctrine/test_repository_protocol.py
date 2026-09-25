"""Repository protocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.rules.protocol import (
    repositories_referencing_several_entities,
)
from julee.core.parsers.ast import parse_bounded_context
from julee.core.usecases.code_artifact.list_repository_protocols import (
    ListRepositoryProtocolsRequest,
    ListRepositoryProtocolsUseCase,
)


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

        The primary entity is declared via the RepositoryOf[T] generic
        parameter, which BaseRepository[T] carries for a CRUD repository. Method signatures SHOULD NOT introduce additional domain
        entity types from other aggregates — doing so means the repository is
        doing two jobs.

        Incidental references to Enums, Status classes, and primitive types
        are excluded automatically: only types that appear in the bounded
        context's entity list are checked.

        A protocol here that declares neither is not exempt so much as
        misfiled. ADR 016 has a row for it: bound to no entity and
        reached through an activity is an Oracle, which belongs in
        domain/oracles/; bound to no entity and safe to call inline is a
        Calculator or a Witness. This rule still passes over it, because
        its entity cannot be read structurally and there is nothing here
        to check — but "no rule applies" is the wrong thing for a reader
        to conclude, and the driven port rules check it instead.
        """
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListRepositoryProtocolsRequest())

        # A solution may legitimately have no repositories: a kit of pure
        # services, for example. Skip rather than fail, as the handler
        # protocol doctrine does.
        if not response.artifacts:
            pytest.skip("No repository protocols in target codebase — nothing to check")

        entity_names_by_ctx = {
            ctx.slug: {e.name for e in info.entities if not _is_enum(e)}
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
        }

        violations = repositories_referencing_several_entities(
            response.artifacts, entity_names_by_ctx
        )

        assert (
            not violations
        ), "Repository protocols referencing multiple entity types:\n" + "\n".join(
            violations
        )

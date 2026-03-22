"""Entity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.parsers.ast import parse_bounded_context


class TestEntityNaming:
    """Doctrine about entity field naming (ADR 004)."""

    @pytest.mark.asyncio
    async def test_entity_fields_MUST_NOT_be_named_workflow_id(self, repo):
        """Entity fields MUST NOT be named 'workflow_id'.

        'workflow_id' is a Temporal-specific concept that leaks execution context
        into the domain model. Use 'execution_id' instead — it is framework-agnostic
        and works identically whether running in Temporal, Prefect, or directly.
        """
        contexts = await repo.list_all()

        violations = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info is None:
                continue
            for entity in info.entities:
                for field in entity.fields:
                    if field.name == "workflow_id":
                        violations.append(
                            f"{ctx.slug}.{entity.name}.{field.name}"
                        )

        assert not violations, (
            "Entity fields named 'workflow_id' (use 'execution_id' instead):\n"
            + "\n".join(violations)
        )

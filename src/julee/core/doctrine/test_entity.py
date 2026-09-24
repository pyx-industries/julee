"""Entity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.rules.entity import (
    entities_not_extending_Entity,
    fields_named_workflow_id,
    fields_using_mutable_collections,
)
from julee.core.parsers.ast import parse_bounded_context


class TestEntityImmutability:
    """Doctrine about entity immutability."""

    @pytest.mark.asyncio
    async def test_entity_classes_MUST_extend_Entity(self, repo):
        """All entity classes MUST extend Entity.

        Entities represent immutable domain records. Inheriting from Entity
        (which sets frozen=True) prevents field reassignment and signals that
        state changes require constructing new instances via model_copy().

        Enum subclasses are exempt — they are inherently immutable.

        Compliance is checked transitively: a class that extends another domain
        model (which itself extends Entity) is compliant. Classes whose bases
        are not found in the scanned codebase are trusted — e.g. julee models
        are verified by julee's own doctrine tests.
        """
        found = [
            (ctx.slug, entity)
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
            for entity in info.entities
        ]

        violations = entities_not_extending_Entity(found)

        assert not violations, "Entity classes not extending Entity:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_entity_field_annotations_MUST_NOT_use_mutable_collections(
        self, repo
    ):
        """Entity field annotations MUST NOT use mutable collection types.

        frozen=True prevents field reassignment but NOT mutation of mutable
        containers — entity.my_list.append(x) bypasses Pydantic's frozen
        constraint. True immutability requires immutable collection types:

        - tuple[...] instead of list[...]
        - Mapping[K, V] instead of dict[K, V]
        - frozenset[...] instead of set[...]

        Enum subclasses are exempt.
        """
        found = [
            (ctx.slug, entity)
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
            for entity in info.entities
        ]

        violations = fields_using_mutable_collections(found)

        assert not violations, (
            "Entity fields using mutable collections"
            " (use tuple/Mapping/frozenset instead):\n" + "\n".join(violations)
        )


class TestEntityNaming:
    """Doctrine about entity field naming (ADR 004)."""

    @pytest.mark.asyncio
    async def test_entity_fields_MUST_NOT_be_named_workflow_id(self, repo):
        """Entity fields MUST NOT be named 'workflow_id'.

        'workflow_id' is a Temporal-specific concept that leaks execution context
        into the domain model. Use 'execution_id' instead — it is framework-agnostic
        and works identically whether running in Temporal, Prefect, or directly.
        """
        found = [
            (ctx.slug, entity)
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
            for entity in info.entities
        ]

        violations = fields_named_workflow_id(found)

        assert not violations, (
            "Entity fields named 'workflow_id' (use 'execution_id' instead):\n"
            + "\n".join(violations)
        )

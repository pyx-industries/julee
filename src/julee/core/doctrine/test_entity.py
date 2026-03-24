"""Entity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

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
        contexts = await repo.list_all()
        enum_indicators = {"str", "int", "Enum"}

        # Collect all scanned entities: name -> (slug, entity)
        all_entities: dict = {}
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info is None:
                continue
            for entity in info.entities:
                if entity.bases:
                    all_entities[entity.name] = (ctx.slug, entity)

        def is_compliant(name: str, visiting: frozenset) -> bool:
            """Return True if the class transitively extends Entity."""
            if name == "Entity":
                return True
            if name == "BaseModel":
                return False
            if name in visiting:
                return False  # cycle guard
            if name not in all_entities:
                # External class (e.g. from julee) — trust it
                return True
            _, entity = all_entities[name]
            if any(b in enum_indicators for b in entity.bases):
                return True
            return any(is_compliant(b, visiting | {name}) for b in entity.bases)

        violations = []
        for name, (slug, entity) in all_entities.items():
            if any(b in enum_indicators for b in entity.bases):
                continue
            if not is_compliant(name, frozenset()):
                violations.append(f"{slug}.{name}")

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
        contexts = await repo.list_all()

        forbidden_prefixes = ("list[", "List[", "set[", "Set[", "dict[", "Dict[")
        enum_indicators = {"str", "int", "Enum"}

        violations = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info is None:
                continue
            for entity in info.entities:
                # Skip classes with no bases (not a Pydantic model)
                if not entity.bases:
                    continue
                # Skip Enum subclasses
                if any(b in enum_indicators for b in entity.bases):
                    continue
                for field in entity.fields:
                    # Skip private attributes (PrivateAttr) — mutable by design,
                    # not part of the entity's serialised state
                    if field.name.startswith("_"):
                        continue
                    annotation = field.type_annotation
                    if any(annotation.startswith(p) for p in forbidden_prefixes):
                        violations.append(
                            f"{ctx.slug}.{entity.name}.{field.name}: {annotation}"
                        )

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
        contexts = await repo.list_all()

        violations = []
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info is None:
                continue
            for entity in info.entities:
                for field in entity.fields:
                    if field.name == "workflow_id":
                        violations.append(f"{ctx.slug}.{entity.name}.{field.name}")

        assert not violations, (
            "Entity fields named 'workflow_id' (use 'execution_id' instead):\n"
            + "\n".join(violations)
        )

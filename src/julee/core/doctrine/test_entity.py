"""Entity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import ast
from pathlib import Path

import pytest

from julee.core.doctrine.rules.entity import (
    contexts_whose_entities_doctrine_cannot_see,
    copies_that_skip_a_validator,
    domain_packages_doctrine_does_not_read,
    entities_not_extending_Entity,
    fields_named_workflow_id,
    fields_using_mutable_collections,
)
from julee.core.doctrine_constants import ENTITIES_PATH
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


class TestEntityVisibility:
    """Doctrine about doctrine: that it can see the entities it checks."""

    @pytest.mark.asyncio
    async def test_a_context_with_domain_code_MUST_yield_entities(self, repo):
        """A context with use cases or repositories MUST yield entities.

        The canary. Entities are read out of domain/models/, so a context
        keeping them anywhere else yields none — and then every entity
        rule passes having nothing to check, and every repository in it is
        measured against an empty set of entity names. Silence all the way
        down.

        Use cases and repository protocols are the evidence that there is
        a domain here at all. A context with neither may legitimately have
        no entities; one with either almost certainly has them somewhere.

        Same failure mode as #175, where a solution's twenty service
        protocols were reported as none, and #231, where seven repository
        protocols went unchecked. Both were green throughout.
        """
        contexts = [
            info
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
        ]

        if not contexts:
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        violations = contexts_whose_entities_doctrine_cannot_see(contexts)

        assert not violations, "Contexts whose entities doctrine cannot see:\n" + (
            "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_every_package_under_domain_MUST_be_one_doctrine_reads(self, repo):
        """Packages under domain/ MUST be ones doctrine reads.

        The canary for partial blindness. A context keeping some entities
        in domain/models/ and others in domain/entities/ passes the rule
        above — it has entities doctrine reads — while half its domain
        goes unchecked and nothing says so.

        trust-graph-explorer is the case that prompted this: three
        entities in domain/models/, Facility in domain/entities/, and a
        FacilityRepository that returns Facility from four of its six
        methods while reading, to the one-entity rule, as bound to
        nothing.

        Whether domain/entities/ should also be an accepted spelling is a
        separate question. This is about the silence, not the spelling.
        """
        packages = []
        for ctx in await repo.list_all():
            domain_dir = Path(ctx.path) / ENTITIES_PATH[0]
            if not domain_dir.is_dir():
                continue
            for package in sorted(domain_dir.iterdir()):
                if not package.is_dir():
                    continue
                modules = [
                    path for path in package.glob("*.py") if path.name != "__init__.py"
                ]
                if modules:
                    packages.append((ctx.slug, package.name))

        if not packages:
            pytest.skip("No bounded context has a domain package — nothing to check")

        violations = domain_packages_doctrine_does_not_read(packages)

        assert not violations, "Packages under domain/ doctrine walks past:\n" + (
            "\n".join(violations)
        )


SKIPPED_DIRECTORIES = frozenset({".venv", "build", "dist", "__pycache__", "tests"})
"""Where a walk of a context's source does not go."""


def _read_source(contexts) -> tuple[list[tuple[str, int, tuple[str, ...]]], set[str]]:
    """Every model_copy(update=...) and every validated field name.

    One walk answers both, and both have to come from the same tree: a
    field validated in one kit says nothing about a same-named field in
    another.
    """
    copies: list[tuple[str, int, tuple[str, ...]]] = []
    validated: set[str] = set()

    for ctx in contexts:
        for source in sorted(Path(ctx.path).rglob("*.py")):
            if SKIPPED_DIRECTORIES.intersection(source.parts):
                continue
            try:
                tree = ast.parse(source.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue

            relative = source.relative_to(Path(ctx.path).parent)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if not isinstance(decorator, ast.Call):
                            continue
                        named = getattr(decorator.func, "id", None) or getattr(
                            decorator.func, "attr", None
                        )
                        if named != "field_validator":
                            continue
                        validated.update(
                            argument.value
                            for argument in decorator.args
                            if isinstance(argument, ast.Constant)
                            and isinstance(argument.value, str)
                        )
                if (
                    isinstance(node, ast.Call)
                    and getattr(node.func, "attr", None) == "model_copy"
                ):
                    for keyword in node.keywords:
                        if keyword.arg == "update" and isinstance(
                            keyword.value, ast.Dict
                        ):
                            copies.append(
                                (
                                    str(relative),
                                    node.lineno,
                                    tuple(
                                        key.value
                                        for key in keyword.value.keys
                                        if isinstance(key, ast.Constant)
                                        and isinstance(key.value, str)
                                    ),
                                )
                            )
    return copies, validated


class TestChangingAnEntity:
    """Doctrine about how a new snapshot of an entity is made."""

    @pytest.mark.asyncio
    async def test_a_validated_field_MUST_NOT_be_written_by_model_copy(
        self, repo
    ) -> None:
        """A field with a validator MUST be changed through evolve().

        model_copy(update=...) does not validate, by design, and for a
        field with nothing to check that is exactly right — it is how an
        immutable entity is changed.

        A validator is different, and not mainly because a value might
        be refused. One that returns tuple(v) or v.strip() or None is
        deciding what the field holds rather than checking it. Skipped,
        an entity ends up carrying a mutable list where its annotation
        says tuple: the thing the mutable-collections rule above reads
        annotations to prevent, reached from the other side.

        Entity.evolve() makes the same change and runs the validators.
        """
        copies, validated = _read_source(await repo.list_all())
        if not copies:
            pytest.skip("No model_copy(update=...) in target codebase")

        violations = copies_that_skip_a_validator(copies, validated)

        assert not violations, (
            "Fields with validators changed through model_copy:\n"
            + "\n".join(violations)
        )

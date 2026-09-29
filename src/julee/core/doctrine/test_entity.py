"""Entity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import ast
from pathlib import Path

import pytest

from julee.core.doctrine.resolution import entity_verdicts
from julee.core.doctrine.rules.entity import (
    VALIDATOR_DECORATORS,
    contexts_whose_entities_doctrine_cannot_see,
    copies_that_skip_a_validator,
    domain_packages_doctrine_does_not_read,
    entities_that_are_not_frozen_dataclasses,
    entities_that_can_be_mutated,
    fields_named_workflow_id,
    fields_using_mutable_collections,
    validators_that_transform,
)
from julee.core.doctrine_constants import ENTITIES_PATH
from julee.core.parsers.ast import parse_bounded_context


class TestEntityImmutability:
    """Doctrine about entity immutability."""

    @pytest.mark.asyncio
    async def test_entity_classes_MUST_be_immutable(self, repo):
        """An entity's fields MUST NOT be reassignable.

        An entity is a snapshot of business state: a change means a new
        instance rather than an edited one, and a field that can be
        written makes that a convention rather than a fact. A frozen
        dataclass is how one says so.

        Enum subclasses are exempt — they are inherently immutable.

        Compliance is checked transitively: a class that extends another domain
        model (which is itself immutable) is compliant. Classes whose bases
        are not found in the scanned codebase are trusted — e.g. julee models
        are verified by julee's own doctrine tests.
        """
        found = [
            (ctx.slug, entity)
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
            for entity in info.entities
        ]

        violations = entities_that_can_be_mutated(found)

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

        dataclasses.replace() makes the same change and runs __post_init__.
        """
        copies, validated = _read_source(await repo.list_all())
        if not copies:
            pytest.skip("No model_copy(update=...) in target codebase")

        violations = copies_that_skip_a_validator(copies, validated)

        assert not violations, (
            "Fields with validators changed through model_copy:\n"
            + "\n".join(violations)
        )


class TestWhatAValidatorIsFor:
    """Doctrine about what a validator may do."""

    @pytest.mark.asyncio
    async def test_a_validator_MUST_NOT_return_a_changed_value(self, repo) -> None:
        """A validator MUST return the value it was given, or raise.

        A validator that returns something else is not checking
        anything. It is deciding what the field holds, which is
        normalisation, and normalisation belongs in the field's *type*.

        The argument is not stylistic. A normalising validator is a
        constructor written in the wrong place, and being in the wrong
        place it gets copied — unevenly. c4 had a slug field that ran
        slugify and eight fields naming those slugs that ran strip, so a
        component could name a container that could not be found. The
        lookup came back empty rather than wrong: no exception, no log
        line, no failing test (julee-kits#70).

        A type cannot be copied unevenly. Declare both ends Slug and
        they agree, because there is one implementation of what a slug
        is and every route reaches it — deserialisation included, which
        is where a constructor-side check does not always run.

        julee.core.values.text is where the estate's went: 76 of 83
        validators were transformers, 53 of them literally v.strip().

        A validator with no return at all complies. Raising, or saying
        nothing, is what checking looks like.
        """
        found = [
            (ctx.slug, entity)
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
            for entity in info.entities
        ]

        violations = validators_that_transform(found)

        assert not violations, "Validators that change what they were given:\n" + (
            "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_doctrine_can_see_a_validator_where_one_exists(self, repo) -> None:
        """Whatever the rule above reads, it must be reading something.

        The rule passes over a codebase with no validators, and reads
        identically to one over a codebase that complies. That much is
        fine: zero validators is the destination, not a blind spot.

        What is not fine is the rule finding zero because the parser
        stopped recording decorators. Then every codebase passes and
        nothing says so — the failure this repository keeps meeting
        (#175, #231, #142).

        So this asserts the mechanism rather than the count: where a
        method's own source carries a validator decorator, the parsed
        view of it must agree. A target with no validators at all skips,
        having nothing to prove.
        """
        entities = [
            entity
            for ctx in await repo.list_all()
            if (info := parse_bounded_context(Path(ctx.path))) is not None
            for entity in info.entities
        ]
        by_source = {
            f"{entity.name}.{method.name}"
            for entity in entities
            for method in entity.methods
            if any(f"@{d}" in (method.source or "") for d in VALIDATOR_DECORATORS)
        }
        if not by_source:
            pytest.skip("No validators in target codebase, so nothing to see")

        by_parse = {
            f"{entity.name}.{method.name}"
            for entity in entities
            for method in entity.methods
            if any(method.decorated_with(d) for d in VALIDATOR_DECORATORS)
        }

        assert by_source <= by_parse, (
            "Doctrine cannot see validators that are there:\n"
            + "\n".join(sorted(by_source - by_parse))
        )


class TestTheDomainRing:
    """Doctrine about what a domain class may be built from."""

    @pytest.mark.asyncio
    async def test_entities_MUST_be_frozen_dataclasses(self, repo):
        """A domain class MUST be an entity or a value object.

        An entity has identity and is a frozen stdlib dataclass. A
        value object is the value it wraps — two with the same
        contents are the same thing — so it is an enum or is built on
        str or int.

        Pydantic is refused in both its forms. A model carries a
        serialisation library into the innermost ring. A pydantic
        dataclass carries it while reading as a plain dataclass
        everywhere else, so it satisfies this rule and the rule for
        the driving ring at once and says which ring it is in to
        neither.
        """
        contexts = await repo.list_all()
        if not contexts:
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        verdicts = []
        found_any = False
        for ctx in contexts:
            info = parse_bounded_context(Path(ctx.path))
            if info is None:
                continue
            names = [entity.name for entity in info.entities]
            found_any = found_any or bool(names)
            verdicts.extend(entity_verdicts(ctx.slug, Path(ctx.path), names))

        if not found_any:
            pytest.skip("No domain classes in target codebase — nothing to check")

        violations = entities_that_are_not_frozen_dataclasses(verdicts)

        assert not violations, (
            "Domain classes that are not frozen dataclasses:\n" + "\n".join(violations)
        )

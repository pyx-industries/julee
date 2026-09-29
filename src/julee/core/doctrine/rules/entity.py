"""What the entity rules object to.

Most take the entities a codebase has, paired with the bounded context
each was found in, and return their objections. The two canaries read a
parsed bounded context instead, because what they are checking is
whether doctrine found any entities to check at all. Either way the
parsing has already happened: nothing here reads a file.
"""

from collections.abc import Iterable

from julee.core.doctrine.resolution import Verdict
from julee.core.doctrine_constants import (
    CALCULATORS_PATH,
    ENTITIES_PATH,
    HANDLERS_PATH,
    ORACLES_PATH,
    REPOSITORIES_PATH,
    SERVICES_PATH,
    WITNESSES_PATH,
)
from julee.core.entities.bounded_context_info import BoundedContextInfo
from julee.core.entities.code_info import ClassInfo

__all__ = [
    "ENUM_INDICATORS",
    "FORBIDDEN_COLLECTION_PREFIXES",
    "READ_DOMAIN_PACKAGES",
    "VALIDATOR_DECORATORS",
    "contexts_whose_entities_doctrine_cannot_see",
    "copies_that_skip_a_validator",
    "domain_packages_doctrine_does_not_read",
    "entities_that_can_be_mutated",
    "value_object_names",
    "entities_that_are_not_frozen_dataclasses",
    "fields_named_workflow_id",
    "fields_using_mutable_collections",
    "validators_that_transform",
]

Found = Iterable[tuple[str, ClassInfo]]
"""Entities paired with the bounded context each was found in."""

ENUM_INDICATORS = {"str", "int", "Enum"}
"""Bases that mark a class as an enum, which is immutable already."""

FORBIDDEN_COLLECTION_PREFIXES = ("list[", "List[", "set[", "Set[", "dict[", "Dict[")
"""Annotations that can be mutated through, whatever frozen says."""

VALIDATOR_DECORATORS = frozenset({"field_validator", "model_validator"})
"""The decorators that make a method a validator."""

_IMPLICIT_PARAMETERS = frozenset({"cls", "self"})
"""Parameters that are the class or the instance, not the value."""

READ_DOMAIN_PACKAGES = frozenset(
    path[-1]
    for path in (
        ENTITIES_PATH,
        REPOSITORIES_PATH,
        SERVICES_PATH,
        ORACLES_PATH,
        CALCULATORS_PATH,
        WITNESSES_PATH,
        HANDLERS_PATH,
    )
)
"""The packages under domain/ that doctrine reads anything out of.

Derived from the layer paths rather than spelled again, so a package
doctrine learns to read stops being reported the moment it does.

Three of the seven were spelled in by hand when this was written, and
the four ADR 016 added arrived later, so the first kit to file a
protocol under domain/oracles/ was told the directory held modules
doctrine does not read — while the parser was reading them perfectly
well. A false objection is worse than a missing rule: it tells an
author their correct work is wrong.

Comprehension rather than a set literal, so adding a layer path is the
only edit a new port needs.
"""

_ENTITIES_DIR = "/".join(ENTITIES_PATH)


def _is_enum(entity: ClassInfo) -> bool:
    """Whether a class is an enum, and so exempt."""
    return any(base in ENUM_INDICATORS for base in entity.bases)


def _is_dataclass(entity: ClassInfo) -> bool:
    """Whether a class gets its shape from a dataclass decorator.

    Such a class has no bases, so the rules here used to pass over it:
    they filtered on ``entity.bases`` to mean "something I can reason
    about", and a decorated class is something they can reason about
    from the decorator instead. A downstream solution with 52
    frozen-dataclass entities had them all discovered and two of the
    three rules declining to check any of them (#142).
    """
    return entity.decorated_with("dataclass")


def _is_frozen_dataclass(entity: ClassInfo) -> bool:
    """Whether a dataclass was told to be immutable.

    Read from the source of ``frozen=``, so anything but a literal True
    counts as not knowing and the class is reported. A constant is worth
    objecting to here: whether an entity is immutable should be legible
    where it is defined.
    """
    return entity.decorator_argument("dataclass", "frozen") == "True"


def entities_that_can_be_mutated(found: Found) -> list[str]:
    """Entities whose fields can be reassigned after construction.

    An entity is a snapshot: a change means a new instance rather than
    an edited one, and a field that can be written makes that a
    convention rather than a fact.

    This was ``entities_not_extending_Entity``, and it named a base
    class that no longer exists. ``Entity`` was a pydantic ``BaseModel``
    with ``frozen=True``; every entity that inherited it is a frozen
    dataclass now, so the rule is stated as what it always measured.

    Compliance is transitive: a class extending another entity in the
    same codebase is fine. A base this codebase cannot see is trusted,
    since whoever owns it runs their own doctrine over it.

    A class with no bases complies if it is a ``@dataclass(frozen=True)``.
    A ``@dataclass`` without it is reported, which is the case this rule
    used to miss entirely: a mutable entity, discovered and unexamined.

    Args:
        found: Entities paired with their bounded context

    Returns:
        One name per entity that is not frozen and should be
    """
    by_name = {
        entity.name: (slug, entity)
        for slug, entity in found
        if entity.bases or _is_dataclass(entity)
    }

    def is_compliant(name: str, visiting: frozenset[str]) -> bool:
        # "Entity" was trusted here by name, because julee's Entity was
        # frozen. It is gone, and trusting the name would now pass any
        # base a solution chose to call Entity, frozen or not.
        if name == "BaseModel":
            return False
        if name in visiting:
            return False
        if name not in by_name:
            return True
        _, entity = by_name[name]
        if _is_enum(entity):
            return True
        if _is_dataclass(entity):
            return _is_frozen_dataclass(entity)
        return any(is_compliant(base, visiting | {name}) for base in entity.bases)

    return [
        f"{slug}.{name}"
        for name, (slug, entity) in by_name.items()
        if not _is_enum(entity) and not is_compliant(name, frozenset())
    ]


def value_object_names(
    entities: Iterable[ClassInfo], roots: frozenset[str]
) -> set[str]:
    """Which of these classes are values rather than entities.

    A value object is not an aggregate, so a repository naming one is
    not a repository doing the work of two, and a port naming one is
    not leaking a representation. An enum, and anything built on str or
    int, directly or through another value object.

    The indirect case is the one that matters. ``ContentMultihash``
    extends ``NonEmptyText``, which extends ``str``: read one base deep
    it looks like a class extending some entity, and ceap's
    DocumentRepository was reported as bound to two aggregates for
    returning one. The note in that method's docstring predicted it
    exactly, and said str was returned instead for that reason.

    Args:
        entities: The classes a bounded context declares
        roots: Names that are values without being looked up — "str",
            "int", and the kernel's own value objects

    Returns:
        The names that are values
    """
    by_name = {entity.name: entity for entity in entities}
    found: set[str] = set()

    def is_a_value(name: str, visiting: frozenset[str]) -> bool:
        if name in roots or name.endswith("Enum"):
            return True
        if name in visiting or name not in by_name:
            return False
        bases = by_name[name].bases
        return any(is_a_value(base, visiting | {name}) for base in bases)

    for name, entity in by_name.items():
        if any(is_a_value(base, frozenset({name})) for base in entity.bases):
            found.add(name)
    return found


def fields_using_mutable_collections(found: Found) -> list[str]:
    """Entity fields holding something that can be changed in place.

    frozen=True stops a field being reassigned, not a list on it being
    appended to. Immutability needs tuple, Mapping and frozenset rather
    than list, dict and set.

    Private attributes are exempt: they are mutable by design and are not
    part of what the entity serialises.

    A dataclass is checked like anything else. It has no bases, so this
    used to pass over every field on one, which meant a frozen dataclass
    carrying ``list[str]`` — mutable through, exactly what this rule is
    for — read as compliant (#142).

    Args:
        found: Entities paired with their bounded context

    Returns:
        One sentence per field that can be mutated through
    """
    return [
        f"{slug}.{entity.name}.{field.name}: {field.type_annotation}"
        for slug, entity in found
        if (entity.bases or _is_dataclass(entity)) and not _is_enum(entity)
        for field in entity.fields
        if not field.name.startswith("_")
        and field.type_annotation.startswith(FORBIDDEN_COLLECTION_PREFIXES)
    ]


def fields_named_workflow_id(found: Found) -> list[str]:
    """Entity fields carrying Temporal's word for an execution.

    workflow_id names how the work is being run, which the domain should
    not know. execution_id says the same thing without naming a runner
    (ADR 004).

    Args:
        found: Entities paired with their bounded context

    Returns:
        One sentence per offending field
    """
    return [
        f"{slug}.{entity.name}.{field.name}"
        for slug, entity in found
        for field in entity.fields
        if field.name == "workflow_id"
    ]


def contexts_whose_entities_doctrine_cannot_see(
    contexts: Iterable[BoundedContextInfo],
) -> list[str]:
    """Contexts with domain code but no entity doctrine can read.

    The canary, for the case where doctrine is blind to all of them. A
    rule that finds nothing passes, and a rule that finds nothing because
    it was looking in the wrong place passes just as quietly — which is
    how twenty service protocols went unseen in #175 and seven repository
    protocols in #231. Both looked green.

    Entities are read out of ``domain/models/``. A context keeping them
    somewhere else yields none, so every entity rule passes having
    nothing to check, and every repository in it is measured against an
    empty set of entity names. Nothing fails and nothing is reported.

    Use cases and repository protocols are the evidence that the context
    has a domain at all. One with neither may legitimately have no
    entities; one with either almost certainly has them somewhere.

    Args:
        contexts: The bounded contexts doctrine parsed

    Returns:
        One sentence per context whose entities doctrine cannot see
    """
    objections = []
    for info in contexts:
        if info.entities:
            continue
        evidence = []
        if info.use_cases:
            evidence.append(f"{len(info.use_cases)} use cases")
        if info.repository_protocols:
            evidence.append(f"{len(info.repository_protocols)} repository protocols")
        if not evidence:
            continue
        objections.append(
            f"{info.slug}: doctrine read {' and '.join(evidence)} out of this "
            f"context but no entity at all out of {_ENTITIES_DIR}/, so either "
            f"it has none or they are somewhere doctrine is not looking"
        )
    return objections


def domain_packages_doctrine_does_not_read(
    packages: Iterable[tuple[str, str]],
) -> list[str]:
    """Packages under domain/ that doctrine walks past without a word.

    The canary for partial blindness, which the other one cannot catch.
    A context keeping some entities in ``domain/models/`` and others in
    ``domain/entities/`` has entities doctrine reads, so it passes the
    first rule while half its domain goes unchecked.

    trust-graph-explorer is the case: three entities in ``domain/models/``
    and ``Facility`` in ``domain/entities/``. ``FacilityRepository``
    returns ``Facility`` from four of its six methods and reads, to the
    one-entity rule, as bound to nothing at all.

    Whether ``domain/entities/`` should also be an accepted spelling is a
    separate question. This rule is about the silence, not the spelling:
    a package under domain/ with modules in it that doctrine reads
    nothing out of says so, rather than being skipped.

    Args:
        packages: Context slug paired with the name of a package under
            its domain/ directory that holds at least one module

    Returns:
        One sentence per package doctrine reads nothing out of
    """
    return [
        f"{slug}: domain/{name}/ holds modules doctrine does not read. "
        f"Entities belong in {_ENTITIES_DIR}/, and anything doctrine reads "
        f"nothing out of is unchecked rather than compliant"
        for slug, name in packages
        if name not in READ_DOMAIN_PACKAGES
    ]


def copies_that_skip_a_validator(
    copies: Iterable[tuple[str, int, tuple[str, ...]]],
    validated_fields: Iterable[str],
) -> list[str]:
    """Uses of model_copy that write a field carrying a validator.

    ``model_copy(update=...)`` does not validate, by design. For most
    fields that is exactly what is wanted — it is how an immutable
    entity is changed, and there is nothing to check.

    A field with a validator is different, and not mainly because the
    value might be refused. A validator that returns ``tuple(v)`` or
    ``v.strip() or None`` is not checking the value, it is deciding what
    the field holds. Skipped, the entity ends up carrying a mutable list
    where its own annotation says tuple — which is what
    :func:`fields_using_mutable_collections` reads annotations to
    prevent, arrived at from the other direction (julee-kits#57).

    ``dataclasses.replace`` writes the same change and runs
    ``__post_init__``, so the remedy is to use it.

    Field names are matched across the codebase being checked rather
    than resolved to the model being copied, because the model a
    ``model_copy`` call sits on cannot be told from the source. Scoping
    matters: run over two kits at once and a field validated in one is
    attributed to a same-named field in the other.

    Only production code is read. Building a state the validators
    forbid is what ``model_copy`` is still for, and a test exercising
    what happens to one has no other way to make it.

    An ``update`` that is not a dict literal is not read, and so not
    objected to. Nothing in the estate writes one, and guessing at what
    a variable holds would object to the wrong lines.

    Args:
        copies: File, line, and the field names each model_copy writes
        validated_fields: Every field name carrying a validator here

    Returns:
        One sentence per call that writes a validated field
    """
    validated = set(validated_fields)

    objections = []
    for path, line, fields in copies:
        skipped = sorted(set(fields) & validated)
        if not skipped:
            continue
        # Read once by a person who then has to act on it, so it agrees
        # with itself: one field has a validator, several have validators.
        subject = (
            f"{skipped[0]}, which has a validator"
            if len(skipped) == 1
            else f"{', '.join(skipped)}, which have validators"
        )
        objections.append(
            f"{path}:{line}: model_copy writes {subject} that will not "
            f"run. Use evolve() instead"
        )
    return objections


def validators_that_transform(found: Found) -> list[str]:
    """Validators that hand back something other than what they were given.

    A validator that returns a changed value is not checking anything.
    It is deciding what the field holds, which is normalisation, which
    belongs in the *type* of the field rather than in every entity that
    carries one.

    The argument is not stylistic. A normalising validator is a
    constructor written in the wrong place, and being in the wrong place
    it gets copied — unevenly. c4 had a slug field that ran ``slugify``
    and eight fields *naming* those slugs that ran ``strip``, so a
    component could name a container that could not be found. The lookup
    came back empty rather than wrong: no exception, no log line, no
    failing test (julee-kits#70).

    A type cannot be copied unevenly. Both ends of a reference declared
    ``Slug`` agree because there is one implementation of what a slug is
    and every route reaches it — including deserialisation, which a
    validator on the constructor does not always cover.

    The measurement that prompted this: 76 of 83 validators across the
    estate were transformers, 53 of them literally ``v.strip()``.
    :mod:`julee.core.entities.text` is where those went.

    Three further consequences, each of which bit before the rule:

    - ``model_copy(update=...)`` does not run validators, so a
      transformer skipped there leaves an entity holding something its
      own annotation forbids. :func:`copies_that_skip_a_validator` is
      that problem from the other side, and it stops being needed as
      this one is obeyed.
    - ``Entity.evolve`` existed to re-run transformers. It is gone with
      the class, and ``dataclasses.replace`` always runs
      ``__post_init__``, so there is no longer a pair to tell apart.
    - A frozen dataclass has no validators at all (#307). Work that
      lives in one has to move before entities can stop being pydantic
      models; work that lives in a type moves with it.

    What counts as compliant is returning a parameter unchanged —
    ``return v``. Anything else is reported: a call, a literal, an
    attribute, a comprehension. ``return None`` is included on purpose,
    because turning an empty value into None is the same decision made
    quietly.

    A validator with no ``return`` at all is compliant and useful: it
    raises or says nothing, which is what checking looks like.

    This rule cannot see a validator on something that is not an entity
    — an API request model, say. That is not blindness to hide: those
    are not what the rule is about, and a request that declares the
    entity's field *type* gets the rule for free rather than borrowing
    it (julee-kits#71).

    Args:
        found: Entities paired with their bounded context

    Returns:
        One sentence per validator that returns something else
    """
    objections = []
    for slug, entity in found:
        for method in entity.methods:
            if not any(method.decorated_with(d) for d in VALIDATOR_DECORATORS):
                continue
            value_parameters = {
                name
                for name in method.parameter_names
                if name not in _IMPLICIT_PARAMETERS
            }
            transforms = sorted(
                {r for r in method.returns if r not in value_parameters}
            )
            if not transforms:
                continue
            objections.append(
                f"{slug}.{entity.name}.{method.name} returns "
                f"{', '.join(transforms)} rather than what it was given. A "
                f"validator that changes a value is deciding what the field "
                f"holds, which belongs in the field's type — see "
                f"julee.core.entities.text"
            )
    return objections


def entities_that_are_not_frozen_dataclasses(
    verdicts: Iterable["Verdict"],
) -> list[str]:
    """Domain classes that are neither an entity nor a value object.

    The domain ring holds two kinds of class. An entity has identity
    and is a frozen stdlib dataclass. A value object is the value it
    wraps, so it is an enum or is built on ``str`` or ``int``.

    A pydantic model brings a serialisation library into the innermost
    ring; a pydantic dataclass brings it while reading as a plain
    dataclass everywhere else.

    The verdicts come from
    :func:`julee.core.doctrine.resolution.entity_verdicts`, which
    imports the class. Neither of pydantic's forms can be told from
    the AST: ``Entity`` is a name, and both decorators are spelled
    ``@dataclass(frozen=True)`` at the point of use.

    Args:
        verdicts: One per entity name, from entity_verdicts

    Returns:
        One sentence per entity carrying pydantic into the domain
    """
    return [
        f"{verdict.bounded_context}.{verdict.name}: {verdict.reason}"
        for verdict in verdicts
        if verdict.reason is not None
    ]

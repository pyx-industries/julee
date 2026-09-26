"""What the entity rules object to.

Most take the entities a codebase has, paired with the bounded context
each was found in, and return their objections. The two canaries read a
parsed bounded context instead, because what they are checking is
whether doctrine found any entities to check at all. Either way the
parsing has already happened: nothing here reads a file.
"""

from collections.abc import Iterable

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
    "contexts_whose_entities_doctrine_cannot_see",
    "copies_that_skip_a_validator",
    "domain_packages_doctrine_does_not_read",
    "entities_not_extending_Entity",
    "fields_named_workflow_id",
    "fields_using_mutable_collections",
]

Found = Iterable[tuple[str, ClassInfo]]
"""Entities paired with the bounded context each was found in."""

ENUM_INDICATORS = {"str", "int", "Enum"}
"""Bases that mark a class as an enum, which is immutable already."""

FORBIDDEN_COLLECTION_PREFIXES = ("list[", "List[", "set[", "Set[", "dict[", "Dict[")
"""Annotations that can be mutated through, whatever frozen says."""

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


def entities_not_extending_Entity(found: Found) -> list[str]:
    """Entities that do not inherit immutability.

    Entity sets frozen=True, which stops field reassignment and says that
    a change means a new instance rather than an edited one.

    Compliance is transitive: a class extending another entity in the
    same codebase is fine. A base this codebase cannot see is trusted,
    since whoever owns it runs their own doctrine over it.

    Args:
        found: Entities paired with their bounded context

    Returns:
        One name per entity that is not frozen and should be
    """
    by_name = {entity.name: (slug, entity) for slug, entity in found if entity.bases}

    def is_compliant(name: str, visiting: frozenset[str]) -> bool:
        if name == "Entity":
            return True
        if name == "BaseModel":
            return False
        if name in visiting:
            return False
        if name not in by_name:
            return True
        _, entity = by_name[name]
        if _is_enum(entity):
            return True
        return any(is_compliant(base, visiting | {name}) for base in entity.bases)

    return [
        f"{slug}.{name}"
        for name, (slug, entity) in by_name.items()
        if not _is_enum(entity) and not is_compliant(name, frozenset())
    ]


def fields_using_mutable_collections(found: Found) -> list[str]:
    """Entity fields holding something that can be changed in place.

    frozen=True stops a field being reassigned, not a list on it being
    appended to. Immutability needs tuple, Mapping and frozenset rather
    than list, dict and set.

    Private attributes are exempt: they are mutable by design and are not
    part of what the entity serialises.

    Args:
        found: Entities paired with their bounded context

    Returns:
        One sentence per field that can be mutated through
    """
    return [
        f"{slug}.{entity.name}.{field.name}: {field.type_annotation}"
        for slug, entity in found
        if entity.bases and not _is_enum(entity)
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

    :meth:`julee.core.entities.entity.Entity.evolve` writes the same
    change and runs the validators, so the remedy is a rename.

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

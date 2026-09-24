"""What the entity rules object to.

Each function takes the entities a codebase has, paired with the bounded
context each was found in, and returns its objections. The parsing has
already happened: these read ClassInfo and nothing else.
"""

from collections.abc import Iterable

from julee.core.entities.code_info import ClassInfo

__all__ = [
    "ENUM_INDICATORS",
    "FORBIDDEN_COLLECTION_PREFIXES",
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

"""Tests for the entity rules."""

import pytest

from julee.core.doctrine.rules.entity import (
    contexts_whose_entities_doctrine_cannot_see,
    domain_packages_doctrine_does_not_read,
    entities_not_extending_Entity,
    fields_named_workflow_id,
    fields_using_mutable_collections,
)
from julee.core.entities.bounded_context_info import BoundedContextInfo
from julee.core.entities.code_info import ClassInfo, FieldInfo

pytestmark = pytest.mark.unit


def an_entity(
    name: str = "Story",
    bases: tuple[str, ...] = ("Entity",),
    fields: tuple[tuple[str, str], ...] = (("slug", "str"),),
    slug: str = "hcd",
) -> tuple[str, ClassInfo]:
    """An entity that offends none of the rules."""
    return (
        slug,
        ClassInfo(
            name=name,
            bases=list(bases),
            fields=[
                FieldInfo(name=n, type_annotation=annotation)
                for n, annotation in fields
            ],
        ),
    )


def a_context(
    slug: str = "hcd",
    entities: int = 3,
    use_cases: int = 4,
    repositories: int = 2,
) -> BoundedContextInfo:
    """A parsed context, described by how much of each thing doctrine read."""
    return BoundedContextInfo(
        slug=slug,
        entities=[ClassInfo(name=f"Entity{i}") for i in range(entities)],
        use_cases=[ClassInfo(name=f"Do{i}UseCase") for i in range(use_cases)],
        repository_protocols=[
            ClassInfo(name=f"Thing{i}Repository") for i in range(repositories)
        ],
    )


# =============================================================================
# Frozen, or descended from something frozen
# =============================================================================


def test_an_entity_extending_Entity_is_allowed() -> None:
    """The ordinary case."""
    assert entities_not_extending_Entity([an_entity()]) == []


def test_an_entity_extending_BaseModel_is_reported() -> None:
    """Pydantic's base is mutable; a domain record should not be."""
    assert entities_not_extending_Entity([an_entity(bases=("BaseModel",))]) != []


def test_compliance_is_inherited_through_another_entity() -> None:
    """A class extending a frozen class is frozen."""
    found = [
        an_entity(name="Story", bases=("Entity",)),
        an_entity(name="DraftStory", bases=("Story",)),
    ]

    assert entities_not_extending_Entity(found) == []


def test_a_base_this_codebase_cannot_see_is_trusted() -> None:
    """Whoever owns it runs their own doctrine over it."""
    found = [an_entity(name="Persona", bases=("SomeKitEntity",))]

    assert entities_not_extending_Entity(found) == []


def test_an_enum_is_exempt_because_it_is_already_immutable() -> None:
    """Freezing an enum would be a category error."""
    found = [an_entity(name="AppType", bases=("str", "Enum"))]

    assert entities_not_extending_Entity(found) == []


def test_inheriting_from_a_mutable_entity_is_reported() -> None:
    """The chain is only as frozen as its weakest link."""
    found = [
        an_entity(name="Loose", bases=("BaseModel",)),
        an_entity(name="Tighter", bases=("Loose",)),
    ]

    assert len(entities_not_extending_Entity(found)) == 2


def test_a_cycle_in_the_bases_does_not_hang() -> None:
    """Impossible in Python, but the parser reads text, not classes."""
    found = [
        an_entity(name="A", bases=("B",)),
        an_entity(name="B", bases=("A",)),
    ]

    assert len(entities_not_extending_Entity(found)) == 2


# =============================================================================
# Frozen all the way down
# =============================================================================


def test_immutable_collections_are_allowed() -> None:
    """tuple, Mapping and frozenset cannot be changed in place."""
    found = [
        an_entity(
            fields=(
                ("tags", "tuple[str, ...]"),
                ("props", "Mapping[str, str]"),
                ("seen", "frozenset[str]"),
            )
        )
    ]

    assert fields_using_mutable_collections(found) == []


@pytest.mark.parametrize(
    "annotation",
    ["list[str]", "List[str]", "dict[str, str]", "Dict[str, str]", "set[str]"],
)
def test_a_mutable_collection_is_reported(annotation: str) -> None:
    """frozen stops reassignment, not appending to what is already there."""
    found = [an_entity(fields=(("tags", annotation),))]

    assert fields_using_mutable_collections(found) != []


def test_a_private_attribute_may_be_mutable() -> None:
    """It is mutable by design and is not part of what is serialised."""
    found = [an_entity(fields=(("_cache", "dict[str, str]"),))]

    assert fields_using_mutable_collections(found) == []


def test_an_enum_is_exempt_here_too() -> None:
    """Its members are not fields in this sense."""
    found = [an_entity(bases=("str", "Enum"), fields=(("values", "list[str]"),))]

    assert fields_using_mutable_collections(found) == []


def test_the_objection_names_the_field_and_its_annotation() -> None:
    """Whoever fixes it needs to know what to change it to."""
    found = [an_entity(fields=(("tags", "list[str]"),))]

    objection = fields_using_mutable_collections(found)[0]

    assert objection == "hcd.Story.tags: list[str]"


def test_a_type_merely_containing_list_is_not_a_list() -> None:
    """Checklist is not a list, and neither is tuple[Checklist, ...]."""
    found = [an_entity(fields=(("items", "tuple[Checklist, ...]"),))]

    assert fields_using_mutable_collections(found) == []


# =============================================================================
# The domain does not name its runner
# =============================================================================


def test_execution_id_is_allowed() -> None:
    """The framework-agnostic word for the same thing."""
    assert (
        fields_named_workflow_id([an_entity(fields=(("execution_id", "str"),))]) == []
    )


def test_workflow_id_is_reported() -> None:
    """Temporal's word for it, leaking into the domain (ADR 004)."""
    found = [an_entity(fields=(("workflow_id", "str"),))]

    assert fields_named_workflow_id(found) == ["hcd.Story.workflow_id"]


def test_a_field_merely_containing_workflow_id_is_allowed() -> None:
    """parent_workflow_id is a different name, and this rule is about one."""
    found = [an_entity(fields=(("parent_workflow_id", "str"),))]

    assert fields_named_workflow_id(found) == []


# =============================================================================
# Nothing at all
# =============================================================================


@pytest.mark.parametrize(
    "rule",
    [
        lambda: entities_not_extending_Entity([]),
        lambda: fields_using_mutable_collections([]),
        lambda: fields_named_workflow_id([]),
    ],
)
def test_a_codebase_with_no_entities_offends_nothing(rule) -> None:
    """A kit of pure use cases has none."""
    assert rule() == []


# =============================================================================
# The canary: doctrine can see the entities it checks
# =============================================================================


def test_a_context_yielding_entities_is_fine() -> None:
    """The ordinary case: doctrine read some, so it was looking correctly."""
    assert contexts_whose_entities_doctrine_cannot_see([a_context()]) == []


def test_a_context_with_use_cases_but_no_entities_is_objected_to() -> None:
    """What #238 looked like: green, and not looking.

    Every entity rule passes on a context like this, having nothing to
    check, and every repository in it is measured against an empty set of
    entity names.
    """
    objections = contexts_whose_entities_doctrine_cannot_see([a_context(entities=0)])

    assert len(objections) == 1
    assert "hcd" in objections[0]


def test_the_objection_says_what_doctrine_did_read() -> None:
    """Whoever reads it needs the asymmetry, not just the absence."""
    contexts = [a_context(entities=0, use_cases=44, repositories=10)]

    objection = contexts_whose_entities_doctrine_cannot_see(contexts)[0]

    assert "44 use cases" in objection
    assert "10 repository protocols" in objection
    assert "domain/models/" in objection


def test_repositories_alone_are_evidence_enough_of_a_domain() -> None:
    """A context of pure protocols still holds something."""
    contexts = [a_context(entities=0, use_cases=0, repositories=2)]

    assert len(contexts_whose_entities_doctrine_cannot_see(contexts)) == 1


def test_a_context_with_no_domain_code_at_all_is_left_alone() -> None:
    """Nothing to be blind to.

    julee's own packages parse this way, and a kit of pure infrastructure
    would too. Objecting here would fail codebases for being small.
    """
    contexts = [a_context(entities=0, use_cases=0, repositories=0)]

    assert contexts_whose_entities_doctrine_cannot_see(contexts) == []


def test_one_blind_context_does_not_hide_behind_a_sighted_one() -> None:
    contexts = [a_context(slug="c4"), a_context(slug="billing", entities=0)]

    objections = contexts_whose_entities_doctrine_cannot_see(contexts)

    assert len(objections) == 1
    assert "billing" in objections[0]


# =============================================================================
# The canary for partial blindness
# =============================================================================


@pytest.mark.parametrize("package", ["models", "repositories", "services"])
def test_a_package_doctrine_reads_is_fine(package: str) -> None:
    assert domain_packages_doctrine_does_not_read([("hcd", package)]) == []


def test_a_package_doctrine_reads_nothing_out_of_is_objected_to() -> None:
    """trust-graph-explorer's case, which the other canary cannot catch.

    Three entities in domain/models/ and Facility in domain/entities/.
    The context yields entities, so it passes the rule above while half
    its domain goes unchecked.
    """
    objections = domain_packages_doctrine_does_not_read([("app", "entities")])

    assert len(objections) == 1
    assert "domain/entities/" in objections[0]


def test_a_context_may_be_partially_blind_and_still_yield_entities() -> None:
    """The two canaries answer different questions.

    Passing the first is not evidence for the second, which is the whole
    reason there are two.
    """
    assert contexts_whose_entities_doctrine_cannot_see([a_context()]) == []
    assert domain_packages_doctrine_does_not_read([("hcd", "entities")]) != []


def test_every_unread_package_is_named_rather_than_just_the_first() -> None:
    packages = [
        ("app", "entities"),
        ("app", "models"),
        ("app", "value_objects"),
    ]

    assert len(domain_packages_doctrine_does_not_read(packages)) == 2


def test_neither_canary_objects_to_an_empty_codebase() -> None:
    """A rule that fires on nothing is a rule nobody can adopt."""
    assert contexts_whose_entities_doctrine_cannot_see([]) == []
    assert domain_packages_doctrine_does_not_read([]) == []

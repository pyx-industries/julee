"""Tests for what the kernel offers a kit to be bound to."""

import pytest

from julee.core.entities import kernel_entity_names

pytestmark = pytest.mark.unit


def test_the_kernel_offers_entities() -> None:
    """The canary.

    An empty set would silently un-widen every rule that reads arity,
    and each of them would go on passing. That is the whole family this
    guards against, and it costs one assertion.
    """
    assert kernel_entity_names()


@pytest.mark.parametrize(
    "name", ["BoundedContextInfo", "ClassInfo", "Accelerator", "Kit"]
)
def test_an_entity_kits_build_on_is_offered(name: str) -> None:
    """Each of these has a kit repository over it today (#237)."""
    assert name in kernel_entity_names()


def test_the_base_class_is_not_itself_an_entity() -> None:
    """Entity is what an entity inherits, not one of them."""
    assert "Entity" not in kernel_entity_names()


def test_a_thing_that_is_not_a_record_is_not_offered() -> None:
    """ContentStream is a stream a repository hands back.

    Binding is about records. Counting this one would object to every
    ceap repository that returns document content alongside its own
    entity.
    """
    assert "ContentStream" not in kernel_entity_names()


def test_nothing_from_outside_the_entities_package_leaks_in() -> None:
    """Imports are read too, so the module of origin is what decides.

    ``BaseModel`` is imported by nearly every entity module; a rule that
    took every BaseModel subclass it found in one would offer it.
    """
    assert "BaseModel" not in kernel_entity_names()

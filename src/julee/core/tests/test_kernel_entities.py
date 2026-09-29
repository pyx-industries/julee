"""Tests for what the kernel offers a kit to be bound to."""

import pytest

from julee.core.doctrine.resolution import (
    domain_class_verdicts,
    mutable_collection_verdicts,
)
from julee.core.doctrine.rules.entity import entities_that_are_not_frozen_dataclasses
from julee.core.entities import kernel_classes, kernel_entity_names

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


class TestTheKernelIsADomainToo:
    """The kernel's entities cross kits' driven ports, so they are
    held to the ring rule the kits are held to.

    Nothing was holding them to it. The domain rule reads a bounded
    context's ``domain/models/``; julee declares it has no bounded
    contexts, so its own entities have never been looked at — and
    ``Accelerator`` is a pydantic model that hcd's repository is bound
    to, which hcd cannot do anything about.
    """

    def test_the_kernel_offers_classes_to_judge(self) -> None:
        """The canary, and the reason discovery is unfiltered.

        ``kernel_entity_names`` keeps only what is a ``BaseModel``, so
        reading it here would empty itself as entities converted and
        this would pass by finding nothing.
        """
        assert kernel_classes()

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "19 kernel entities are still pydantic models and ContentStream "
            "is not a record at all. Strict, so that fixing them fails here "
            "until this marker goes with them — a gap that stops being a gap "
            "and leaves its marker behind is how the next one gets missed."
        ),
    )
    def test_every_kernel_entity_is_a_domain_class(self) -> None:
        """A kernel entity MUST be a frozen dataclass or a value object.

        The same judge the kits get, not a second rule written beside
        it: an entity is a frozen stdlib dataclass, an enum, or built
        on str or int.
        """
        violations = entities_that_are_not_frozen_dataclasses(
            domain_class_verdicts("julee", kernel_classes())
        )

        assert not violations, (
            "Kernel classes that are not domain classes:\n" + "\n".join(violations)
        )

    def test_no_kernel_entity_holds_a_mutable_collection(self) -> None:
        """A kernel entity MUST NOT be annotated with list, set or dict.

        The kits are held to this already. julee has no bounded
        contexts for that rule's source scan to find, so its own
        entities were never asked — the same gap the frozen dataclass
        rule had, and the reason a converted entity could carry a list
        inside a frozen record and nothing would say so.

        Asked of the live annotations rather than the source, so an
        alias or a string annotation cannot hide one.
        """
        violations = entities_that_are_not_frozen_dataclasses(
            mutable_collection_verdicts("julee", kernel_classes())
        )

        assert not violations, (
            "Kernel entities holding a mutable collection:\n" + "\n".join(violations)
        )

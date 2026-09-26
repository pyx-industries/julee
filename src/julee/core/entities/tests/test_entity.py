"""Tests for what an Entity is, and how a new one is made from an old one."""

import pytest
from pydantic import Field, ValidationError, field_validator

from julee.core.entities.entity import Entity

pytestmark = pytest.mark.unit


class _Widget(Entity):
    """An entity with a validator that refuses, and one that coerces."""

    name: str
    tags: tuple[str, ...] = ()
    secret: str = Field(default="", exclude=True)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def tags_are_a_tuple(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(v)


class TestImmutability:
    def test_a_field_cannot_be_reassigned(self) -> None:
        widget = _Widget(name="a")

        with pytest.raises(ValidationError):
            widget.name = "b"  # type: ignore[misc]


class TestEvolve:
    """A new snapshot with some fields changed, validators and all."""

    def test_it_changes_the_field(self) -> None:
        assert _Widget(name="a").evolve(name="b").name == "b"

    def test_it_leaves_the_others_alone(self) -> None:
        widget = _Widget(name="a", tags=("x",))

        assert widget.evolve(name="b").tags == ("x",)

    def test_it_returns_a_new_instance(self) -> None:
        widget = _Widget(name="a")

        assert widget.evolve(name="b") is not widget
        assert widget.name == "a"

    def test_a_validator_that_refuses_runs(self) -> None:
        """The whole difference from model_copy(update=...)."""
        with pytest.raises(ValidationError):
            _Widget(name="a").evolve(name="")

    def test_a_validator_that_coerces_runs_too(self) -> None:
        """The case that actually bit. A validator returning tuple(v) is
        not checking the value, it is deciding what the field holds, and
        skipping it leaves a mutable list on a frozen entity."""
        evolved = _Widget(name="a").evolve(tags=["x", "y"])

        assert evolved.tags == ("x", "y")
        assert isinstance(evolved.tags, tuple)

    def test_model_copy_still_does_not(self) -> None:
        """Written down rather than assumed: pydantic's copy skips
        validation by design, and this says what that costs."""
        copied = _Widget(name="a").model_copy(update={"tags": ["x"]})

        assert isinstance(copied.tags, list)

    def test_changing_nothing_gives_an_equal_entity(self) -> None:
        widget = _Widget(name="a", tags=("x",))

        assert widget.evolve() == widget

    def test_a_field_excluded_from_dumps_survives(self) -> None:
        """Implemented from the field values rather than model_dump(),
        which drops these — a document's content stream is one, and the
        obvious implementation would have lost it silently."""
        widget = _Widget(name="a", secret="s")

        assert "secret" not in widget.model_dump()
        assert widget.evolve(name="b").secret == "s"

    def test_a_subclass_evolves_to_its_own_type(self) -> None:
        class _Gadget(_Widget):
            extra: int = 0

        evolved = _Gadget(name="a", extra=1).evolve(name="b")

        assert isinstance(evolved, _Gadget)
        assert evolved.extra == 1

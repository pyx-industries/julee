"""Tests for turning a contribution path into the thing it names."""

import pytest

from julee.core.kits import resolve_contribution

pytestmark = pytest.mark.unit


def test_a_bare_path_names_the_module() -> None:
    """Which is what Sphinx wants: it takes module paths and imports them."""
    resolved = resolve_contribution("julee.core.kits")

    assert getattr(resolved, "__name__", None) == "julee.core.kits"


def test_a_path_with_an_attribute_names_what_is_inside() -> None:
    """Which is what FastAPI wants: a router is an object in a module."""
    resolved = resolve_contribution("julee.core.kits:adopted_kits")

    assert callable(resolved)
    assert getattr(resolved, "__name__", None) == "adopted_kits"


def test_a_bare_path_does_not_mean_look_inside_for_anything() -> None:
    """The rule that makes the convention worth having.

    A point wanting several things is pointed at something holding them,
    so what a kit offers is written in the kit rather than inferred by
    whoever reads it.
    """
    resolved = resolve_contribution("julee.core.kits")

    assert not isinstance(resolved, list | tuple)


def test_a_path_may_name_a_collection() -> None:
    """Which is how a kit offers several things at one point."""
    resolved = resolve_contribution("julee.core.doctrine.rules.entity:ENUM_INDICATORS")

    assert resolved == {"str", "int", "Enum"}


def test_a_module_that_is_not_there_raises() -> None:
    """Rather than returning None for a caller to trip over later."""
    with pytest.raises(ImportError):
        resolve_contribution("julee.nothing.here")


def test_an_attribute_that_is_not_there_raises() -> None:
    """The failure a rename leaves behind."""
    with pytest.raises(AttributeError):
        resolve_contribution("julee.core.kits:no_such_name")


def test_the_error_names_what_was_being_looked_for() -> None:
    """Whoever sees this at startup needs to know which manifest to fix."""
    with pytest.raises(AttributeError, match="no_such_name"):
        resolve_contribution("julee.core.kits:no_such_name")

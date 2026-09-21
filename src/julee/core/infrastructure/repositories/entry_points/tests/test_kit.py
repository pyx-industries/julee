"""Unit tests for the entry-point kit repository.

The repository is the only thing that loads code a kit provides, so what
it does with a broken kit matters: one bad manifest must not stop a
solution from starting.
"""

from importlib.metadata import EntryPoint

import pytest

from julee.core.entities.kit import Kit
from julee.core.infrastructure.repositories.entry_points import kit as kit_module
from julee.core.infrastructure.repositories.entry_points.kit import (
    EntryPointKitRepository,
)

pytestmark = pytest.mark.unit


class FakeEntryPoint:
    """An entry point whose load() we control."""

    def __init__(self, name: str, value: object | Exception) -> None:
        self.name = name
        self._value = value

    def load(self) -> object:
        if isinstance(self._value, Exception):
            raise self._value
        return self._value


@pytest.fixture
def register(monkeypatch):
    """Install a set of fake entry points in the julee.kits group."""

    def _register(*points: FakeEntryPoint):
        def fake_entry_points(*, group: str):
            assert group == kit_module.ENTRY_POINT_GROUP
            return list(points)

        monkeypatch.setattr(kit_module, "entry_points", fake_entry_points)

    return _register


def a_kit(slug: str = "ceap", **overrides) -> Kit:
    """A minimal valid manifest."""
    fields = {"slug": slug, "name": slug.upper(), "package": f"julee_{slug}"}
    return Kit(**{**fields, **overrides})


def test_lists_installed_kits(register) -> None:
    register(
        FakeEntryPoint("polling", a_kit("polling")), FakeEntryPoint("ceap", a_kit())
    )

    kits = EntryPointKitRepository().list_all_sync()

    assert [kit.slug for kit in kits] == ["ceap", "polling"]


def test_get_returns_none_for_an_uninstalled_slug(register) -> None:
    register(FakeEntryPoint("ceap", a_kit()))

    repository = EntryPointKitRepository()

    assert repository.get_sync("ceap") is not None
    assert repository.get_sync("untp") is None


def test_a_manifest_that_fails_to_load_is_skipped(register) -> None:
    register(
        FakeEntryPoint("broken", ImportError("no such module")),
        FakeEntryPoint("ceap", a_kit()),
    )

    kits = EntryPointKitRepository().list_all_sync()

    assert [kit.slug for kit in kits] == ["ceap"]


def test_a_manifest_that_is_not_a_kit_is_skipped(register) -> None:
    register(
        FakeEntryPoint("wrong", {"slug": "wrong"}),
        FakeEntryPoint("ceap", a_kit()),
    )

    kits = EntryPointKitRepository().list_all_sync()

    assert [kit.slug for kit in kits] == ["ceap"]


def test_the_entry_point_name_wins_over_a_mismatched_slug(register) -> None:
    """The name is how a solution adopts the kit, so it is authoritative."""
    register(FakeEntryPoint("ceap", a_kit(slug="something-else")))

    (kit,) = EntryPointKitRepository().list_all_sync()

    assert kit.slug == "ceap"


def test_real_entry_points_are_read_without_error() -> None:
    """The default construction works against the installed environment."""
    assert isinstance(EntryPointKitRepository().list_all_sync(), list)


def test_entry_point_type_is_what_importlib_provides() -> None:
    """Guard the assumption the fake stands in for."""
    assert hasattr(EntryPoint, "load")

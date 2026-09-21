"""Unit tests for the Kit manifest."""

import pytest
from pydantic import ValidationError

from julee.core.entities.kit import Kit

pytestmark = pytest.mark.unit


def test_a_manifest_needs_only_slug_name_and_package() -> None:
    kit = Kit(slug="ceap", name="CEAP", package="julee_ceap")

    assert kit.requires == ()
    assert dict(kit.contributes) == {}
    assert kit.viewpoint is False
    assert kit.policies == ()


def test_a_manifest_is_immutable() -> None:
    kit = Kit(slug="ceap", name="CEAP", package="julee_ceap")

    with pytest.raises(ValidationError):
        kit.slug = "other"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["slug", "name", "package"])
def test_identifiers_must_not_be_empty(field: str) -> None:
    fields: dict[str, str] = {
        "slug": "ceap",
        "name": "CEAP",
        "package": "julee_ceap",
    }
    fields[field] = "   "

    with pytest.raises(ValidationError):
        Kit(slug=fields["slug"], name=fields["name"], package=fields["package"])


def test_identifiers_are_stripped() -> None:
    kit = Kit(slug=" ceap ", name="CEAP", package=" julee_ceap ")

    assert kit.slug == "ceap"
    assert kit.package == "julee_ceap"

"""Tests for the shared text helpers.

These decide whether two entities refer to the same thing, so the cases
that matter are the ones where different spellings must agree.
"""

import pytest

from julee.core.utils import kebab_to_snake, normalize_name, slugify

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "written",
    ["Data Steward", "data-steward", "data_steward", "  data steward  "],
)
def test_names_that_differ_only_in_spelling_normalise_alike(written: str) -> None:
    assert normalize_name(written) == normalize_name("data steward")


def test_normalising_does_not_collapse_internal_whitespace() -> None:
    """Documented, not endorsed.

    Leading and trailing space goes, but "Data  Steward" with two spaces
    does not match "Data Steward". Every caller compares normalised names
    to find one entity from another's reference, so changing this changes
    what matches; it is a change with its own consequences, not a tidy-up
    to fold into a move.
    """
    assert normalize_name("Data  Steward") != normalize_name("Data Steward")


def test_normalising_leaves_a_name_comparable_not_pretty() -> None:
    """It is for matching, not display: spacing is kept, case is not."""
    assert normalize_name("Upload Document") == "upload document"


@pytest.mark.parametrize(
    ("text", "slug"),
    [
        ("Upload Document", "upload-document"),
        ("Review: the vocabulary!", "review-the-vocabulary"),
        ("already-a-slug", "already-a-slug"),
        ("snake case name", "snake-case-name"),
        ("  leading and trailing  ", "leading-and-trailing"),
        ("multiple   spaces", "multiple-spaces"),
        ("double--hyphen", "double-hyphen"),
        ("-edges-", "edges"),
    ],
)
def test_slugify(text: str, slug: str) -> None:
    assert slugify(text) == slug


def test_slugify_is_idempotent() -> None:
    """A slug of a slug is the same slug, so re-slugging is safe."""
    once = slugify("Some Title: with punctuation")

    assert slugify(once) == once


def test_slugify_drops_characters_it_cannot_represent() -> None:
    assert slugify("café") == "caf"


def test_slugify_drops_underscores_rather_than_converting_them() -> None:
    """Also documented rather than endorsed.

    normalize_name treats an underscore as a space; slugify deletes it.
    So "snake_case_name" slugifies to "snakecasename", not
    "snake-case-name". Anything relying on the two agreeing about
    underscores does not get what it expects.
    """
    assert slugify("snake_case_name") == "snakecasename"


def test_kebab_to_snake() -> None:
    assert kebab_to_snake("audit-analysis") == "audit_analysis"


def test_kebab_to_snake_leaves_a_module_name_alone() -> None:
    assert kebab_to_snake("audit_analysis") == "audit_analysis"

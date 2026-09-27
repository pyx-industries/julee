"""What NonEmptyText, Name and Slug promise.

These absorbed fifty-nine transforming validators across the kits. The
properties each of those was asserting separately are asserted once
here, against the types that carry them now.

The last class is the reason the types exist: two entities naming each
other end up with the same string, which is what the kits got wrong
everywhere one end was stripped and the other slugified.
"""

import pytest
from pydantic import ValidationError

from julee.core.entities import kernel_entity_names
from julee.core.entities.entity import Entity
from julee.core.entities.text import Name, NonEmptyText, Slug


class Referrer(Entity):
    """An entity naming another by slug, for the round-trip tests."""

    slug: Slug
    name: Name
    target_slug: Slug
    note: NonEmptyText


class TestNonEmptyText:
    """Text a caller has to actually supply."""

    def test_it_strips_the_edges(self) -> None:
        """Whitespace around a value is typing, not value."""
        assert NonEmptyText("  doc_123  ") == "doc_123"

    @pytest.mark.parametrize("given", ["", "   ", "\n\t "])
    def test_it_refuses_nothing(self, given: str) -> None:
        """Stripping first is what makes the refusal mean anything.

        Without it, ``"   "`` would be a value and ``""`` would not,
        which is a distinction no domain wants to carry.
        """
        with pytest.raises(ValueError, match="cannot be empty"):
            NonEmptyText(given)


class TestName:
    """Text a person wrote, kept as they wrote it."""

    def test_it_keeps_what_was_written(self) -> None:
        """A name is for reading, so its spelling survives."""
        assert Name("Internet Banking System") == "Internet Banking System"

    @pytest.mark.parametrize(
        "given", ["Data Steward", "data-steward", "data_steward", "DATA STEWARD"]
    )
    def test_names_that_differ_only_in_spelling_compare_equal(self, given: str) -> None:
        """How names are matched, in one place rather than sixty."""
        assert Name(given).normalized == "data steward"

    def test_it_refuses_an_empty_name(self) -> None:
        """Something has to be displayed."""
        with pytest.raises(ValueError, match="a name cannot be empty"):
            Name("   ")


class TestSlug:
    """A URL-safe identifier that normalises itself."""

    @pytest.mark.parametrize(
        ("given", "expected"),
        [
            ("Banking System", "banking-system"),
            ("  Banking System  ", "banking-system"),
            ("banking-system", "banking-system"),
            ("Banking   System", "banking-system"),
            ("Banking, System!", "banking-system"),
        ],
    )
    def test_it_normalises_what_it_is_given(self, given: str, expected: str) -> None:
        """One spelling out, whatever spelling went in."""
        assert Slug(given) == expected

    def test_normalising_twice_changes_nothing(self) -> None:
        """Idempotent, so a slug can be re-made from a slug.

        Deserialisation does exactly that on every read.
        """
        once = Slug("Banking System")
        assert Slug(once) == once

    @pytest.mark.parametrize("given", ["", "   ", "!!!", "---"])
    def test_it_refuses_what_it_cannot_make_a_slug_of(self, given: str) -> None:
        """An empty identifier names everything and nothing."""
        with pytest.raises(ValueError, match="nothing in it that can be a slug"):
            Slug(given)


class TestTheyAreStrings:
    """Being a str is what makes them free to adopt."""

    def test_they_compare_format_and_key_as_strings(self) -> None:
        """Nothing downstream unwraps them."""
        slug = Slug("Banking System")
        assert slug == "banking-system"
        assert f"{slug}/x" == "banking-system/x"
        keyed: dict[str, int] = {slug: 1}
        assert keyed["banking-system"] == 1

    def test_the_serialised_shape_is_a_plain_string(self) -> None:
        """Stored data does not change shape when a kit adopts these."""
        entity = Referrer(
            slug=Slug("a"),
            name=Name("A"),
            target_slug=Slug("b"),
            note=NonEmptyText("n"),
        )

        assert entity.model_dump_json() == (
            '{"slug":"a","name":"A","target_slug":"b","note":"n"}'
        )

    def test_reading_one_back_rebuilds_the_type(self) -> None:
        """A slug read from storage is a Slug, not a str that looks like one."""
        entity = Referrer(
            slug=Slug("A Thing"),
            name=Name("A Thing"),
            target_slug=Slug("b"),
            note=NonEmptyText("n"),
        )

        read_back = Referrer.model_validate_json(entity.model_dump_json())

        assert isinstance(read_back.slug, Slug)
        assert read_back.slug == "a-thing"

    def test_evolve_normalises_and_model_copy_does_not(self) -> None:
        """The distinction Entity.evolve exists for, in one assertion.

        ``model_copy(update=...)`` does not validate, by design, so it
        writes whatever it is handed — here a plain str where the
        annotation says Slug. ``evolve`` goes through the schema, so the
        value is constructed.
        """
        entity = Referrer(
            slug=Slug("a"),
            name=Name("A"),
            target_slug=Slug("b"),
            note=NonEmptyText("n"),
        )

        assert isinstance(entity.evolve(slug="Another Thing").slug, Slug)
        assert not isinstance(entity.model_copy(update={"slug": "Raw"}).slug, Slug)

    def test_an_entity_refuses_stored_data_the_type_would_refuse(self) -> None:
        """The rule holds on the way in from storage, not only in Python."""
        with pytest.raises(ValidationError):
            Referrer.model_validate(
                {"slug": "", "name": "A", "target_slug": "b", "note": "n"}
            )


class TestTheyAreNotEntities:
    """A value object is not something a repository is bound to.

    julee-kits#69 put a value object under ``domain/models/`` and
    doctrine objected that the repository referenced two entity types —
    correctly, by its own rules. These do not have that problem for a
    reason worth pinning down rather than relying on: they are not
    ``BaseModel`` subclasses, so entity discovery does not collect them,
    the same reason ``ContentStream`` is not collected.
    """

    def test_the_kernel_does_not_offer_them_as_entities(self) -> None:
        """A protocol taking a Slug is not bound to a second entity."""
        offered = kernel_entity_names()

        assert not {"NonEmptyText", "Name", "Slug"} & set(offered)
        assert "Accelerator" in offered, (
            "discovery found nothing, so this proves nothing"
        )


class TestReferencesMatchWhatTheyName:
    """The defect the types exist to make impossible (julee-kits#70).

    A slug field was slugified and a field *naming* that slug was only
    stripped, so an entity could name another that could not be found.
    Nothing raised; the lookup came back empty.
    """

    def test_both_ends_of_a_reference_are_written_the_same_way(self) -> None:
        """However the author spelled it at either end."""
        target = Referrer(
            slug=Slug("Web Application"),
            name=Name("Web"),
            target_slug=Slug("x"),
            note=NonEmptyText("n"),
        )
        referrer = Referrer(
            slug=Slug("api"),
            name=Name("API"),
            target_slug=Slug("web application"),
            note=NonEmptyText("n"),
        )

        assert referrer.target_slug == target.slug

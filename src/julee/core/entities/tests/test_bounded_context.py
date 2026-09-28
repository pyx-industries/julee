"""What a BoundedContext insists on about its own slug.

The slug is how a context is named everywhere else — in an import
path, in a doctrine objection, as a repository key — so a padded or
empty one is not a cosmetic problem. Nothing exercised this until the
entity became a frozen dataclass and the check moved with it.
"""

import pytest

from julee.core.entities.bounded_context import BoundedContext, StructuralMarkers

pytestmark = pytest.mark.unit


class TestTheSlug:
    """Checked and trimmed on the way in."""

    def test_it_is_trimmed(self) -> None:
        """A padded slug would not match its own import path.

        Asserting the stored value: a test that only built one without
        raising would pass with the trimming deleted.
        """
        assert BoundedContext(slug="  polling  ", path="src/polling").slug == "polling"

    @pytest.mark.parametrize("slug", ["", "   "])
    def test_an_empty_slug_is_refused(self, slug: str) -> None:
        """A context with no name cannot be referred to at all."""
        with pytest.raises(ValueError, match="slug cannot be empty"):
            BoundedContext(slug=slug, path="src/nowhere")


class TestWhatItDerives:
    """Everything else is read off the path or the slug."""

    def test_the_import_path_is_what_follows_src(self) -> None:
        """How a context is imported, not where its files sit."""
        context = BoundedContext(slug="polling", path="/a/b/src/julee_polling")

        assert context.import_path == "julee_polling"

    def test_a_path_with_no_src_keeps_its_parts(self) -> None:
        """The fallback, which is a different branch."""
        assert BoundedContext(slug="x", path="a/b").import_path == "a.b"

    def test_the_display_name_is_the_slug_made_readable(self) -> None:
        """Both separators, so neither replacement can be dropped."""
        context = BoundedContext(slug="human-centred_design", path="p")

        assert context.display_name == "Human Centred Design"


class TestTheLayersItReports:
    """has_layer answers from the markers it was given."""

    def test_a_layer_it_has(self) -> None:
        """The marker is read, not guessed from the path."""
        context = BoundedContext(
            slug="x", path="p", markers=StructuralMarkers(has_domain_models=True)
        )

        assert context.has_layer("models") is True

    def test_a_layer_it_does_not_have(self) -> None:
        """Absent markers are absent layers."""
        assert BoundedContext(slug="x", path="p").has_layer("models") is False

    def test_a_layer_that_is_not_one(self) -> None:
        """An unknown name is False rather than an error."""
        assert BoundedContext(slug="x", path="p").has_layer("nonsense") is False

    def test_clean_architecture_needs_models_or_use_cases(self) -> None:
        """Repositories alone do not make a context an architecture."""
        markers = StructuralMarkers(has_domain_repositories=True)

        assert markers.has_clean_architecture_layers is False

    def test_use_cases_alone_are_enough(self) -> None:
        """The second half of the or, which the first test cannot reach."""
        markers = StructuralMarkers(has_domain_use_cases=True)

        assert markers.has_clean_architecture_layers is True


class TestItIsARecord:
    """An entity, so it is immutable."""

    def test_it_cannot_be_changed(self) -> None:
        """Renaming a context after discovery would strand its key."""
        context = BoundedContext(slug="polling", path="p")

        with pytest.raises(AttributeError):
            context.slug = "something-else"  # type: ignore[misc]

    def test_each_one_gets_its_own_markers(self) -> None:
        """A shared default would let one context's markers be another's."""
        first = BoundedContext(slug="a", path="p")
        second = BoundedContext(slug="b", path="p")

        assert first.markers is not second.markers

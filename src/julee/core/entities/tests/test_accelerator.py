"""What an Accelerator insists on, and what it answers about itself.

Nothing in julee ever builds one — hcd does, and hcd's tests covered
hcd's use of it. So the slug check and the lookup helpers travelled
from a pydantic validator into __post_init__ with nothing here
watching.
"""

import pytest

from julee.core.entities.accelerator import (
    Accelerator,
    AcceleratorValidationIssue,
    IntegrationReference,
)

pytestmark = pytest.mark.unit


class TestTheSlug:
    """Checked and trimmed, on both entities that carry one."""

    def test_an_accelerator_slug_is_trimmed(self) -> None:
        """A padded slug would stop matching the references to it.

        Asserting the stored value: a test that only constructed one
        without raising would pass with the trimming deleted.
        """
        assert Accelerator(slug="  vocabulary  ").slug == "vocabulary"

    def test_an_integration_reference_slug_is_trimmed(self) -> None:
        """The same check, and it is the same function."""
        assert IntegrationReference(slug=" feed ").slug == "feed"

    @pytest.mark.parametrize("slug", ["", "   "])
    def test_an_empty_accelerator_slug_is_refused(self, slug: str) -> None:
        """An accelerator nothing can refer to is not one."""
        with pytest.raises(ValueError, match="slug cannot be empty"):
            Accelerator(slug=slug)

    @pytest.mark.parametrize("slug", ["", "   "])
    def test_an_empty_reference_slug_is_refused(self, slug: str) -> None:
        """A reference to nothing is not a reference."""
        with pytest.raises(ValueError, match="slug cannot be empty"):
            IntegrationReference(slug=slug)


class TestBuildingAReferenceFromWhatAManifestSaid:
    """A manifest gives either a bare slug or a slug with a description."""

    def test_a_bare_string_is_a_reference_with_no_description(self) -> None:
        """The short form."""
        reference = IntegrationReference.from_dict("pilot-data-collection")

        assert reference.slug == "pilot-data-collection"
        assert reference.description == ""

    def test_a_mapping_carries_the_description_too(self) -> None:
        """The long form."""
        reference = IntegrationReference.from_dict(
            {"slug": "pilot-data-collection", "description": "Scheme documentation"}
        )

        assert reference.description == "Scheme documentation"

    def test_a_mapping_with_no_slug_is_refused(self) -> None:
        """from_dict defaults the slug to "", which is not a slug.

        The refusal comes from the field rather than from here, and it
        has to keep coming: a manifest entry with a description and no
        slug is a typo, not a reference.
        """
        with pytest.raises(ValueError, match="slug cannot be empty"):
            IntegrationReference.from_dict({"description": "no slug given"})


class TestWhatItKnowsAboutItsDependencies:
    """Asked by slug, answered from what it carries."""

    def an_accelerator(self) -> Accelerator:
        """One that reads from a feed and writes to a register."""
        return Accelerator(
            slug="vocabulary",
            sources_from=(IntegrationReference(slug="feed", description="Terms"),),
            publishes_to=(IntegrationReference(slug="register"),),
            depends_on=("taxonomy",),
            feeds_into=("search",),
        )

    def test_an_integration_it_reads_from(self) -> None:
        """The sources_from half."""
        assert self.an_accelerator().has_integration_dependency("feed") is True

    def test_an_integration_it_writes_to(self) -> None:
        """The publishes_to half, which the first cannot reach."""
        assert self.an_accelerator().has_integration_dependency("register") is True

    def test_an_integration_it_has_nothing_to_do_with(self) -> None:
        """Neither half."""
        assert self.an_accelerator().has_integration_dependency("other") is False

    def test_an_accelerator_it_depends_on(self) -> None:
        """The depends_on half."""
        assert self.an_accelerator().has_accelerator_dependency("taxonomy") is True

    def test_an_accelerator_it_feeds(self) -> None:
        """The feeds_into half, which the first cannot reach."""
        assert self.an_accelerator().has_accelerator_dependency("search") is True

    def test_an_accelerator_it_does_not_know(self) -> None:
        """Neither half."""
        assert self.an_accelerator().has_accelerator_dependency("nothing") is False

    def test_the_description_of_something_it_reads_from(self) -> None:
        """Looked up by relationship, not searched across both."""
        found = self.an_accelerator().get_integration_description(
            "feed", "sources_from"
        )

        assert found == "Terms"

    def test_a_reference_with_no_description_answers_None(self) -> None:
        """An empty description is not a description."""
        found = self.an_accelerator().get_integration_description(
            "register", "publishes_to"
        )

        assert found is None

    def test_looking_in_the_wrong_relationship_finds_nothing(self) -> None:
        """ "feed" is a source, so it is not among what is published."""
        found = self.an_accelerator().get_integration_description(
            "feed", "publishes_to"
        )

        assert found is None

    def test_it_lists_what_it_reads_from(self) -> None:
        """Slugs, for a caller that only wants the names."""
        assert self.an_accelerator().get_sources_from_slugs() == ["feed"]

    def test_it_lists_what_it_writes_to(self) -> None:
        """The other side."""
        assert self.an_accelerator().get_publishes_to_slugs() == ["register"]


class TestHowItPresentsItself:
    """Derived from the slug and the status."""

    def test_the_title_is_the_slug_made_readable(self) -> None:
        """Hyphens become spaces and the words are capitalised."""
        assert Accelerator(slug="pilot-data").display_title == "Pilot Data"

    def test_the_status_is_normalised_for_grouping(self) -> None:
        """Compared in one case, with no padding."""
        assert Accelerator(slug="a", status="  Alpha ").status_normalized == "alpha"

    def test_no_status_normalises_to_nothing(self) -> None:
        """Rather than raising on the empty string."""
        assert Accelerator(slug="a").status_normalized == ""


class TestTheyAreRecords:
    """All three are entities, so none can be changed."""

    def test_an_accelerator_cannot_be_changed(self) -> None:
        """Renaming one would strand every reference to it."""
        with pytest.raises(AttributeError):
            Accelerator(slug="a").slug = "b"  # type: ignore[misc]

    def test_a_reference_cannot_be_changed(self) -> None:
        """It is a fact about a manifest, not a working value."""
        with pytest.raises(AttributeError):
            IntegrationReference(slug="a").slug = "b"  # type: ignore[misc]

    def test_an_issue_cannot_be_changed(self) -> None:
        """A finding is a finding."""
        issue = AcceleratorValidationIssue(
            slug="a", issue_type="no_code", message="nothing in src/a/"
        )

        with pytest.raises(AttributeError):
            issue.message = "something else"  # type: ignore[misc]

    def test_an_issue_says_which_accelerator_and_why(self) -> None:
        """All three fields are required; none is guessed."""
        issue = AcceleratorValidationIssue(
            slug="a", issue_type="no_code", message="nothing in src/a/"
        )

        assert (issue.slug, issue.issue_type) == ("a", "no_code")

"""Tests for resolve_story_references use case."""

from julee.hcd.domain.models.epic import Epic
from julee.hcd.domain.models.journey import Journey, JourneyStep
from julee.hcd.domain.models.story import Story
from julee.hcd.domain.use_cases.resolve_story_references import (
    get_epics_for_story,
    get_journeys_for_story,
    get_related_stories,
    get_story_cross_references,
)


def create_story(feature_title: str, app_slug: str = "test-app") -> Story:
    """Helper to create test stories."""
    return Story(
        slug=feature_title.lower().replace(" ", "-"),
        feature_title=feature_title,
        persona="Test User",
        i_want="test",
        so_that="verify",
        app_slug=app_slug,
        file_path="test.feature",
    )


def create_epic(slug: str, story_refs: list[str]) -> Epic:
    """Helper to create test epics."""
    return Epic(slug=slug, story_refs=story_refs)


def create_journey(slug: str, story_refs: list[str]) -> Journey:
    """Helper to create test journeys."""
    steps = [JourneyStep.story(ref) for ref in story_refs]
    return Journey(slug=slug, persona="User", steps=steps)


class TestGetEpicsForStory:
    """Test get_epics_for_story function."""

    def test_find_single_epic(self) -> None:
        """Test finding a story in one epic."""
        story = create_story("Upload Document")
        epics = [
            create_epic(
                "vocabulary-management", ["Upload Document", "Review Vocabulary"]
            ),
            create_epic("other-epic", ["Other Story"]),
        ]

        result = get_epics_for_story(story, epics)

        assert len(result) == 1
        assert result[0].slug == "vocabulary-management"

    def test_find_multiple_epics(self) -> None:
        """Test finding a story in multiple epics."""
        story = create_story("Upload Document")
        epics = [
            create_epic("vocabulary-management", ["Upload Document"]),
            create_epic("document-processing", ["Upload Document", "Process Document"]),
        ]

        result = get_epics_for_story(story, epics)

        assert len(result) == 2
        slugs = {e.slug for e in result}
        assert slugs == {"vocabulary-management", "document-processing"}

    def test_case_insensitive_matching(self) -> None:
        """Test that matching is case-insensitive."""
        story = create_story("Upload Document")
        epics = [create_epic("test-epic", ["upload document"])]  # lowercase

        result = get_epics_for_story(story, epics)

        assert len(result) == 1

    def test_no_matching_epics(self) -> None:
        """Test when story is not in any epic."""
        story = create_story("Unknown Story")
        epics = [create_epic("test-epic", ["Other Story"])]

        result = get_epics_for_story(story, epics)

        assert result == []

    def test_sorted_by_slug(self) -> None:
        """Test results are sorted by slug."""
        story = create_story("Shared Story")
        epics = [
            create_epic("zebra-epic", ["Shared Story"]),
            create_epic("alpha-epic", ["Shared Story"]),
        ]

        result = get_epics_for_story(story, epics)

        slugs = [e.slug for e in result]
        assert slugs == ["alpha-epic", "zebra-epic"]


class TestGetJourneysForStory:
    """Test get_journeys_for_story function."""

    def test_find_single_journey(self) -> None:
        """Test finding a story in one journey."""
        story = create_story("Upload Document")
        journeys = [
            create_journey("build-vocabulary", ["Upload Document"]),
            create_journey("other-journey", ["Other Story"]),
        ]

        result = get_journeys_for_story(story, journeys)

        assert len(result) == 1
        assert result[0].slug == "build-vocabulary"

    def test_find_multiple_journeys(self) -> None:
        """Test finding a story in multiple journeys."""
        story = create_story("Upload Document")
        journeys = [
            create_journey("journey-1", ["Upload Document"]),
            create_journey("journey-2", ["Upload Document", "Other Story"]),
        ]

        result = get_journeys_for_story(story, journeys)

        assert len(result) == 2

    def test_no_matching_journeys(self) -> None:
        """Test when story is not in any journey."""
        story = create_story("Unknown Story")
        journeys = [create_journey("test", ["Other Story"])]

        result = get_journeys_for_story(story, journeys)

        assert result == []


class TestGetRelatedStories:
    """Test get_related_stories function."""

    def test_find_related_stories(self) -> None:
        """Test finding stories in same epic."""
        stories = [
            create_story("Upload Document"),
            create_story("Review Vocabulary"),
            create_story("Publish Catalog"),
            create_story("Unrelated Story"),
        ]
        epics = [
            create_epic(
                "vocabulary-management",
                ["Upload Document", "Review Vocabulary", "Publish Catalog"],
            ),
        ]

        result = get_related_stories(stories[0], stories, epics)

        assert len(result) == 2
        titles = {s.feature_title for s in result}
        assert titles == {"Review Vocabulary", "Publish Catalog"}

    def test_excludes_original_story(self) -> None:
        """Test that original story is excluded from results."""
        stories = [create_story("Upload Document")]
        epics = [create_epic("test-epic", ["Upload Document"])]

        result = get_related_stories(stories[0], stories, epics)

        assert result == []

    def test_multiple_epics(self) -> None:
        """Test finding related stories across multiple epics."""
        stories = [
            create_story("Shared Story"),
            create_story("Epic1 Story"),
            create_story("Epic2 Story"),
        ]
        epics = [
            create_epic("epic-1", ["Shared Story", "Epic1 Story"]),
            create_epic("epic-2", ["Shared Story", "Epic2 Story"]),
        ]

        result = get_related_stories(stories[0], stories, epics)

        assert len(result) == 2
        titles = {s.feature_title for s in result}
        assert titles == {"Epic1 Story", "Epic2 Story"}

    def test_sorted_by_feature_title(self) -> None:
        """Test results are sorted by feature title."""
        stories = [
            create_story("Main Story"),
            create_story("Zebra Story"),
            create_story("Alpha Story"),
        ]
        epics = [create_epic("test", ["Main Story", "Zebra Story", "Alpha Story"])]

        result = get_related_stories(stories[0], stories, epics)

        titles = [s.feature_title for s in result]
        assert titles == ["Alpha Story", "Zebra Story"]


class TestGetStoryCrossReferences:
    """Test get_story_cross_references function."""

    def test_cross_references(self) -> None:
        """Test getting all cross-references for a story."""
        stories = [
            create_story("Upload Document"),
            create_story("Review Vocabulary"),
        ]
        epics = [
            create_epic(
                "vocabulary-management", ["Upload Document", "Review Vocabulary"]
            ),
        ]
        journeys = [
            create_journey("build-vocabulary", ["Upload Document"]),
        ]

        result = get_story_cross_references(stories[0], stories, epics, journeys)

        assert len(result["epics"]) == 1
        assert len(result["journeys"]) == 1
        assert len(result["related_stories"]) == 1
        assert result["related_stories"][0].feature_title == "Review Vocabulary"

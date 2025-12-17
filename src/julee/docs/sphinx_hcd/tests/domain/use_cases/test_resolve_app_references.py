"""Tests for resolve_app_references use case."""

import pytest

from julee.docs.sphinx_hcd.domain.models.app import App, AppType
from julee.docs.sphinx_hcd.domain.models.epic import Epic
from julee.docs.sphinx_hcd.domain.models.journey import Journey, JourneyStep
from julee.docs.sphinx_hcd.domain.models.story import Story
from julee.docs.sphinx_hcd.domain.use_cases.resolve_app_references import (
    get_app_cross_references,
    get_epics_for_app,
    get_journeys_for_app,
    get_personas_for_app,
    get_stories_for_app,
)


def create_app(slug: str, name: str = "") -> App:
    """Helper to create test apps."""
    return App(
        slug=slug,
        name=name or slug.replace("-", " ").title(),
        app_type=AppType.STAFF,
        manifest_path=f"apps/{slug}/app.yaml",
    )


def create_story(
    feature_title: str,
    app_slug: str,
    persona: str = "Test User",
) -> Story:
    """Helper to create test stories."""
    return Story(
        slug=feature_title.lower().replace(" ", "-"),
        feature_title=feature_title,
        persona=persona,
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


class TestGetStoriesForApp:
    """Test get_stories_for_app function."""

    def test_find_stories(self) -> None:
        """Test finding stories for an app."""
        app = create_app("vocabulary-tool")
        stories = [
            create_story("Upload Document", "vocabulary-tool"),
            create_story("Review Vocabulary", "vocabulary-tool"),
            create_story("Other Feature", "other-app"),
        ]

        result = get_stories_for_app(app, stories)

        assert len(result) == 2
        titles = {s.feature_title for s in result}
        assert titles == {"Upload Document", "Review Vocabulary"}

    def test_no_stories(self) -> None:
        """Test when app has no stories."""
        app = create_app("empty-app")
        stories = [create_story("Feature", "other-app")]

        result = get_stories_for_app(app, stories)

        assert result == []

    def test_sorted_by_feature_title(self) -> None:
        """Test results are sorted by feature title."""
        app = create_app("test-app")
        stories = [
            create_story("Zebra Feature", "test-app"),
            create_story("Alpha Feature", "test-app"),
        ]

        result = get_stories_for_app(app, stories)

        titles = [s.feature_title for s in result]
        assert titles == ["Alpha Feature", "Zebra Feature"]


class TestGetPersonasForApp:
    """Test get_personas_for_app function."""

    def test_find_personas(self) -> None:
        """Test finding personas that use an app."""
        app = create_app("vocabulary-tool")
        stories = [
            create_story("Upload Document", "vocabulary-tool", "Knowledge Curator"),
            create_story("Review Document", "vocabulary-tool", "Reviewer"),
            create_story("Other Feature", "other-app", "Other User"),
        ]
        epics: list[Epic] = []

        result = get_personas_for_app(app, stories, epics)

        assert len(result) == 2
        names = {p.name for p in result}
        assert names == {"Knowledge Curator", "Reviewer"}

    def test_single_persona_multiple_stories(self) -> None:
        """Test persona appears once even with multiple stories."""
        app = create_app("vocabulary-tool")
        stories = [
            create_story("Upload Document", "vocabulary-tool", "Curator"),
            create_story("Review Document", "vocabulary-tool", "Curator"),
        ]
        epics: list[Epic] = []

        result = get_personas_for_app(app, stories, epics)

        assert len(result) == 1
        assert result[0].name == "Curator"

    def test_sorted_by_name(self) -> None:
        """Test results are sorted by name."""
        app = create_app("test-app")
        stories = [
            create_story("Feature Z", "test-app", "Zebra User"),
            create_story("Feature A", "test-app", "Alpha User"),
        ]
        epics: list[Epic] = []

        result = get_personas_for_app(app, stories, epics)

        names = [p.name for p in result]
        assert names == ["Alpha User", "Zebra User"]


class TestGetJourneysForApp:
    """Test get_journeys_for_app function."""

    def test_find_journeys(self) -> None:
        """Test finding journeys containing app's stories."""
        app = create_app("vocabulary-tool")
        stories = [
            create_story("Upload Document", "vocabulary-tool"),
            create_story("Other Feature", "other-app"),
        ]
        journeys = [
            create_journey("build-vocabulary", ["Upload Document"]),
            create_journey("other-journey", ["Other Feature"]),
        ]

        result = get_journeys_for_app(app, stories, journeys)

        assert len(result) == 1
        assert result[0].slug == "build-vocabulary"

    def test_no_journeys(self) -> None:
        """Test when app's stories are not in any journey."""
        app = create_app("vocabulary-tool")
        stories = [create_story("Lonely Feature", "vocabulary-tool")]
        journeys = [create_journey("other-journey", ["Other Story"])]

        result = get_journeys_for_app(app, stories, journeys)

        assert result == []

    def test_no_stories(self) -> None:
        """Test when app has no stories."""
        app = create_app("empty-app")
        stories = [create_story("Feature", "other-app")]
        journeys = [create_journey("test", ["Feature"])]

        result = get_journeys_for_app(app, stories, journeys)

        assert result == []


class TestGetEpicsForApp:
    """Test get_epics_for_app function."""

    def test_find_epics(self) -> None:
        """Test finding epics containing app's stories."""
        app = create_app("vocabulary-tool")
        stories = [
            create_story("Upload Document", "vocabulary-tool"),
            create_story("Other Feature", "other-app"),
        ]
        epics = [
            create_epic("vocabulary-management", ["Upload Document"]),
            create_epic("other-epic", ["Other Feature"]),
        ]

        result = get_epics_for_app(app, stories, epics)

        assert len(result) == 1
        assert result[0].slug == "vocabulary-management"

    def test_multiple_epics(self) -> None:
        """Test finding multiple epics."""
        app = create_app("vocabulary-tool")
        stories = [
            create_story("Upload Document", "vocabulary-tool"),
            create_story("Review Document", "vocabulary-tool"),
        ]
        epics = [
            create_epic("epic-1", ["Upload Document"]),
            create_epic("epic-2", ["Review Document"]),
        ]

        result = get_epics_for_app(app, stories, epics)

        assert len(result) == 2

    def test_no_stories_for_app(self) -> None:
        """Test when app has no stories at all."""
        app = create_app("empty-app")
        stories = [create_story("Feature", "other-app")]
        epics = [create_epic("some-epic", ["Feature"])]

        result = get_epics_for_app(app, stories, epics)

        assert result == []

    def test_no_epics_contain_app_stories(self) -> None:
        """Test when app has stories but no epics reference them."""
        app = create_app("vocabulary-tool")
        stories = [create_story("Lonely Feature", "vocabulary-tool")]
        epics = [create_epic("other-epic", ["Other Feature"])]

        result = get_epics_for_app(app, stories, epics)

        assert result == []


class TestGetAppCrossReferences:
    """Test get_app_cross_references function."""

    def test_cross_references(self) -> None:
        """Test getting all cross-references for an app."""
        app = create_app("vocabulary-tool")
        stories = [
            create_story("Upload Document", "vocabulary-tool", "Curator"),
            create_story("Review Document", "vocabulary-tool", "Reviewer"),
        ]
        epics = [
            create_epic("vocabulary-management", ["Upload Document", "Review Document"]),
        ]
        journeys = [
            create_journey("build-vocabulary", ["Upload Document"]),
        ]

        result = get_app_cross_references(app, stories, epics, journeys)

        assert len(result["stories"]) == 2
        assert len(result["personas"]) == 2
        assert len(result["journeys"]) == 1
        assert len(result["epics"]) == 1

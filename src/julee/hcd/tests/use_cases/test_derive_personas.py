"""Tests for derive_personas use case."""

import pytest

from julee.hcd.entities.app import App, AppType
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.story import Story
from julee.hcd.use_cases.derive_personas import (
    derive_personas,
    derive_personas_by_app_type,
    get_apps_for_persona,
    get_epics_for_persona,
)


def create_story(
    feature_title: str,
    persona: str,
    app_slug: str,
) -> Story:
    """Helper to create test stories."""
    return Story(
        slug=feature_title.lower().replace(" ", "-"),
        feature_title=feature_title,
        persona=persona,
        i_want="test want",
        so_that="test outcome",
        app_slug=app_slug,
        file_path=f"features/{app_slug}.feature",
    )


def create_epic(
    slug: str,
    story_refs: list[str],
) -> Epic:
    """Helper to create test epics."""
    return Epic(
        slug=slug,
        description=f"Epic for {slug}",
        story_refs=story_refs,
    )


def create_app(
    slug: str,
    name: str,
    app_type: AppType = AppType.STAFF,
) -> App:
    """Helper to create test apps."""
    return App(
        slug=slug,
        name=name,
        app_type=app_type,
        manifest_path=f"apps/{slug}/app.yaml",
    )


class TestDerivePersonas:
    """Test derive_personas function."""

    def test_derive_single_persona(self) -> None:
        """Test deriving a single persona from stories."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("Review Vocabulary", "Knowledge Curator", "vocabulary-tool"),
        ]
        epics: list[Epic] = []

        personas = derive_personas(stories, epics)

        assert len(personas) == 1
        assert personas[0].name == "Knowledge Curator"
        assert personas[0].app_slugs == ["vocabulary-tool"]

    def test_derive_multiple_personas(self) -> None:
        """Test deriving multiple personas from stories."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("Run Analysis", "Analyst", "analytics-app"),
            create_story("Configure System", "Administrator", "admin-portal"),
        ]
        epics: list[Epic] = []

        personas = derive_personas(stories, epics)

        assert len(personas) == 3
        names = [p.name for p in personas]
        assert "Administrator" in names
        assert "Analyst" in names
        assert "Knowledge Curator" in names

    def test_derive_persona_with_multiple_apps(self) -> None:
        """Test persona using multiple apps."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("Manage Users", "Knowledge Curator", "admin-portal"),
            create_story("Review Data", "Knowledge Curator", "analytics-app"),
        ]
        epics: list[Epic] = []

        personas = derive_personas(stories, epics)

        assert len(personas) == 1
        persona = personas[0]
        assert set(persona.app_slugs) == {
            "vocabulary-tool",
            "admin-portal",
            "analytics-app",
        }

    def test_derive_persona_with_epics(self) -> None:
        """Test persona epic association."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("Review Vocabulary", "Knowledge Curator", "vocabulary-tool"),
        ]
        epics = [
            create_epic(
                "vocabulary-management", ["Upload Document", "Review Vocabulary"]
            ),
            create_epic(
                "credential-creation", ["Create Credential"]
            ),  # Different persona
        ]

        personas = derive_personas(stories, epics)

        assert len(personas) == 1
        persona = personas[0]
        assert persona.epic_slugs == ["vocabulary-management"]

    def test_derive_skips_unknown_persona(self) -> None:
        """Test that 'unknown' persona is skipped."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("Unknown Feature", "unknown", "some-app"),
        ]
        epics: list[Epic] = []

        personas = derive_personas(stories, epics)

        assert len(personas) == 1
        assert personas[0].name == "Knowledge Curator"

    def test_derive_empty_lists(self) -> None:
        """Test with empty input lists."""
        personas = derive_personas([], [])
        assert personas == []

    def test_derive_sorted_by_name(self) -> None:
        """Test personas are sorted by name."""
        stories = [
            create_story("Feature Z", "Zebra User", "app-z"),
            create_story("Feature A", "Alpha User", "app-a"),
            create_story("Feature M", "Middle User", "app-m"),
        ]
        epics: list[Epic] = []

        personas = derive_personas(stories, epics)

        names = [p.name for p in personas]
        assert names == ["Alpha User", "Middle User", "Zebra User"]


class TestDerivePersonasByAppType:
    """Test derive_personas_by_app_type function."""

    def test_group_by_app_type(self) -> None:
        """Test grouping personas by app type."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("View Portal", "Customer", "customer-portal"),
        ]
        epics: list[Epic] = []
        apps = [
            create_app("vocabulary-tool", "Vocabulary Tool", AppType.STAFF),
            create_app("customer-portal", "Customer Portal", AppType.EXTERNAL),
        ]

        personas_by_type = derive_personas_by_app_type(stories, epics, apps)

        assert "staff" in personas_by_type
        assert "external" in personas_by_type
        assert len(personas_by_type["staff"]) == 1
        assert personas_by_type["staff"][0].name == "Knowledge Curator"
        assert len(personas_by_type["external"]) == 1
        assert personas_by_type["external"][0].name == "Customer"

    def test_persona_in_multiple_types(self) -> None:
        """Test persona using apps of different types."""
        stories = [
            create_story("Upload Document", "Power User", "staff-tool"),
            create_story("View Portal", "Power User", "external-portal"),
        ]
        epics: list[Epic] = []
        apps = [
            create_app("staff-tool", "Staff Tool", AppType.STAFF),
            create_app("external-portal", "External Portal", AppType.EXTERNAL),
        ]

        personas_by_type = derive_personas_by_app_type(stories, epics, apps)

        # Power User appears in both groups
        assert any(p.name == "Power User" for p in personas_by_type.get("staff", []))
        assert any(p.name == "Power User" for p in personas_by_type.get("external", []))

    def test_unknown_app_type(self) -> None:
        """Test handling of unknown app type."""
        stories = [
            create_story("Upload Document", "User", "unknown-app"),
        ]
        epics: list[Epic] = []
        apps: list[App] = []  # No app definitions

        personas_by_type = derive_personas_by_app_type(stories, epics, apps)

        assert "unknown" in personas_by_type
        assert len(personas_by_type["unknown"]) == 1


class TestGetEpicsForPersona:
    """Test get_epics_for_persona function."""

    @pytest.fixture
    def sample_data(self) -> tuple[list[Story], list[Epic]]:
        """Create sample test data."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("Review Vocabulary", "Knowledge Curator", "vocabulary-tool"),
            create_story("Run Analysis", "Analyst", "analytics-app"),
        ]
        epics = [
            create_epic(
                "vocabulary-management", ["Upload Document", "Review Vocabulary"]
            ),
            create_epic("analytics", ["Run Analysis"]),
            create_epic("mixed-epic", ["Upload Document", "Run Analysis"]),
        ]
        return stories, epics

    def test_get_epics_for_persona(
        self, sample_data: tuple[list[Story], list[Epic]]
    ) -> None:
        """Test getting epics for a persona."""
        stories, epics = sample_data
        all_personas = derive_personas(stories, epics)
        curator = next(p for p in all_personas if p.name == "Knowledge Curator")

        persona_epics = get_epics_for_persona(curator, epics, stories)

        assert len(persona_epics) == 2
        slugs = {e.slug for e in persona_epics}
        assert slugs == {"vocabulary-management", "mixed-epic"}

    def test_get_epics_sorted_by_slug(
        self, sample_data: tuple[list[Story], list[Epic]]
    ) -> None:
        """Test epics are sorted by slug."""
        stories, epics = sample_data
        all_personas = derive_personas(stories, epics)
        curator = next(p for p in all_personas if p.name == "Knowledge Curator")

        persona_epics = get_epics_for_persona(curator, epics, stories)

        slugs = [e.slug for e in persona_epics]
        assert slugs == sorted(slugs)


class TestGetAppsForPersona:
    """Test get_apps_for_persona function."""

    def test_get_apps_for_persona(self) -> None:
        """Test getting apps for a persona."""
        stories = [
            create_story("Upload Document", "Knowledge Curator", "vocabulary-tool"),
            create_story("Admin Task", "Knowledge Curator", "admin-portal"),
        ]
        epics: list[Epic] = []
        apps = [
            create_app("vocabulary-tool", "Vocabulary Tool"),
            create_app("admin-portal", "Admin Portal"),
            create_app("other-app", "Other App"),  # Not used by this persona
        ]

        all_personas = derive_personas(stories, epics)
        curator = all_personas[0]

        persona_apps = get_apps_for_persona(curator, apps)

        assert len(persona_apps) == 2
        slugs = {a.slug for a in persona_apps}
        assert slugs == {"vocabulary-tool", "admin-portal"}

    def test_get_apps_missing_app_definition(self) -> None:
        """Test handling when app definition is missing."""
        stories = [
            create_story("Upload Document", "User", "defined-app"),
            create_story("Other Task", "User", "undefined-app"),
        ]
        epics: list[Epic] = []
        apps = [
            create_app("defined-app", "Defined App"),
            # undefined-app is not in the list
        ]

        all_personas = derive_personas(stories, epics)
        user = all_personas[0]

        persona_apps = get_apps_for_persona(user, apps)

        # Only the defined app is returned
        assert len(persona_apps) == 1
        assert persona_apps[0].slug == "defined-app"

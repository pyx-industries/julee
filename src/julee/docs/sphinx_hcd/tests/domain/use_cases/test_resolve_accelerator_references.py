"""Tests for resolve_accelerator_references use case."""

import pytest

from julee.docs.sphinx_hcd.domain.models.accelerator import (
    Accelerator,
    IntegrationReference,
)
from julee.docs.sphinx_hcd.domain.models.app import App, AppType
from julee.docs.sphinx_hcd.domain.models.code_info import BoundedContextInfo, ClassInfo
from julee.docs.sphinx_hcd.domain.models.integration import Direction, Integration
from julee.docs.sphinx_hcd.domain.models.journey import Journey, JourneyStep
from julee.docs.sphinx_hcd.domain.models.story import Story
from julee.docs.sphinx_hcd.domain.use_cases.resolve_accelerator_references import (
    get_accelerator_cross_references,
    get_apps_for_accelerator,
    get_code_info_for_accelerator,
    get_dependent_accelerators,
    get_fed_by_accelerators,
    get_journeys_for_accelerator,
    get_publish_integrations,
    get_source_integrations,
    get_stories_for_accelerator,
)


def create_accelerator(
    slug: str,
    sources_from: list[str] | None = None,
    publishes_to: list[str] | None = None,
    depends_on: list[str] | None = None,
    feeds_into: list[str] | None = None,
) -> Accelerator:
    """Helper to create test accelerators."""
    return Accelerator(
        slug=slug,
        status="active",
        sources_from=[IntegrationReference(slug=s) for s in (sources_from or [])],
        publishes_to=[IntegrationReference(slug=p) for p in (publishes_to or [])],
        depends_on=depends_on or [],
        feeds_into=feeds_into or [],
    )


def create_app(slug: str, accelerators: list[str] | None = None) -> App:
    """Helper to create test apps."""
    kwargs: dict = {
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "app_type": AppType.STAFF,
        "manifest_path": f"apps/{slug}/app.yaml",
    }
    if accelerators is not None:
        kwargs["accelerators"] = accelerators
    return App(**kwargs)


def create_story(feature_title: str, app_slug: str) -> Story:
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


def create_journey(slug: str, story_refs: list[str]) -> Journey:
    """Helper to create test journeys."""
    steps = [JourneyStep.story(ref) for ref in story_refs]
    return Journey(slug=slug, persona="User", steps=steps)


def create_integration(slug: str) -> Integration:
    """Helper to create test integrations."""
    return Integration(
        slug=slug,
        module="test",
        name=slug.replace("-", " ").title(),
        description="Test integration",
        direction=Direction.INBOUND,
        manifest_path=f"integrations/{slug}.yaml",
    )


def create_code_info(slug: str, code_dir: str | None = None) -> BoundedContextInfo:
    """Helper to create test code info."""
    return BoundedContextInfo(
        slug=slug,
        code_dir=code_dir or slug,
        entities=[ClassInfo(name="TestEntity", docstring="Test")],
    )


class TestGetAppsForAccelerator:
    """Test get_apps_for_accelerator function."""

    def test_find_apps(self) -> None:
        """Test finding apps that expose an accelerator."""
        accelerator = create_accelerator("vocabulary-builder")
        apps = [
            create_app("vocab-app", accelerators=["vocabulary-builder"]),
            create_app("other-app", accelerators=["other-accel"]),
            create_app("multi-app", accelerators=["vocabulary-builder", "other"]),
        ]

        result = get_apps_for_accelerator(accelerator, apps)

        assert len(result) == 2
        slugs = {a.slug for a in result}
        assert slugs == {"vocab-app", "multi-app"}

    def test_no_apps(self) -> None:
        """Test when no apps expose the accelerator."""
        accelerator = create_accelerator("orphan-accel")
        apps = [create_app("app1", accelerators=["other"])]

        result = get_apps_for_accelerator(accelerator, apps)

        assert result == []

    def test_app_no_accelerators(self) -> None:
        """Test apps without accelerators field."""
        accelerator = create_accelerator("test-accel")
        apps = [create_app("plain-app")]

        result = get_apps_for_accelerator(accelerator, apps)

        assert result == []

    def test_sorted_by_slug(self) -> None:
        """Test results are sorted by slug."""
        accelerator = create_accelerator("shared")
        apps = [
            create_app("zebra-app", accelerators=["shared"]),
            create_app("alpha-app", accelerators=["shared"]),
        ]

        result = get_apps_for_accelerator(accelerator, apps)

        slugs = [a.slug for a in result]
        assert slugs == ["alpha-app", "zebra-app"]


class TestGetStoriesForAccelerator:
    """Test get_stories_for_accelerator function."""

    def test_find_stories(self) -> None:
        """Test finding stories from apps that expose accelerator."""
        accelerator = create_accelerator("vocabulary-builder")
        apps = [
            create_app("vocab-app", accelerators=["vocabulary-builder"]),
            create_app("other-app", accelerators=["other"]),
        ]
        stories = [
            create_story("Upload Document", "vocab-app"),
            create_story("Review Vocab", "vocab-app"),
            create_story("Other Feature", "other-app"),
        ]

        result = get_stories_for_accelerator(accelerator, apps, stories)

        assert len(result) == 2
        titles = {s.feature_title for s in result}
        assert titles == {"Upload Document", "Review Vocab"}

    def test_no_apps_no_stories(self) -> None:
        """Test when no apps expose the accelerator."""
        accelerator = create_accelerator("orphan")
        apps = [create_app("app", accelerators=["other"])]
        stories = [create_story("Feature", "app")]

        result = get_stories_for_accelerator(accelerator, apps, stories)

        assert result == []

    def test_sorted_by_feature_title(self) -> None:
        """Test results are sorted by feature title."""
        accelerator = create_accelerator("test")
        apps = [create_app("app", accelerators=["test"])]
        stories = [
            create_story("Zebra Feature", "app"),
            create_story("Alpha Feature", "app"),
        ]

        result = get_stories_for_accelerator(accelerator, apps, stories)

        titles = [s.feature_title for s in result]
        assert titles == ["Alpha Feature", "Zebra Feature"]


class TestGetJourneysForAccelerator:
    """Test get_journeys_for_accelerator function."""

    def test_find_journeys(self) -> None:
        """Test finding journeys containing accelerator's stories."""
        accelerator = create_accelerator("vocab-builder")
        apps = [create_app("vocab-app", accelerators=["vocab-builder"])]
        stories = [create_story("Upload Document", "vocab-app")]
        journeys = [
            create_journey("build-vocab", ["Upload Document"]),
            create_journey("other-journey", ["Other Feature"]),
        ]

        result = get_journeys_for_accelerator(accelerator, apps, stories, journeys)

        assert len(result) == 1
        assert result[0].slug == "build-vocab"

    def test_no_journeys(self) -> None:
        """Test when accelerator's stories are not in any journey."""
        accelerator = create_accelerator("test")
        apps = [create_app("app", accelerators=["test"])]
        stories = [create_story("Lonely Feature", "app")]
        journeys = [create_journey("journey", ["Other Story"])]

        result = get_journeys_for_accelerator(accelerator, apps, stories, journeys)

        assert result == []

    def test_sorted_by_slug(self) -> None:
        """Test results are sorted by slug."""
        accelerator = create_accelerator("test")
        apps = [create_app("app", accelerators=["test"])]
        stories = [create_story("Shared Story", "app")]
        journeys = [
            create_journey("zebra-journey", ["Shared Story"]),
            create_journey("alpha-journey", ["Shared Story"]),
        ]

        result = get_journeys_for_accelerator(accelerator, apps, stories, journeys)

        slugs = [j.slug for j in result]
        assert slugs == ["alpha-journey", "zebra-journey"]


class TestGetSourceIntegrations:
    """Test get_source_integrations function."""

    def test_find_sources(self) -> None:
        """Test finding source integrations."""
        accelerator = create_accelerator(
            "vocab-builder",
            sources_from=["kafka", "postgres"],
        )
        integrations = [
            create_integration("kafka"),
            create_integration("postgres"),
            create_integration("redis"),
        ]

        result = get_source_integrations(accelerator, integrations)

        assert len(result) == 2
        slugs = {i.slug for i in result}
        assert slugs == {"kafka", "postgres"}

    def test_no_sources(self) -> None:
        """Test accelerator with no sources."""
        accelerator = create_accelerator("no-sources")
        integrations = [create_integration("kafka")]

        result = get_source_integrations(accelerator, integrations)

        assert result == []

    def test_missing_integration(self) -> None:
        """Test when referenced integration doesn't exist."""
        accelerator = create_accelerator("test", sources_from=["missing"])
        integrations = [create_integration("other")]

        result = get_source_integrations(accelerator, integrations)

        assert result == []


class TestGetPublishIntegrations:
    """Test get_publish_integrations function."""

    def test_find_publish_targets(self) -> None:
        """Test finding publish target integrations."""
        accelerator = create_accelerator(
            "vocab-builder",
            publishes_to=["elasticsearch", "api"],
        )
        integrations = [
            create_integration("elasticsearch"),
            create_integration("api"),
            create_integration("unused"),
        ]

        result = get_publish_integrations(accelerator, integrations)

        assert len(result) == 2
        slugs = {i.slug for i in result}
        assert slugs == {"elasticsearch", "api"}

    def test_no_publish_targets(self) -> None:
        """Test accelerator with no publish targets."""
        accelerator = create_accelerator("no-publish")
        integrations = [create_integration("kafka")]

        result = get_publish_integrations(accelerator, integrations)

        assert result == []


class TestGetDependentAccelerators:
    """Test get_dependent_accelerators function."""

    def test_find_dependents(self) -> None:
        """Test finding accelerators that depend on this one."""
        accelerator = create_accelerator("core-accel")
        accelerators = [
            create_accelerator("dependent-1", depends_on=["core-accel"]),
            create_accelerator("dependent-2", depends_on=["core-accel", "other"]),
            create_accelerator("independent", depends_on=["other"]),
        ]

        result = get_dependent_accelerators(accelerator, accelerators)

        assert len(result) == 2
        slugs = {a.slug for a in result}
        assert slugs == {"dependent-1", "dependent-2"}

    def test_no_dependents(self) -> None:
        """Test when no accelerators depend on this one."""
        accelerator = create_accelerator("leaf-accel")
        accelerators = [create_accelerator("other", depends_on=["different"])]

        result = get_dependent_accelerators(accelerator, accelerators)

        assert result == []

    def test_sorted_by_slug(self) -> None:
        """Test results are sorted by slug."""
        accelerator = create_accelerator("core")
        accelerators = [
            create_accelerator("zebra", depends_on=["core"]),
            create_accelerator("alpha", depends_on=["core"]),
        ]

        result = get_dependent_accelerators(accelerator, accelerators)

        slugs = [a.slug for a in result]
        assert slugs == ["alpha", "zebra"]


class TestGetFedByAccelerators:
    """Test get_fed_by_accelerators function."""

    def test_find_feeders(self) -> None:
        """Test finding accelerators that feed into this one."""
        accelerator = create_accelerator("downstream")
        accelerators = [
            create_accelerator("feeder-1", feeds_into=["downstream"]),
            create_accelerator("feeder-2", feeds_into=["downstream", "other"]),
            create_accelerator("non-feeder", feeds_into=["other"]),
        ]

        result = get_fed_by_accelerators(accelerator, accelerators)

        assert len(result) == 2
        slugs = {a.slug for a in result}
        assert slugs == {"feeder-1", "feeder-2"}

    def test_no_feeders(self) -> None:
        """Test when no accelerators feed into this one."""
        accelerator = create_accelerator("source-accel")
        accelerators = [create_accelerator("other", feeds_into=["different"])]

        result = get_fed_by_accelerators(accelerator, accelerators)

        assert result == []


class TestGetCodeInfoForAccelerator:
    """Test get_code_info_for_accelerator function."""

    def test_exact_match(self) -> None:
        """Test finding code info by exact slug match."""
        accelerator = create_accelerator("vocab-builder")
        code_infos = [
            create_code_info("vocab-builder"),
            create_code_info("other"),
        ]

        result = get_code_info_for_accelerator(accelerator, code_infos)

        assert result is not None
        assert result.slug == "vocab-builder"

    def test_snake_case_match(self) -> None:
        """Test finding code info by snake_case slug match."""
        accelerator = create_accelerator("vocab-builder")
        code_infos = [create_code_info("vocab_builder")]

        result = get_code_info_for_accelerator(accelerator, code_infos)

        assert result is not None
        assert result.slug == "vocab_builder"

    def test_code_dir_match(self) -> None:
        """Test finding code info by code_dir match."""
        accelerator = create_accelerator("vocab-builder")
        code_infos = [create_code_info("different-slug", code_dir="vocab_builder")]

        result = get_code_info_for_accelerator(accelerator, code_infos)

        assert result is not None
        assert result.code_dir == "vocab_builder"

    def test_no_match(self) -> None:
        """Test when no code info matches."""
        accelerator = create_accelerator("unknown")
        code_infos = [create_code_info("other")]

        result = get_code_info_for_accelerator(accelerator, code_infos)

        assert result is None


class TestGetAcceleratorCrossReferences:
    """Test get_accelerator_cross_references function."""

    def test_cross_references(self) -> None:
        """Test getting all cross-references for an accelerator."""
        accelerator = create_accelerator(
            "vocab-builder",
            sources_from=["kafka"],
            publishes_to=["elasticsearch"],
        )
        accelerators = [
            accelerator,
            create_accelerator("dependent", depends_on=["vocab-builder"]),
            create_accelerator("feeder", feeds_into=["vocab-builder"]),
        ]
        apps = [create_app("vocab-app", accelerators=["vocab-builder"])]
        stories = [create_story("Upload Document", "vocab-app")]
        journeys = [create_journey("build-vocab", ["Upload Document"])]
        integrations = [
            create_integration("kafka"),
            create_integration("elasticsearch"),
        ]
        code_infos = [create_code_info("vocab-builder")]

        result = get_accelerator_cross_references(
            accelerator,
            accelerators,
            apps,
            stories,
            journeys,
            integrations,
            code_infos,
        )

        assert len(result["apps"]) == 1
        assert len(result["stories"]) == 1
        assert len(result["journeys"]) == 1
        assert len(result["source_integrations"]) == 1
        assert len(result["publish_integrations"]) == 1
        assert len(result["dependents"]) == 1
        assert len(result["fed_by"]) == 1
        assert result["code_info"] is not None

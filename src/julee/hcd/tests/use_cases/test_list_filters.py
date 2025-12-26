"""Tests for list use case filter functionality."""

import pytest

from julee.hcd.entities.accelerator import Accelerator, IntegrationReference
from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey, JourneyStep
from julee.hcd.entities.story import Story
from julee.hcd.infrastructure.repositories.memory.accelerator import (
    MemoryAcceleratorRepository,
)
from julee.hcd.infrastructure.repositories.memory.app import MemoryAppRepository
from julee.hcd.infrastructure.repositories.memory.epic import MemoryEpicRepository
from julee.hcd.infrastructure.repositories.memory.journey import MemoryJourneyRepository
from julee.hcd.infrastructure.repositories.memory.story import MemoryStoryRepository
from julee.hcd.use_cases.crud import (
    ListAcceleratorsRequest,
    ListAcceleratorsUseCase,
    ListAppsRequest,
    ListAppsUseCase,
    ListEpicsRequest,
    ListEpicsUseCase,
    ListJourneysRequest,
    ListJourneysUseCase,
    ListStoriesRequest,
    ListStoriesUseCase,
)


class TestListStoriesFilters:
    """Tests for ListStoriesUseCase filtering."""

    @pytest.fixture
    def stories(self) -> list[Story]:
        return [
            Story(
                slug="portal--upload-doc",
                feature_title="Upload Document",
                persona="Manager",
                app_slug="staff-portal",
                file_path="features/portal/upload.feature",
            ),
            Story(
                slug="portal--view-doc",
                feature_title="View Document",
                persona="Manager",
                app_slug="staff-portal",
                file_path="features/portal/view.feature",
            ),
            Story(
                slug="mobile--scan-doc",
                feature_title="Scan Document",
                persona="Field Worker",
                app_slug="mobile-app",
                file_path="features/mobile/scan.feature",
            ),
        ]

    @pytest.fixture
    def repo(self, stories) -> MemoryStoryRepository:
        """Create repository pre-populated with stories."""
        repo = MemoryStoryRepository()
        for story in stories:
            repo._save_entity(story)
        return repo

    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self, repo):
        """Should return all stories when no filter is specified."""
        use_case = ListStoriesUseCase(repo)

        response = await use_case.execute(ListStoriesRequest())

        assert response.count == 3

    @pytest.mark.asyncio
    async def test_filter_by_app_slug(self, repo):
        """Should filter stories by app slug."""
        use_case = ListStoriesUseCase(repo)

        response = await use_case.execute(ListStoriesRequest(app_slug="staff-portal"))

        assert response.count == 2
        assert all(s.app_slug == "staff-portal" for s in response.stories)

    @pytest.mark.asyncio
    async def test_filter_by_persona(self, repo):
        """Should filter stories by persona."""
        use_case = ListStoriesUseCase(repo)

        response = await use_case.execute(ListStoriesRequest(persona="Field Worker"))

        assert response.count == 1
        assert response.stories[0].persona == "Field Worker"

    @pytest.mark.asyncio
    async def test_filter_by_app_and_persona(self, repo):
        """Should combine filters with AND logic."""
        use_case = ListStoriesUseCase(repo)

        response = await use_case.execute(
            ListStoriesRequest(app_slug="staff-portal", persona="Manager")
        )

        assert response.count == 2

    @pytest.mark.asyncio
    async def test_grouped_by_persona(self, repo):
        """Should group stories by persona."""
        use_case = ListStoriesUseCase(repo)

        response = await use_case.execute(ListStoriesRequest())
        grouped = response.grouped_by_persona()

        assert "Manager" in grouped
        assert len(grouped["Manager"]) == 2
        assert "Field Worker" in grouped
        assert len(grouped["Field Worker"]) == 1

    @pytest.mark.asyncio
    async def test_grouped_by_app(self, repo):
        """Should group stories by app."""
        use_case = ListStoriesUseCase(repo)

        response = await use_case.execute(ListStoriesRequest())
        grouped = response.grouped_by_app()

        assert "staff-portal" in grouped
        assert len(grouped["staff-portal"]) == 2


class TestListAcceleratorsFilters:
    """Tests for ListAcceleratorsUseCase filtering."""

    @pytest.fixture
    def accelerators(self) -> list[Accelerator]:
        return [
            Accelerator(
                slug="ceap",
                status="active",
                sources_from=[IntegrationReference(slug="kafka")],
            ),
            Accelerator(
                slug="vocab",
                status="active",
                publishes_to=[IntegrationReference(slug="elasticsearch")],
            ),
            Accelerator(
                slug="legacy",
                status="deprecated",
                sources_from=[IntegrationReference(slug="kafka")],
            ),
        ]

    @pytest.fixture
    def repo(self, accelerators) -> MemoryAcceleratorRepository:
        """Create repository pre-populated with accelerators."""
        repo = MemoryAcceleratorRepository()
        for accel in accelerators:
            repo._save_entity(accel)
        return repo

    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self, repo):
        """Should return all accelerators when no filter is specified."""
        use_case = ListAcceleratorsUseCase(repo)

        response = await use_case.execute(ListAcceleratorsRequest())

        assert response.count == 3

    @pytest.mark.asyncio
    async def test_filter_by_status(self, repo):
        """Should filter accelerators by status."""
        use_case = ListAcceleratorsUseCase(repo)

        response = await use_case.execute(ListAcceleratorsRequest(status="active"))

        assert response.count == 2
        assert all(a.status == "active" for a in response.accelerators)

    @pytest.mark.asyncio
    async def test_filter_by_deprecated_status(self, repo):
        """Should filter accelerators by deprecated status."""
        use_case = ListAcceleratorsUseCase(repo)

        response = await use_case.execute(ListAcceleratorsRequest(status="deprecated"))

        assert response.count == 1
        assert response.accelerators[0].slug == "legacy"


class TestListEpicsFilters:
    """Tests for ListEpicsUseCase filtering."""

    @pytest.fixture
    def epics(self) -> list[Epic]:
        return [
            Epic(slug="onboarding", story_refs=["Upload Doc", "View Doc"]),
            Epic(slug="compliance", story_refs=["Audit Log"]),
            Epic(slug="future", story_refs=[]),
        ]

    @pytest.fixture
    def repo(self, epics) -> MemoryEpicRepository:
        """Create repository pre-populated with epics."""
        repo = MemoryEpicRepository()
        for epic in epics:
            repo._save_entity(epic)
        return repo

    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self, repo):
        """Should return all epics when no filter is specified."""
        use_case = ListEpicsUseCase(repo)

        response = await use_case.execute(ListEpicsRequest())

        assert response.count == 3

    @pytest.mark.asyncio
    async def test_filter_has_stories_true(self, repo):
        """Should filter to epics with stories."""
        use_case = ListEpicsUseCase(repo)

        response = await use_case.execute(ListEpicsRequest(has_stories=True))

        assert response.count == 2
        assert all(e.story_refs for e in response.epics)

    @pytest.mark.asyncio
    async def test_filter_has_stories_false(self, repo):
        """Should filter to epics without stories."""
        use_case = ListEpicsUseCase(repo)

        response = await use_case.execute(ListEpicsRequest(has_stories=False))

        assert response.count == 1
        assert response.epics[0].slug == "future"

    @pytest.mark.asyncio
    async def test_filter_contains_story(self, repo):
        """Should filter to epics containing a specific story."""
        use_case = ListEpicsUseCase(repo)

        response = await use_case.execute(ListEpicsRequest(contains_story="Upload Doc"))

        assert response.count == 1
        assert response.epics[0].slug == "onboarding"

    @pytest.mark.asyncio
    async def test_total_stories_property(self, repo):
        """Should compute total stories across all epics."""
        use_case = ListEpicsUseCase(repo)

        response = await use_case.execute(ListEpicsRequest())

        assert response.total_stories == 3


class TestListAppsFilters:
    """Tests for ListAppsUseCase filtering."""

    @pytest.fixture
    def apps(self) -> list[App]:
        from julee.hcd.entities.app import AppType

        return [
            App(
                slug="portal",
                name="Staff Portal",
                app_type=AppType.STAFF,
                accelerators=["ceap"],
            ),
            App(
                slug="mobile",
                name="Mobile App",
                app_type=AppType.EXTERNAL,
                accelerators=["vocab"],
            ),
            App(
                slug="admin",
                name="Admin Panel",
                app_type=AppType.STAFF,
                accelerators=["ceap", "vocab"],
            ),
        ]

    @pytest.fixture
    def repo(self, apps) -> MemoryAppRepository:
        """Create repository pre-populated with apps."""
        repo = MemoryAppRepository()
        for app in apps:
            repo._save_entity(app)
        return repo

    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self, repo):
        """Should return all apps when no filter is specified."""
        use_case = ListAppsUseCase(repo)

        response = await use_case.execute(ListAppsRequest())

        assert response.count == 3

    @pytest.mark.asyncio
    async def test_filter_by_type(self, repo):
        """Should filter apps by type."""
        from julee.hcd.entities.app import AppType

        use_case = ListAppsUseCase(repo)

        response = await use_case.execute(ListAppsRequest(app_type="staff"))

        assert response.count == 2
        assert all(a.app_type == AppType.STAFF for a in response.apps)

    @pytest.mark.asyncio
    async def test_filter_by_accelerator(self, repo):
        """Should filter apps by accelerator."""
        use_case = ListAppsUseCase(repo)

        response = await use_case.execute(ListAppsRequest(has_accelerator="ceap"))

        assert response.count == 2
        slugs = {a.slug for a in response.apps}
        assert slugs == {"portal", "admin"}

    @pytest.mark.asyncio
    async def test_grouped_by_type(self, repo):
        """Should group apps by type."""
        use_case = ListAppsUseCase(repo)

        response = await use_case.execute(ListAppsRequest())
        grouped = response.grouped_by_type()

        assert "staff" in grouped
        assert len(grouped["staff"]) == 2
        assert "external" in grouped
        assert len(grouped["external"]) == 1


class TestListJourneysFilters:
    """Tests for ListJourneysUseCase filtering."""

    @pytest.fixture
    def journeys(self) -> list[Journey]:
        return [
            Journey(
                slug="onboard",
                steps=[
                    JourneyStep.story("Upload Doc"),
                    JourneyStep.story("Review Doc"),
                ],
            ),
            Journey(
                slug="audit",
                steps=[
                    JourneyStep.story("View Audit Log"),
                ],
            ),
        ]

    @pytest.fixture
    def repo(self, journeys) -> MemoryJourneyRepository:
        """Create repository pre-populated with journeys."""
        repo = MemoryJourneyRepository()
        for journey in journeys:
            repo._save_entity(journey)
        return repo

    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self, repo):
        """Should return all journeys when no filter is specified."""
        use_case = ListJourneysUseCase(repo)

        response = await use_case.execute(ListJourneysRequest())

        assert response.count == 2

    @pytest.mark.asyncio
    async def test_filter_contains_story(self, repo):
        """Should filter to journeys containing a specific story."""
        use_case = ListJourneysUseCase(repo)

        response = await use_case.execute(
            ListJourneysRequest(contains_story="Upload Doc")
        )

        assert response.count == 1
        assert response.journeys[0].slug == "onboard"

"""Dependency injection for HCD REST API.

Provides repository instances and use-case factories for FastAPI dependency injection.
Repositories are configured from environment variables.
"""

import os
from functools import lru_cache
from pathlib import Path

from julee.hcd.infrastructure.repositories.file.accelerator import (
    FileAcceleratorRepository,
)
from julee.hcd.infrastructure.repositories.file.app import FileAppRepository
from julee.hcd.infrastructure.repositories.file.epic import FileEpicRepository
from julee.hcd.infrastructure.repositories.file.integration import (
    FileIntegrationRepository,
)
from julee.hcd.infrastructure.repositories.file.journey import FileJourneyRepository
from julee.hcd.infrastructure.repositories.file.story import FileStoryRepository
from julee.hcd.use_cases.accelerator.create import CreateAcceleratorUseCase
from julee.hcd.use_cases.accelerator.delete import DeleteAcceleratorUseCase
from julee.hcd.use_cases.accelerator.get import GetAcceleratorUseCase
from julee.hcd.use_cases.accelerator.list import ListAcceleratorsUseCase
from julee.hcd.use_cases.accelerator.update import UpdateAcceleratorUseCase
from julee.hcd.use_cases.app.create import CreateAppUseCase
from julee.hcd.use_cases.app.delete import DeleteAppUseCase
from julee.hcd.use_cases.app.get import GetAppUseCase
from julee.hcd.use_cases.app.list import ListAppsUseCase
from julee.hcd.use_cases.app.update import UpdateAppUseCase
from julee.hcd.use_cases.epic.create import CreateEpicUseCase
from julee.hcd.use_cases.epic.delete import DeleteEpicUseCase
from julee.hcd.use_cases.epic.get import GetEpicUseCase
from julee.hcd.use_cases.epic.list import ListEpicsUseCase
from julee.hcd.use_cases.epic.update import UpdateEpicUseCase
from julee.hcd.use_cases.integration.create import CreateIntegrationUseCase
from julee.hcd.use_cases.integration.delete import DeleteIntegrationUseCase
from julee.hcd.use_cases.integration.get import GetIntegrationUseCase
from julee.hcd.use_cases.integration.list import ListIntegrationsUseCase
from julee.hcd.use_cases.integration.update import UpdateIntegrationUseCase
from julee.hcd.use_cases.journey.create import CreateJourneyUseCase
from julee.hcd.use_cases.journey.delete import DeleteJourneyUseCase
from julee.hcd.use_cases.journey.get import GetJourneyUseCase
from julee.hcd.use_cases.journey.list import ListJourneysUseCase
from julee.hcd.use_cases.journey.update import UpdateJourneyUseCase
from julee.hcd.use_cases.queries.derive_personas import DerivePersonasUseCase
from julee.hcd.use_cases.queries.get_persona import GetPersonaUseCase
from julee.hcd.use_cases.story.create import CreateStoryUseCase
from julee.hcd.use_cases.story.delete import DeleteStoryUseCase
from julee.hcd.use_cases.story.get import GetStoryUseCase
from julee.hcd.use_cases.story.list import ListStoriesUseCase
from julee.hcd.use_cases.story.update import UpdateStoryUseCase


def get_docs_root() -> Path:
    """Get the documentation root directory from environment.

    Returns:
        Path to the docs root directory
    """
    return Path(os.getenv("HCD_DOCS_ROOT", "docs"))


# =============================================================================
# Repository Factories
# =============================================================================


@lru_cache
def get_story_repository() -> FileStoryRepository:
    """Get the story repository singleton."""
    docs_root = get_docs_root()
    return FileStoryRepository(docs_root / "features")


@lru_cache
def get_epic_repository() -> FileEpicRepository:
    """Get the epic repository singleton."""
    docs_root = get_docs_root()
    return FileEpicRepository(docs_root / "epics")


@lru_cache
def get_journey_repository() -> FileJourneyRepository:
    """Get the journey repository singleton."""
    docs_root = get_docs_root()
    return FileJourneyRepository(docs_root / "journeys")


@lru_cache
def get_app_repository() -> FileAppRepository:
    """Get the app repository singleton."""
    docs_root = get_docs_root()
    return FileAppRepository(docs_root / "apps")


@lru_cache
def get_integration_repository() -> FileIntegrationRepository:
    """Get the integration repository singleton."""
    docs_root = get_docs_root()
    return FileIntegrationRepository(docs_root / "integrations")


@lru_cache
def get_accelerator_repository() -> FileAcceleratorRepository:
    """Get the accelerator repository singleton."""
    docs_root = get_docs_root()
    return FileAcceleratorRepository(docs_root / "accelerators")


# =============================================================================
# Story Use-Case Factories
# =============================================================================


def get_create_story_use_case() -> CreateStoryUseCase:
    """Get CreateStoryUseCase with repository dependency."""
    return CreateStoryUseCase(get_story_repository())


def get_get_story_use_case() -> GetStoryUseCase:
    """Get GetStoryUseCase with repository dependency."""
    return GetStoryUseCase(get_story_repository())


def get_list_stories_use_case() -> ListStoriesUseCase:
    """Get ListStoriesUseCase with repository dependency."""
    return ListStoriesUseCase(get_story_repository())


def get_update_story_use_case() -> UpdateStoryUseCase:
    """Get UpdateStoryUseCase with repository dependency."""
    return UpdateStoryUseCase(get_story_repository())


def get_delete_story_use_case() -> DeleteStoryUseCase:
    """Get DeleteStoryUseCase with repository dependency."""
    return DeleteStoryUseCase(get_story_repository())


# =============================================================================
# Epic Use-Case Factories
# =============================================================================


def get_create_epic_use_case() -> CreateEpicUseCase:
    """Get CreateEpicUseCase with repository dependency."""
    return CreateEpicUseCase(get_epic_repository())


def get_get_epic_use_case() -> GetEpicUseCase:
    """Get GetEpicUseCase with repository dependency."""
    return GetEpicUseCase(get_epic_repository())


def get_list_epics_use_case() -> ListEpicsUseCase:
    """Get ListEpicsUseCase with repository dependency."""
    return ListEpicsUseCase(get_epic_repository())


def get_update_epic_use_case() -> UpdateEpicUseCase:
    """Get UpdateEpicUseCase with repository dependency."""
    return UpdateEpicUseCase(get_epic_repository())


def get_delete_epic_use_case() -> DeleteEpicUseCase:
    """Get DeleteEpicUseCase with repository dependency."""
    return DeleteEpicUseCase(get_epic_repository())


# =============================================================================
# Journey Use-Case Factories
# =============================================================================


def get_create_journey_use_case() -> CreateJourneyUseCase:
    """Get CreateJourneyUseCase with repository dependency."""
    return CreateJourneyUseCase(get_journey_repository())


def get_get_journey_use_case() -> GetJourneyUseCase:
    """Get GetJourneyUseCase with repository dependency."""
    return GetJourneyUseCase(get_journey_repository())


def get_list_journeys_use_case() -> ListJourneysUseCase:
    """Get ListJourneysUseCase with repository dependency."""
    return ListJourneysUseCase(get_journey_repository())


def get_update_journey_use_case() -> UpdateJourneyUseCase:
    """Get UpdateJourneyUseCase with repository dependency."""
    return UpdateJourneyUseCase(get_journey_repository())


def get_delete_journey_use_case() -> DeleteJourneyUseCase:
    """Get DeleteJourneyUseCase with repository dependency."""
    return DeleteJourneyUseCase(get_journey_repository())


# =============================================================================
# Accelerator Use-Case Factories
# =============================================================================


def get_create_accelerator_use_case() -> CreateAcceleratorUseCase:
    """Get CreateAcceleratorUseCase with repository dependency."""
    return CreateAcceleratorUseCase(get_accelerator_repository())


def get_get_accelerator_use_case() -> GetAcceleratorUseCase:
    """Get GetAcceleratorUseCase with repository dependency."""
    return GetAcceleratorUseCase(get_accelerator_repository())


def get_list_accelerators_use_case() -> ListAcceleratorsUseCase:
    """Get ListAcceleratorsUseCase with repository dependency."""
    return ListAcceleratorsUseCase(get_accelerator_repository())


def get_update_accelerator_use_case() -> UpdateAcceleratorUseCase:
    """Get UpdateAcceleratorUseCase with repository dependency."""
    return UpdateAcceleratorUseCase(get_accelerator_repository())


def get_delete_accelerator_use_case() -> DeleteAcceleratorUseCase:
    """Get DeleteAcceleratorUseCase with repository dependency."""
    return DeleteAcceleratorUseCase(get_accelerator_repository())


# =============================================================================
# Integration Use-Case Factories
# =============================================================================


def get_create_integration_use_case() -> CreateIntegrationUseCase:
    """Get CreateIntegrationUseCase with repository dependency."""
    return CreateIntegrationUseCase(get_integration_repository())


def get_get_integration_use_case() -> GetIntegrationUseCase:
    """Get GetIntegrationUseCase with repository dependency."""
    return GetIntegrationUseCase(get_integration_repository())


def get_list_integrations_use_case() -> ListIntegrationsUseCase:
    """Get ListIntegrationsUseCase with repository dependency."""
    return ListIntegrationsUseCase(get_integration_repository())


def get_update_integration_use_case() -> UpdateIntegrationUseCase:
    """Get UpdateIntegrationUseCase with repository dependency."""
    return UpdateIntegrationUseCase(get_integration_repository())


def get_delete_integration_use_case() -> DeleteIntegrationUseCase:
    """Get DeleteIntegrationUseCase with repository dependency."""
    return DeleteIntegrationUseCase(get_integration_repository())


# =============================================================================
# App Use-Case Factories
# =============================================================================


def get_create_app_use_case() -> CreateAppUseCase:
    """Get CreateAppUseCase with repository dependency."""
    return CreateAppUseCase(get_app_repository())


def get_get_app_use_case() -> GetAppUseCase:
    """Get GetAppUseCase with repository dependency."""
    return GetAppUseCase(get_app_repository())


def get_list_apps_use_case() -> ListAppsUseCase:
    """Get ListAppsUseCase with repository dependency."""
    return ListAppsUseCase(get_app_repository())


def get_update_app_use_case() -> UpdateAppUseCase:
    """Get UpdateAppUseCase with repository dependency."""
    return UpdateAppUseCase(get_app_repository())


def get_delete_app_use_case() -> DeleteAppUseCase:
    """Get DeleteAppUseCase with repository dependency."""
    return DeleteAppUseCase(get_app_repository())


# =============================================================================
# Query Use-Case Factories
# =============================================================================


def get_derive_personas_use_case() -> DerivePersonasUseCase:
    """Get DerivePersonasUseCase with repository dependencies."""
    return DerivePersonasUseCase(
        story_repo=get_story_repository(),
        epic_repo=get_epic_repository(),
    )


def get_get_persona_use_case() -> GetPersonaUseCase:
    """Get GetPersonaUseCase with repository dependencies."""
    return GetPersonaUseCase(
        story_repo=get_story_repository(),
        epic_repo=get_epic_repository(),
    )

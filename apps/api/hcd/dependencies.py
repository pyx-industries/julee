"""Dependency injection for HCD REST API.

Provides repository instances, handler factories, and use-case factories for
FastAPI dependency injection. Repositories are configured from environment variables.

Handler architecture (see ADR 003):
- Fine-grained handlers: No internal use case, interact directly with technology
- Coarse-grained handlers: Wrap ONE internal use case, delegate to fine-grained handlers
"""

import os
from functools import lru_cache
from pathlib import Path

from julee.hcd.infrastructure.handlers.null_handlers import (
    LoggingOrphanStoryHandler,
    LoggingUnknownPersonaHandler,
    NullStoryCreatedHandler,
)
from julee.hcd.infrastructure.handlers.story_orchestration import (
    StoryOrchestrationHandler,
)
from julee.hcd.infrastructure.repositories.memory.persona import (
    MemoryPersonaRepository,
)
from julee.hcd.services.story_handlers import StoryCreatedHandler
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
from julee.hcd.use_cases.crud import (
    # Accelerator
    CreateAcceleratorUseCase,
    DeleteAcceleratorUseCase,
    GetAcceleratorUseCase,
    ListAcceleratorsUseCase,
    UpdateAcceleratorUseCase,
    # App
    CreateAppUseCase,
    DeleteAppUseCase,
    GetAppUseCase,
    ListAppsUseCase,
    UpdateAppUseCase,
    # Epic
    CreateEpicUseCase,
    DeleteEpicUseCase,
    GetEpicUseCase,
    ListEpicsUseCase,
    UpdateEpicUseCase,
    # Integration
    CreateIntegrationUseCase,
    DeleteIntegrationUseCase,
    GetIntegrationUseCase,
    ListIntegrationsUseCase,
    UpdateIntegrationUseCase,
    # Journey
    CreateJourneyUseCase,
    DeleteJourneyUseCase,
    GetJourneyUseCase,
    ListJourneysUseCase,
    UpdateJourneyUseCase,
    # Story
    CreateStoryUseCase,
    DeleteStoryUseCase,
    GetStoryUseCase,
    ListStoriesUseCase,
    UpdateStoryUseCase,
)
from julee.hcd.use_cases.queries.derive_personas import DerivePersonasUseCase
from julee.hcd.use_cases.queries.get_persona import GetPersonaUseCase
from julee.hcd.use_cases.story_orchestration import StoryOrchestrationUseCase


def get_docs_root() -> Path:
    """Get the documentation root directory from environment.

    Returns:
        Path to the docs root directory
    """
    return Path(os.getenv("HCD_DOCS_ROOT", "docs"))


# =============================================================================
# Persona Repository Factory
# =============================================================================


@lru_cache
def get_persona_repository() -> MemoryPersonaRepository:
    """Get the persona repository singleton.

    Uses in-memory repository since personas are derived from stories/epics.
    """
    return MemoryPersonaRepository()


# =============================================================================
# Handler Factories
# =============================================================================


@lru_cache
def get_orphan_story_handler() -> LoggingOrphanStoryHandler:
    """Get fine-grained handler for orphan story conditions.

    Logs warning when a story is not referenced in any epic.
    """
    return LoggingOrphanStoryHandler()


@lru_cache
def get_unknown_persona_handler() -> LoggingUnknownPersonaHandler:
    """Get fine-grained handler for unknown persona conditions.

    Logs warning when a story references an unknown persona.
    """
    return LoggingUnknownPersonaHandler()


def get_story_orchestration_handler() -> StoryOrchestrationHandler:
    """Get coarse-grained handler for story orchestration.

    Creates the full handler chain:
    - StoryOrchestrationUseCase (detects conditions)
    - Fine-grained handlers (process each condition)
    """
    from julee.hcd.use_cases.story_orchestration import StoryOrchestrationUseCase

    orchestration_use_case = StoryOrchestrationUseCase(
        persona_repo=get_persona_repository(),
        epic_repo=get_epic_repository(),
    )
    return StoryOrchestrationHandler(
        orchestration_use_case=orchestration_use_case,
        orphan_handler=get_orphan_story_handler(),
        unknown_persona_handler=get_unknown_persona_handler(),
    )


def get_story_created_handler() -> StoryCreatedHandler:
    """Get handler for post-story-creation orchestration.

    Returns the full StoryOrchestrationHandler chain by default.
    Override in solution-specific dependencies for custom behavior.
    """
    return get_story_orchestration_handler()


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
    """Get CreateStoryUseCase with repository and handler dependencies."""
    return CreateStoryUseCase(
        get_story_repository(),
        post_create_handler=get_story_created_handler(),
    )


def get_get_story_use_case() -> GetStoryUseCase:
    """Get GetStoryUseCase with repository dependency."""
    return GetStoryUseCase(get_story_repository())


def get_list_stories_use_case() -> ListStoriesUseCase:
    """Get ListStoriesUseCase with repository dependency."""
    return ListStoriesUseCase(get_story_repository())


def get_update_story_use_case() -> UpdateStoryUseCase:
    """Get UpdateStoryUseCase with repository and handler dependencies."""
    return UpdateStoryUseCase(
        get_story_repository(),
        post_update_handler=get_story_created_handler(),
    )


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

"""Use cases for sphinx_hcd.

Business logic for cross-referencing and deriving entities.
"""

# CRUD use-case classes (following clean architecture pattern)
from .accelerator import (
    CreateAcceleratorUseCase,
    DeleteAcceleratorUseCase,
    GetAcceleratorUseCase,
    ListAcceleratorsUseCase,
    UpdateAcceleratorUseCase,
)
from .app import (
    CreateAppUseCase,
    DeleteAppUseCase,
    GetAppUseCase,
    ListAppsUseCase,
    UpdateAppUseCase,
)

# Legacy function-based use cases (for backwards compatibility)
from .derive_personas import (
    derive_personas,
    derive_personas_by_app_type,
    get_apps_for_persona,
    get_epics_for_persona,
)
from .epic import (
    CreateEpicUseCase,
    DeleteEpicUseCase,
    GetEpicUseCase,
    ListEpicsUseCase,
    UpdateEpicUseCase,
)
from .integration import (
    CreateIntegrationUseCase,
    DeleteIntegrationUseCase,
    GetIntegrationUseCase,
    ListIntegrationsUseCase,
    UpdateIntegrationUseCase,
)
from .journey import (
    CreateJourneyUseCase,
    DeleteJourneyUseCase,
    GetJourneyUseCase,
    ListJourneysUseCase,
    UpdateJourneyUseCase,
)
from .persona import (
    CreatePersonaUseCase,
    DeletePersonaUseCase,
    GetPersonaBySlugRequest,
    GetPersonaBySlugUseCase,
    ListPersonasUseCase,
    UpdatePersonaUseCase,
)
from .queries import DerivePersonasUseCase, GetPersonaUseCase
from .resolve_accelerator_references import (
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
from .resolve_app_references import (
    get_app_cross_references,
    get_epics_for_app,
    get_journeys_for_app,
    get_personas_for_app,
    get_stories_for_app,
)
from .resolve_story_references import (
    get_epics_for_story,
    get_journeys_for_story,
    get_related_stories,
    get_story_cross_references,
)
from .story import (
    CreateStoryUseCase,
    DeleteStoryUseCase,
    GetStoryUseCase,
    ListStoriesUseCase,
    UpdateStoryUseCase,
)

__all__ = [
    # Story use-case classes
    "CreateStoryUseCase",
    "GetStoryUseCase",
    "ListStoriesUseCase",
    "UpdateStoryUseCase",
    "DeleteStoryUseCase",
    # Epic use-case classes
    "CreateEpicUseCase",
    "GetEpicUseCase",
    "ListEpicsUseCase",
    "UpdateEpicUseCase",
    "DeleteEpicUseCase",
    # Journey use-case classes
    "CreateJourneyUseCase",
    "GetJourneyUseCase",
    "ListJourneysUseCase",
    "UpdateJourneyUseCase",
    "DeleteJourneyUseCase",
    # Accelerator use-case classes
    "CreateAcceleratorUseCase",
    "GetAcceleratorUseCase",
    "ListAcceleratorsUseCase",
    "UpdateAcceleratorUseCase",
    "DeleteAcceleratorUseCase",
    # Integration use-case classes
    "CreateIntegrationUseCase",
    "GetIntegrationUseCase",
    "ListIntegrationsUseCase",
    "UpdateIntegrationUseCase",
    "DeleteIntegrationUseCase",
    # App use-case classes
    "CreateAppUseCase",
    "GetAppUseCase",
    "ListAppsUseCase",
    "UpdateAppUseCase",
    "DeleteAppUseCase",
    # Persona use-case classes (CRUD for defined personas)
    "CreatePersonaUseCase",
    "GetPersonaBySlugUseCase",
    "GetPersonaBySlugRequest",
    "ListPersonasUseCase",
    "UpdatePersonaUseCase",
    "DeletePersonaUseCase",
    # Query use-case classes
    "DerivePersonasUseCase",
    "GetPersonaUseCase",
    # Legacy function-based use cases (backwards compatibility)
    "derive_personas",
    "derive_personas_by_app_type",
    "get_apps_for_persona",
    "get_epics_for_persona",
    "get_epics_for_story",
    "get_journeys_for_story",
    "get_related_stories",
    "get_story_cross_references",
    "get_app_cross_references",
    "get_epics_for_app",
    "get_journeys_for_app",
    "get_personas_for_app",
    "get_stories_for_app",
    "get_accelerator_cross_references",
    "get_apps_for_accelerator",
    "get_code_info_for_accelerator",
    "get_dependent_accelerators",
    "get_fed_by_accelerators",
    "get_journeys_for_accelerator",
    "get_publish_integrations",
    "get_source_integrations",
    "get_stories_for_accelerator",
]

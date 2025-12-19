"""Use cases for sphinx_hcd.

Business logic for cross-referencing, deriving entities, and CRUD operations.
"""

# CRUD use-cases by entity type
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
    ListPersonasUseCase,
    UpdatePersonaUseCase,
)
# Query use-cases
from .queries import (
    DerivePersonasUseCase,
    GetPersonaUseCase,
)
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
    # Accelerator CRUD
    "CreateAcceleratorUseCase",
    "GetAcceleratorUseCase",
    "ListAcceleratorsUseCase",
    "UpdateAcceleratorUseCase",
    "DeleteAcceleratorUseCase",
    # App CRUD
    "CreateAppUseCase",
    "GetAppUseCase",
    "ListAppsUseCase",
    "UpdateAppUseCase",
    "DeleteAppUseCase",
    # Epic CRUD
    "CreateEpicUseCase",
    "GetEpicUseCase",
    "ListEpicsUseCase",
    "UpdateEpicUseCase",
    "DeleteEpicUseCase",
    # Integration CRUD
    "CreateIntegrationUseCase",
    "GetIntegrationUseCase",
    "ListIntegrationsUseCase",
    "UpdateIntegrationUseCase",
    "DeleteIntegrationUseCase",
    # Journey CRUD
    "CreateJourneyUseCase",
    "GetJourneyUseCase",
    "ListJourneysUseCase",
    "UpdateJourneyUseCase",
    "DeleteJourneyUseCase",
    # Persona CRUD
    "CreatePersonaUseCase",
    "ListPersonasUseCase",
    "UpdatePersonaUseCase",
    "DeletePersonaUseCase",
    # Story CRUD
    "CreateStoryUseCase",
    "GetStoryUseCase",
    "ListStoriesUseCase",
    "UpdateStoryUseCase",
    "DeleteStoryUseCase",
    # Query use-cases
    "DerivePersonasUseCase",
    "GetPersonaUseCase",
    # Persona derivation functions
    "derive_personas",
    "derive_personas_by_app_type",
    "get_apps_for_persona",
    "get_epics_for_persona",
    # Story references
    "get_epics_for_story",
    "get_journeys_for_story",
    "get_related_stories",
    "get_story_cross_references",
    # App references
    "get_app_cross_references",
    "get_epics_for_app",
    "get_journeys_for_app",
    "get_personas_for_app",
    "get_stories_for_app",
    # Accelerator references
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

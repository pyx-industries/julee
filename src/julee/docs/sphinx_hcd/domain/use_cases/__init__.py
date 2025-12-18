"""Use cases for sphinx_hcd.

Business logic for cross-referencing and deriving entities.
"""

from .derive_personas import (
    derive_personas,
    derive_personas_by_app_type,
    get_apps_for_persona,
    get_epics_for_persona,
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

__all__ = [
    # Persona derivation
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

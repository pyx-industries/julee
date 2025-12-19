"""MCP tools for HCD domain operations.

Tool modules for CRUD operations on HCD domain objects.
"""

from .accelerators import (
    create_accelerator,
    delete_accelerator,
    get_accelerator,
    list_accelerators,
    update_accelerator,
)
from .apps import create_app, delete_app, get_app, list_apps, update_app
from .epics import create_epic, delete_epic, get_epic, list_epics, update_epic
from .integrations import (
    create_integration,
    delete_integration,
    get_integration,
    list_integrations,
    update_integration,
)
from .journeys import (
    create_journey,
    delete_journey,
    get_journey,
    list_journeys,
    update_journey,
)
from .personas import (
    create_persona,
    delete_persona,
    get_persona,
    list_personas,
    update_persona,
)
from .stories import (
    create_story,
    delete_story,
    get_story,
    list_stories,
    update_story,
)

__all__ = [
    # Stories
    "create_story",
    "get_story",
    "list_stories",
    "update_story",
    "delete_story",
    # Epics
    "create_epic",
    "get_epic",
    "list_epics",
    "update_epic",
    "delete_epic",
    # Journeys
    "create_journey",
    "get_journey",
    "list_journeys",
    "update_journey",
    "delete_journey",
    # Personas
    "create_persona",
    "get_persona",
    "list_personas",
    "update_persona",
    "delete_persona",
    # Accelerators
    "create_accelerator",
    "get_accelerator",
    "list_accelerators",
    "update_accelerator",
    "delete_accelerator",
    # Integrations
    "create_integration",
    "get_integration",
    "list_integrations",
    "update_integration",
    "delete_integration",
    # Apps
    "create_app",
    "get_app",
    "list_apps",
    "update_app",
    "delete_app",
]

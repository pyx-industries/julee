"""Use cases for sphinx_hcd.

Business logic for cross-referencing and deriving entities.
"""

from .derive_personas import (
    derive_personas,
    derive_personas_by_app_type,
    get_apps_for_persona,
    get_epics_for_persona,
)

__all__ = [
    "derive_personas",
    "derive_personas_by_app_type",
    "get_apps_for_persona",
    "get_epics_for_persona",
]

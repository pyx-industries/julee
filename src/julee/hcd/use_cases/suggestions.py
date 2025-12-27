"""Suggestion computation support for HCD entities.

Provides repository aggregates for computing contextual suggestions
based on domain semantics and cross-entity validation rules.

Note: Actual suggestion computation and formatting is handled by the
API layer (apps/api/hcd/suggestions.py) which has visibility into
MCP tool names and response formats.
"""

from dataclasses import dataclass

from julee.hcd.repositories.accelerator import AcceleratorRepository
from julee.hcd.repositories.app import AppRepository
from julee.hcd.repositories.epic import EpicRepository
from julee.hcd.repositories.integration import IntegrationRepository
from julee.hcd.repositories.journey import JourneyRepository
from julee.hcd.repositories.story import StoryRepository

__all__ = ["SuggestionRepositories"]


@dataclass
class SuggestionRepositories:
    """Repository aggregate for suggestion computation.

    Groups all repositories needed by suggestion computation functions,
    replacing the SuggestionContextService abstraction with direct
    repository access.

    Used by MCP tools to compute contextual suggestions for entities.
    """

    stories: StoryRepository
    epics: EpicRepository
    journeys: JourneyRepository
    apps: AppRepository
    accelerators: AcceleratorRepository
    integrations: IntegrationRepository

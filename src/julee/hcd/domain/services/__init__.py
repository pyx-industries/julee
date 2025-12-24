"""Domain service protocols for HCD.

Service protocols define interfaces for cross-entity operations.
Implementations live in hcd/services/.
"""

from .suggestion_context import SuggestionContextService

__all__ = ["SuggestionContextService"]

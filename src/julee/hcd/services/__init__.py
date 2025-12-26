"""Domain service protocols for HCD.

Service protocols define interfaces for cross-entity operations.
Implementations live in hcd/infrastructure/services/.

Note: SuggestionContextService was removed as part of doctrine cleanup.
Single-entity operations now use repositories directly via SuggestionRepositories
aggregate in use_cases/suggestions.py.
"""

__all__: list[str] = []

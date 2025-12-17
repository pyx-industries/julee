"""Sphinx application layer for sphinx_hcd.

Contains Sphinx-specific code:
- adapters.py: SyncRepositoryAdapter for sync access to async repos
- context.py: HCDContext for unified repository access
- directives/: Sphinx directive implementations
- event_handlers/: Sphinx lifecycle event handlers
"""

from .adapters import SyncRepositoryAdapter

__all__ = ["SyncRepositoryAdapter"]

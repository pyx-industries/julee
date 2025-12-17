"""Sphinx application layer for sphinx_hcd.

Contains Sphinx-specific code:
- adapters.py: SyncRepositoryAdapter for sync access to async repos
- context.py: HCDContext for unified repository access
- initialization.py: Builder-inited handlers
- directives/: Sphinx directive implementations
- event_handlers/: Sphinx lifecycle event handlers
"""

from .adapters import SyncRepositoryAdapter
from .context import (
    HCDContext,
    ensure_hcd_context,
    get_hcd_context,
    set_hcd_context,
)
from .initialization import initialize_hcd_context, purge_doc_from_context

__all__ = [
    "HCDContext",
    "SyncRepositoryAdapter",
    "ensure_hcd_context",
    "get_hcd_context",
    "initialize_hcd_context",
    "purge_doc_from_context",
    "set_hcd_context",
]

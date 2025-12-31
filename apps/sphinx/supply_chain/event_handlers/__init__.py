"""Event handlers for sphinx_supply_chain.

Consolidates all Sphinx event handlers for the Supply Chain extension.
"""

from .doctree_resolved import on_doctree_resolved
from .env_merge import on_env_merge_info
from .env_purge_doc import on_env_purge_doc

__all__ = [
    "on_doctree_resolved",
    "on_env_merge_info",
    "on_env_purge_doc",
]

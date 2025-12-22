"""Event handlers for sphinx_hcd.

Consolidates all Sphinx event handlers for the HCD extension.
"""

from .builder_inited import on_builder_inited
from .doctree_read import on_doctree_read
from .doctree_resolved import on_doctree_resolved
from .env_check_consistency import on_env_check_consistency
from .env_merge import on_env_merge_info
from .env_purge_doc import on_env_purge_doc

__all__ = [
    "on_builder_inited",
    "on_doctree_read",
    "on_doctree_resolved",
    "on_env_check_consistency",
    "on_env_merge_info",
    "on_env_purge_doc",
]

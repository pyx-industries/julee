"""Doctree-resolved event handler for sphinx_supply_chain.

Processes accelerator placeholders that need cross-document data.
"""

import logging

from apps.sphinx.hcd.context import get_hcd_context

from ..dependencies import get_placeholder_handlers

logger = logging.getLogger(__name__)


def on_doctree_resolved(app, doctree, docname):
    """Process doctree after all documents are read.

    This handler runs after ALL documents have been read, allowing
    cross-document references to be resolved.

    Uses the handler registry to process all placeholder types.

    Args:
        app: Sphinx application instance
        doctree: The document tree
        docname: The document name
    """
    # Use HCD context for cross-entity queries (apps, integrations)
    context = get_hcd_context(app)
    handlers = get_placeholder_handlers()

    for handler in handlers:
        try:
            handler.handle(app, doctree, docname, context)
        except Exception as e:
            logger.warning(
                f"Error in {handler.name} placeholder handler for {docname}: {e}"
            )

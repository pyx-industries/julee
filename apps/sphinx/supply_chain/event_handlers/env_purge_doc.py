"""Env purge doc event handler for sphinx_supply_chain.

Handles cleanup when documents are removed or rebuilt.
"""

from apps.sphinx.hcd.context import get_hcd_context


def on_env_purge_doc(app, env, docname):
    """Clean up supply chain state when a document is purged.

    Args:
        app: Sphinx application instance
        env: Sphinx environment
        docname: Document being purged
    """
    # Remove from documented accelerators tracker
    if hasattr(env, "documented_accelerators"):
        env.documented_accelerators.discard(docname)

    # Clear accelerators from this document via HCD context
    # (accelerator repo is currently on HCD context during migration)
    context = get_hcd_context(app)
    if hasattr(context, "accelerator_repo"):
        context.accelerator_repo.run_async(
            context.accelerator_repo.async_repo.clear_by_docname(docname)
        )

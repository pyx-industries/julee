"""Env-purge-doc event handler for sphinx_hcd.

Clears document-specific state when a document is re-read.
"""

from ..directives import (
    clear_accelerator_state,
    clear_epic_state,
    clear_journey_state,
)


def on_env_purge_doc(app, env, docname):
    """Clear state when a document is re-read.

    This handler runs when a document needs to be re-read (incremental build).
    It clears any state associated with that document.

    Args:
        app: Sphinx application instance
        env: Sphinx build environment
        docname: The document name being purged
    """
    # Clear epic state for this document
    clear_epic_state(app, env, docname)

    # Clear journey state for this document
    clear_journey_state(app, env, docname)

    # Clear accelerator state for this document
    clear_accelerator_state(app, env, docname)

    # Clear documented apps tracker
    if hasattr(env, "documented_apps") and docname in env.documented_apps:
        env.documented_apps.discard(docname)

    # Clear documented integrations tracker
    if (
        hasattr(env, "documented_integrations")
        and docname in env.documented_integrations
    ):
        env.documented_integrations.discard(docname)

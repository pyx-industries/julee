"""Doctree-resolved event handler for sphinx_hcd.

Processes placeholders that need cross-document data (all documents read).
"""

from ..directives import (
    process_accelerator_placeholders,
    process_app_placeholders,
    process_dependency_graph_placeholder,
    process_epic_placeholders,
    process_integration_placeholders,
    process_persona_placeholders,
)


def on_doctree_resolved(app, doctree, docname):
    """Process doctree after all documents are read.

    This handler runs after ALL documents have been read, allowing
    cross-document references to be resolved.

    Args:
        app: Sphinx application instance
        doctree: The document tree
        docname: The document name
    """
    # Process app placeholders (need story/journey/epic registries)
    process_app_placeholders(app, doctree, docname)

    # Process epic placeholders (need story registry)
    process_epic_placeholders(app, doctree, docname)

    # Process accelerator placeholders (need many registries)
    process_accelerator_placeholders(app, doctree, docname)

    # Process integration placeholders
    process_integration_placeholders(app, doctree, docname)

    # Process persona diagram placeholders (need epic/story registries)
    process_persona_placeholders(app, doctree, docname)

    # Process journey dependency graph placeholder (needs all journeys)
    process_dependency_graph_placeholder(app, doctree, docname)

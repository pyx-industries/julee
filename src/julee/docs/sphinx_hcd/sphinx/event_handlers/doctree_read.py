"""Doctree-read event handler for sphinx_hcd.

Processes placeholders that need to be replaced after all directives
in a document have been parsed but before the doctree is pickled.
"""

from ..directives import (
    process_journey_steps,
    process_story_seealso_placeholders,
)


def on_doctree_read(app, doctree):
    """Process doctree after all directives are parsed.

    This handler runs after a document is read but before it's pickled.
    Used for placeholders that need to be resolved within a single document.

    Args:
        app: Sphinx application instance
        doctree: The document tree
    """
    # Process story seealso placeholders
    process_story_seealso_placeholders(app, doctree)

    # Process journey steps placeholder
    process_journey_steps(app, doctree)

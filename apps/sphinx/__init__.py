"""Consolidated Sphinx extension for Julee.

Provides documentation directives for all accelerators:
- HCD: Personas, journeys, stories, epics, apps, integrations, accelerators
- C4: Software systems, containers, components, relationships, deployments
"""

from sphinx.application import Sphinx


def setup(app: Sphinx) -> dict:
    """Set up the consolidated Julee Sphinx extension.

    Registers directives and event handlers for both HCD and C4.
    """
    from .c4 import setup as setup_c4
    from .hcd import setup as setup_hcd

    # Set up HCD directives
    setup_hcd(app)

    # Set up C4 directives
    setup_c4(app)

    return {
        "version": "2.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }

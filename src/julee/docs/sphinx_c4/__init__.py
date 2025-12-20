"""sphinx_c4: C4 software architecture modeling for Sphinx.

This package implements C4 model concepts for documenting software architecture:
- Software Systems, Containers, Components (core abstractions)
- Relationships between elements
- Deployment Nodes for infrastructure modeling
- Dynamic Steps for sequence diagrams

The package shares HCD Personas for the "Person" abstraction in C4 diagrams.

Usage in conf.py::

    extensions = ["julee.docs.sphinx_c4"]
"""

__version__ = "0.1.0"


def setup(app):
    """Set up the Sphinx C4 extension.

    Args:
        app: Sphinx application instance

    Returns:
        Extension metadata
    """
    from .sphinx import setup as sphinx_setup

    return sphinx_setup(app)

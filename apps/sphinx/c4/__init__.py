"""Sphinx integration for C4 architecture model.

Provides Sphinx directives for defining and visualizing C4 elements.
"""

from .directives import setup as setup_directives

__all__ = ["setup"]


def setup(app):
    """Setup the Sphinx C4 extension.

    Args:
        app: Sphinx application instance

    Returns:
        Extension metadata
    """
    setup_directives(app)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

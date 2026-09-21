"""Code-outward documentation for julee solutions.

This kit projects a solution into documentation: its personas, journeys,
epics and stories, its applications and integrations, and the bounded
contexts its code already describes (ADR 006).

It is a viewpoint kit. Its bounded contexts describe a solution rather
than implement part of one, which is why the manifest sets
``viewpoint=True``.

Use it in a solution's ``conf.py``::

    extensions = ["julee_viewpoints.sphinx_hcd"]
"""

from julee.core.entities.kit import Kit

kit = Kit(
    slug="viewpoints",
    name="Code-outward documentation",
    package="julee_viewpoints",
    viewpoint=True,
    contributes={"sphinx.extension": "julee_viewpoints.sphinx_hcd"},
)

__all__ = ["kit"]

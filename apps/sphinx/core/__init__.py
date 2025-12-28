"""Sphinx Core Doctrine Extension.

Provides Sphinx directives for reflexive documentation - rendering
core entity docstrings and introspecting module structure to generate
documentation as projections rather than parallel content.
"""

from sphinx.util import logging

logger = logging.getLogger(__name__)


def setup(app):
    """Set up core doctrine extension for Sphinx."""
    from .directives.catalog import (
        EntityCatalogDirective,
        RepositoryCatalogDirective,
        UseCaseCatalogDirective,
    )
    from .directives.concept import (
        CoreConceptDirective,
        DoctrineConstantDirective,
    )
    from .directives.solution import (
        BoundedContextListDirective,
        SolutionStructureDirective,
    )

    # Register concept directives
    app.add_directive("core-concept", CoreConceptDirective)
    app.add_directive("doctrine-constant", DoctrineConstantDirective)

    # Register catalog directives
    app.add_directive("entity-catalog", EntityCatalogDirective)
    app.add_directive("repository-catalog", RepositoryCatalogDirective)
    app.add_directive("usecase-catalog", UseCaseCatalogDirective)

    # Register solution structure directives
    app.add_directive("solution-structure", SolutionStructureDirective)
    app.add_directive("bounded-context-list", BoundedContextListDirective)

    logger.info("Loaded apps.sphinx.core extension")

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

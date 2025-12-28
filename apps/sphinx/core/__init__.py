"""Sphinx Core Doctrine Extension.

Provides Sphinx directives for code-outward documentation - generating
documentation from code rather than maintaining parallel RST content.

Information Architecture Pattern
--------------------------------
The julee framework provides the information architecture (vocabulary,
structure, relationships). Solutions provide the content (their specific
entities, use cases, bounded contexts).

This extension enables that pattern by:

1. **Rendering docstrings as documentation** - Entity docstrings in
   ``julee.core.entities`` define concepts; autodoc renders them.

2. **Introspecting modules to generate catalogs** - The ``entity-catalog``,
   ``repository-catalog``, and ``usecase-catalog`` directives discover
   what exists in a solution and render it automatically.

3. **Projecting solution content through framework lenses** - The framework
   defines WHAT to show (entities, use cases, protocols); solutions provide
   the actual instances to display.

Recursive Linking Pattern
-------------------------
Documentation forms a navigable dependency graph::

    Concept (julee.core.entities.*)
      → lists interfaces (solution's {bc}/repositories/, {bc}/services/)
        → links to implementations ({bc}/infrastructure/)
          → links to applications using them (via DI containers)

Directives Provided
-------------------
- ``core-concept`` - Render a core entity's docstring as documentation
- ``doctrine-constant`` - Render doctrine constants and their values
- ``entity-catalog`` - List all entities in the solution by bounded context
- ``repository-catalog`` - List all repository protocols in the solution
- ``usecase-catalog`` - List all use cases in the solution
- ``solution-structure`` - Show the solution's overall structure
- ``solution-overview`` - Show solution name and description
- ``bounded-context-list`` - List all bounded contexts in the solution
- ``application-list`` - List all applications in the solution
- ``deployment-list`` - List all deployments in the solution
- ``nested-solution-list`` - List nested solutions (e.g., contrib modules)
- ``viewpoint-links`` - Show links to viewpoint BCs (HCD, C4)
"""

from sphinx.util import logging

logger = logging.getLogger(__name__)


def setup(app):
    """Set up core doctrine extension for Sphinx."""
    from .context import initialize_core_context
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
        ApplicationListDirective,
        BoundedContextListDirective,
        DeploymentListDirective,
        NestedSolutionListDirective,
        SolutionOverviewDirective,
        SolutionStructureDirective,
        ViewpointLinksDirective,
    )

    # Initialize context at builder-inited
    app.connect("builder-inited", lambda app: initialize_core_context(app))

    # Register concept directives
    app.add_directive("core-concept", CoreConceptDirective)
    app.add_directive("doctrine-constant", DoctrineConstantDirective)

    # Register catalog directives
    app.add_directive("entity-catalog", EntityCatalogDirective)
    app.add_directive("repository-catalog", RepositoryCatalogDirective)
    app.add_directive("usecase-catalog", UseCaseCatalogDirective)

    # Register solution structure directives
    app.add_directive("solution-structure", SolutionStructureDirective)
    app.add_directive("solution-overview", SolutionOverviewDirective)
    app.add_directive("bounded-context-list", BoundedContextListDirective)
    app.add_directive("application-list", ApplicationListDirective)
    app.add_directive("deployment-list", DeploymentListDirective)
    app.add_directive("nested-solution-list", NestedSolutionListDirective)
    app.add_directive("viewpoint-links", ViewpointLinksDirective)

    logger.info("Loaded apps.sphinx.core extension")

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

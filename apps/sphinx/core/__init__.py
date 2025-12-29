"""Sphinx Core Doctrine Extension - Technical Manual Viewpoint.

Provides Sphinx directives for code-outward documentation - generating
documentation from code rather than maintaining parallel RST content.

This is one of three viewpoint extensions in julee:

- ``apps.sphinx.core`` - Technical Manual viewpoint (this extension)
- ``apps.sphinx.hcd`` - Human-Centred Design viewpoint
- ``apps.sphinx.c4`` - Architecture viewpoint

Each viewpoint projects the SAME solution content through a different lens.

Two Documentation Modes
-----------------------
**Framework documentation** screams software engineering::

    /
    ├── Core (julee.core)      ← BC: Clean Architecture concepts
    ├── HCD (julee.hcd)        ← BC: Human-Centred Design concepts
    ├── C4 (julee.c4)          ← BC: Architecture modeling concepts
    └── API Reference

**Solution documentation** screams the solution's domain::

    /
    ├── Henchmen and Minions   ← Solution BC (business capability)
    ├── Very Large Kites       ← Solution BC
    ├── Human Centred Design   ← Viewpoint (julee.hcd projection)
    ├── Architecture           ← Viewpoint (julee.c4 projection)
    └── Technical Manual       ← Viewpoint (julee.core projection)

The framework BCs ARE the viewpoints because the framework's domain IS
software engineering methodology.

Information Architecture Pattern
--------------------------------
The julee framework provides the information architecture (vocabulary,
structure, relationships). Solutions provide the content (their specific
entities, use cases, bounded contexts).

This extension enables that pattern by:

1. **Rendering docstrings as documentation** - Entity docstrings in
   ``julee.core.entities`` define concepts; autodoc renders them.

2. **Introspecting modules to generate catalogs** - The catalog directives
   discover what exists in a solution and render it automatically.

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
**Concept directives:**

- ``core-concept`` - Render a core entity's docstring as documentation
- ``doctrine-constant`` - Render doctrine constants and their values

**Catalog directives** (introspect and list solution content):

- ``entity-catalog`` - List all entities in the solution by bounded context
- ``repository-catalog`` - List all repository protocols in the solution
- ``service-protocol-catalog`` - List all service protocols in the solution
- ``usecase-catalog`` - List all use cases in the solution

**Solution structure directives:**

- ``solution-structure`` - Show the solution's overall structure
- ``solution-overview`` - Show solution name and description
- ``bounded-context-list`` - List all bounded contexts in the solution
- ``application-list`` - List all applications in the solution
- ``deployment-list`` - List all deployments in the solution
- ``nested-solution-list`` - List nested solutions (e.g., contrib modules)
- ``viewpoint-links`` - Show links to viewpoint BCs (HCD, C4)
- ``bc-hub`` - Show detailed BC contents (use cases, apps, personas)
- ``bounded-context-map`` - Show BC overview with grouping and dependencies
"""

from sphinx.util import logging

logger = logging.getLogger(__name__)


def setup(app):
    """Set up core doctrine extension for Sphinx."""
    from .context import initialize_core_context
    from .directives.catalog import (
        EntityCatalogDirective,
        RepositoryCatalogDirective,
        ServiceProtocolCatalogDirective,
        UseCaseCatalogDirective,
    )
    from .directives.concept import (
        CoreConceptDirective,
        DoctrineConstantDirective,
    )
    from .directives.bounded_context_hub import BoundedContextHubDirective
    from .directives.bc_map import BoundedContextMapDirective
    from .directives.solution import (
        ApplicationListDirective,
        BoundedContextListDirective,
        DeploymentListDirective,
        NestedSolutionListDirective,
        SolutionOverviewDirective,
        SolutionStructureDirective,
        ViewpointLinksDirective,
    )
    from apps.sphinx.shared.documentation_mapping import get_documentation_mapping
    from apps.sphinx.shared.roles import make_semantic_role
    from julee.core.entities.application import Application
    from julee.core.entities.bounded_context import BoundedContext

    # Initialize context at builder-inited
    app.connect("builder-inited", lambda app: initialize_core_context(app))

    # Get documentation mapping (shares patterns with other extensions)
    mapping = get_documentation_mapping()

    # Register Core cross-reference roles using semantic mapping
    # :bc:`slug` -> autoapi/julee/{slug}/index.html
    BCRole = make_semantic_role(BoundedContext, mapping)
    app.add_role("bc", BCRole())

    # :app:`slug` -> autoapi/apps/{slug}/index.html
    AppRole = make_semantic_role(Application, mapping)
    app.add_role("app", AppRole())

    # Register concept directives
    app.add_directive("core-concept", CoreConceptDirective)
    app.add_directive("doctrine-constant", DoctrineConstantDirective)

    # Register catalog directives
    app.add_directive("entity-catalog", EntityCatalogDirective)
    app.add_directive("repository-catalog", RepositoryCatalogDirective)
    app.add_directive("service-protocol-catalog", ServiceProtocolCatalogDirective)
    app.add_directive("usecase-catalog", UseCaseCatalogDirective)

    # Register solution structure directives
    app.add_directive("solution-structure", SolutionStructureDirective)
    app.add_directive("solution-overview", SolutionOverviewDirective)
    app.add_directive("bounded-context-list", BoundedContextListDirective)
    app.add_directive("application-list", ApplicationListDirective)
    app.add_directive("deployment-list", DeploymentListDirective)
    app.add_directive("nested-solution-list", NestedSolutionListDirective)
    app.add_directive("viewpoint-links", ViewpointLinksDirective)
    app.add_directive("bc-hub", BoundedContextHubDirective)
    app.add_directive("bounded-context-map", BoundedContextMapDirective)

    logger.info("Loaded apps.sphinx.core extension")

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

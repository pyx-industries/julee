"""Sphinx C4 Architecture Model Extension.

Provides Sphinx directives for documenting Julee solutions through the
C4 Architecture viewpoint - projecting solution content in terms of
software systems, containers, components, and deployment nodes.

C4 as a Viewpoint
-----------------
The C4 extension is one of three viewpoint projections in julee:

- ``julee.hcd`` → Human-Centered Design viewpoint
- ``julee.c4`` → Architecture viewpoint (this extension)
- ``julee.core`` → Technical Manual viewpoint

Each viewpoint projects the SAME solution content through a different lens.
A Container defined in C4 terms links to the Accelerator that powers it
and the Apps it serves. The viewpoints are interconnected, not siloed.

Two Documentation Modes
-----------------------
**Framework documentation** screams software engineering - its bounded
contexts ARE the viewpoints (HCD, C4, Core) because the framework's domain
is software engineering methodology.

**Solution documentation** screams its business domain - bounded contexts
like "Henchmen Management" or "Very Large Kites" appear at root level,
with viewpoints projecting their content through HCD/C4/Core lenses.

C4 Model Levels
---------------
The C4 model provides four levels of abstraction:

1. **Context** - How the system fits into the world (people and other systems)
2. **Container** - High-level technology choices (APIs, databases, etc.)
3. **Component** - Logical components within containers
4. **Code** - Implementation details (typically via autodoc, not C4 directives)

Hub Pages
---------
C4 entities form hub pages that link outward to related content:

- **SoftwareSystem** → containers, external relationships
- **Container** → components, technologies, relationships
- **Component** → use cases implemented, relationships
- **DeploymentNode** → containers deployed, infrastructure

Directives Provided
-------------------
Define directives: ``define-software-system``, ``define-container``,
``define-component``, ``define-relationship``, ``define-deployment-node``,
``define-dynamic-step``

Index directives: ``software-system-index``, ``container-index``,
``component-index``, ``relationship-index``, ``deployment-node-index``

Diagram directives: ``system-context-diagram``, ``container-diagram``,
``component-diagram``, ``system-landscape-diagram``, ``deployment-diagram``,
``dynamic-diagram``
"""

from .directives import setup as setup_directives



def setup(app):
    """Setup the Sphinx C4 extension.

    Args:
        app: Sphinx application instance

    Returns:
        Extension metadata
    """
    setup_directives(app)

    # Register C4 cross-reference roles
    from apps.sphinx.shared import make_conditional_role, make_page_role
    from julee.c4.use_cases.crud import GetContainerRequest

    from .context import get_c4_context

    # :system:`slug` -> index.html (System = Solution view)
    # For now, link to solution root; could be enhanced to link to
    # a dedicated system page if one exists
    SystemRole = make_page_role("index")
    app.add_role("system", SystemRole())

    # :container:`slug` -> Application OR BC page depending on container type
    def lookup_container(slug, sphinx_app):
        """Look up container and return appropriate page.

        Container maps to either Application or BoundedContext.
        """
        try:
            c4_ctx = get_c4_context(sphinx_app)
            response = c4_ctx.get_container.execute_sync(
                GetContainerRequest(slug=slug)
            )
            if response.entity:
                # If container has parent_system, it's likely an app
                # For now, try apps first, then BC
                return f"autoapi/apps/{slug}/index"
        except Exception:
            pass
        # Fallback to BC
        return f"autoapi/julee/{slug}/index"

    ContainerRole = make_conditional_role(lookup_container)
    app.add_role("container", ContainerRole())

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

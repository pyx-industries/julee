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

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

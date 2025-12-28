"""C4 Sphinx directives.

Provides directives for defining C4 elements, generating diagrams, and listing elements.
"""

from .component import DefineComponentDirective
from .container import DefineContainerDirective
from .deployment_node import DefineDeploymentNodeDirective
from .diagrams import (
    ComponentDiagramDirective,
    ContainerDiagramDirective,
    DeploymentDiagramDirective,
    DynamicDiagramDirective,
    SystemContextDiagramDirective,
    SystemLandscapeDiagramDirective,
    process_c4_diagram_placeholders,
)
from .dynamic_step import DefineDynamicStepDirective
from .indexes import (
    ComponentIndexDirective,
    ContainerIndexDirective,
    DeploymentNodeIndexDirective,
    RelationshipIndexDirective,
    SoftwareSystemIndexDirective,
)
from .relationship import DefineRelationshipDirective
from .software_system import DefineSoftwareSystemDirective


def setup(app):
    """Register C4 directives with Sphinx.

    Args:
        app: Sphinx application instance
    """
    # Definition directives
    app.add_directive("define-software-system", DefineSoftwareSystemDirective)
    app.add_directive("define-container", DefineContainerDirective)
    app.add_directive("define-component", DefineComponentDirective)
    app.add_directive("define-relationship", DefineRelationshipDirective)
    app.add_directive("define-deployment-node", DefineDeploymentNodeDirective)
    app.add_directive("define-dynamic-step", DefineDynamicStepDirective)

    # Diagram directives
    app.add_directive("system-context-diagram", SystemContextDiagramDirective)
    app.add_directive("container-diagram", ContainerDiagramDirective)
    app.add_directive("component-diagram", ComponentDiagramDirective)
    app.add_directive("system-landscape-diagram", SystemLandscapeDiagramDirective)
    app.add_directive("deployment-diagram", DeploymentDiagramDirective)
    app.add_directive("dynamic-diagram", DynamicDiagramDirective)

    # Index directives
    app.add_directive("software-system-index", SoftwareSystemIndexDirective)
    app.add_directive("container-index", ContainerIndexDirective)
    app.add_directive("component-index", ComponentIndexDirective)
    app.add_directive("relationship-index", RelationshipIndexDirective)
    app.add_directive("deployment-node-index", DeploymentNodeIndexDirective)

    # Register placeholder resolution at doctree-resolved
    app.connect("doctree-resolved", process_c4_diagram_placeholders)

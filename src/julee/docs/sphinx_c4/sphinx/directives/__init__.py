"""C4 Sphinx directives.

Provides directives for defining C4 elements and generating diagrams.
"""

from .base import C4Directive
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
)
from .dynamic_step import DefineDynamicStepDirective
from .relationship import DefineRelationshipDirective
from .software_system import DefineSoftwareSystemDirective

__all__ = [
    "C4Directive",
    "DefineSoftwareSystemDirective",
    "DefineContainerDirective",
    "DefineComponentDirective",
    "DefineRelationshipDirective",
    "DefineDeploymentNodeDirective",
    "DefineDynamicStepDirective",
    "SystemContextDiagramDirective",
    "ContainerDiagramDirective",
    "ComponentDiagramDirective",
    "SystemLandscapeDiagramDirective",
    "DeploymentDiagramDirective",
    "DynamicDiagramDirective",
]


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

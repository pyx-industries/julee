"""C4 domain models.

Core C4 abstractions:
- SoftwareSystem: Highest level, delivers value to users
- Container: Runtime boundary (application or data store)
- Component: Functionality grouping within a container
- Relationship: Connection between elements
- DeploymentNode: Infrastructure for deployment diagrams
- DynamicStep: Numbered interaction for dynamic diagrams
"""

from .component import Component
from .container import Container, ContainerType
from .deployment_node import ContainerInstance, DeploymentNode, NodeType
from .dynamic_step import DynamicStep
from .relationship import ElementType, Relationship
from .software_system import SoftwareSystem, SystemType

__all__ = [
    "SoftwareSystem",
    "SystemType",
    "Container",
    "ContainerType",
    "Component",
    "Relationship",
    "ElementType",
    "DeploymentNode",
    "NodeType",
    "ContainerInstance",
    "DynamicStep",
]

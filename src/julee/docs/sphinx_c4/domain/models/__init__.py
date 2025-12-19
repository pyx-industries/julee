"""C4 domain models.

Core C4 abstractions:
- SoftwareSystem: Highest level, delivers value to users
- Container: Runtime boundary (application or data store)
- Component: Functionality grouping within a container
- Relationship: Connection between elements
- DeploymentNode: Infrastructure for deployment diagrams
- DynamicStep: Numbered interaction for dynamic diagrams
"""

from .software_system import SoftwareSystem, SystemType
from .container import Container, ContainerType
from .component import Component
from .relationship import Relationship, ElementType
from .deployment_node import DeploymentNode, NodeType, ContainerInstance
from .dynamic_step import DynamicStep

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

"""C4 repository protocols.

Defines the abstract interfaces for C4 entity repositories.
"""

from .base import BaseRepository
from .software_system import SoftwareSystemRepository
from .container import ContainerRepository
from .component import ComponentRepository
from .relationship import RelationshipRepository
from .deployment_node import DeploymentNodeRepository
from .dynamic_step import DynamicStepRepository

__all__ = [
    "BaseRepository",
    "SoftwareSystemRepository",
    "ContainerRepository",
    "ComponentRepository",
    "RelationshipRepository",
    "DeploymentNodeRepository",
    "DynamicStepRepository",
]

"""C4 repository protocols.

Defines the abstract interfaces for C4 entity repositories.
"""

from julee.shared.repositories.base import BaseRepository

from .component import ComponentRepository
from .container import ContainerRepository
from .deployment_node import DeploymentNodeRepository
from .dynamic_step import DynamicStepRepository
from .relationship import RelationshipRepository
from .software_system import SoftwareSystemRepository

__all__ = [
    "BaseRepository",
    "SoftwareSystemRepository",
    "ContainerRepository",
    "ComponentRepository",
    "RelationshipRepository",
    "DeploymentNodeRepository",
    "DynamicStepRepository",
]

"""File-backed C4 repository implementations.

These implementations persist entities to JSON files and are suitable
for persistent storage across Sphinx builds.
"""

from .component import FileComponentRepository
from .container import FileContainerRepository
from .deployment_node import FileDeploymentNodeRepository
from .dynamic_step import FileDynamicStepRepository
from .relationship import FileRelationshipRepository
from .software_system import FileSoftwareSystemRepository

__all__ = [
    "FileSoftwareSystemRepository",
    "FileContainerRepository",
    "FileComponentRepository",
    "FileRelationshipRepository",
    "FileDeploymentNodeRepository",
    "FileDynamicStepRepository",
]

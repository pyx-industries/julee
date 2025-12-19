"""C4 domain use cases.

Use cases implement business logic for C4 architecture operations.
"""

from .component import (
    CreateComponentUseCase,
    DeleteComponentUseCase,
    GetComponentUseCase,
    ListComponentsUseCase,
    UpdateComponentUseCase,
)
from .container import (
    CreateContainerUseCase,
    DeleteContainerUseCase,
    GetContainerUseCase,
    ListContainersUseCase,
    UpdateContainerUseCase,
)
from .deployment_node import (
    CreateDeploymentNodeUseCase,
    DeleteDeploymentNodeUseCase,
    GetDeploymentNodeUseCase,
    ListDeploymentNodesUseCase,
    UpdateDeploymentNodeUseCase,
)
from .diagrams import (
    GetComponentDiagramUseCase,
    GetContainerDiagramUseCase,
    GetDeploymentDiagramUseCase,
    GetDynamicDiagramUseCase,
    GetSystemContextDiagramUseCase,
    GetSystemLandscapeDiagramUseCase,
)
from .dynamic_step import (
    CreateDynamicStepUseCase,
    DeleteDynamicStepUseCase,
    GetDynamicStepUseCase,
    ListDynamicStepsUseCase,
    UpdateDynamicStepUseCase,
)
from .relationship import (
    CreateRelationshipUseCase,
    DeleteRelationshipUseCase,
    GetRelationshipUseCase,
    ListRelationshipsUseCase,
    UpdateRelationshipUseCase,
)
from .software_system import (
    CreateSoftwareSystemUseCase,
    DeleteSoftwareSystemUseCase,
    GetSoftwareSystemUseCase,
    ListSoftwareSystemsUseCase,
    UpdateSoftwareSystemUseCase,
)

__all__ = [
    # Software System
    "CreateSoftwareSystemUseCase",
    "GetSoftwareSystemUseCase",
    "ListSoftwareSystemsUseCase",
    "UpdateSoftwareSystemUseCase",
    "DeleteSoftwareSystemUseCase",
    # Container
    "CreateContainerUseCase",
    "GetContainerUseCase",
    "ListContainersUseCase",
    "UpdateContainerUseCase",
    "DeleteContainerUseCase",
    # Component
    "CreateComponentUseCase",
    "GetComponentUseCase",
    "ListComponentsUseCase",
    "UpdateComponentUseCase",
    "DeleteComponentUseCase",
    # Relationship
    "CreateRelationshipUseCase",
    "GetRelationshipUseCase",
    "ListRelationshipsUseCase",
    "UpdateRelationshipUseCase",
    "DeleteRelationshipUseCase",
    # Deployment Node
    "CreateDeploymentNodeUseCase",
    "GetDeploymentNodeUseCase",
    "ListDeploymentNodesUseCase",
    "UpdateDeploymentNodeUseCase",
    "DeleteDeploymentNodeUseCase",
    # Dynamic Step
    "CreateDynamicStepUseCase",
    "GetDynamicStepUseCase",
    "ListDynamicStepsUseCase",
    "UpdateDynamicStepUseCase",
    "DeleteDynamicStepUseCase",
    # Diagrams
    "GetSystemContextDiagramUseCase",
    "GetContainerDiagramUseCase",
    "GetComponentDiagramUseCase",
    "GetSystemLandscapeDiagramUseCase",
    "GetDeploymentDiagramUseCase",
    "GetDynamicDiagramUseCase",
]

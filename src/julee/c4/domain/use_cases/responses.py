"""Response DTOs for C4 API.

Response models wrap domain models, enabling pagination and additional
metadata while maintaining type safety. Following clean architecture,
most responses wrap domain models rather than duplicating their structure.
"""

from pydantic import BaseModel

from ..models.component import Component
from ..models.container import Container
from ..models.deployment_node import DeploymentNode
from ..models.dynamic_step import DynamicStep
from ..models.relationship import Relationship
from ..models.software_system import SoftwareSystem

# =============================================================================
# SoftwareSystem Responses
# =============================================================================


class CreateSoftwareSystemResponse(BaseModel):
    """Response from creating a software system."""

    software_system: SoftwareSystem


class GetSoftwareSystemResponse(BaseModel):
    """Response from getting a software system."""

    software_system: SoftwareSystem | None


class ListSoftwareSystemsResponse(BaseModel):
    """Response from listing software systems."""

    software_systems: list[SoftwareSystem]


class UpdateSoftwareSystemResponse(BaseModel):
    """Response from updating a software system."""

    software_system: SoftwareSystem | None
    found: bool = True


class DeleteSoftwareSystemResponse(BaseModel):
    """Response from deleting a software system."""

    deleted: bool


# =============================================================================
# Container Responses
# =============================================================================


class CreateContainerResponse(BaseModel):
    """Response from creating a container."""

    container: Container


class GetContainerResponse(BaseModel):
    """Response from getting a container."""

    container: Container | None


class ListContainersResponse(BaseModel):
    """Response from listing containers."""

    containers: list[Container]


class UpdateContainerResponse(BaseModel):
    """Response from updating a container."""

    container: Container | None
    found: bool = True


class DeleteContainerResponse(BaseModel):
    """Response from deleting a container."""

    deleted: bool


# =============================================================================
# Component Responses
# =============================================================================


class CreateComponentResponse(BaseModel):
    """Response from creating a component."""

    component: Component


class GetComponentResponse(BaseModel):
    """Response from getting a component."""

    component: Component | None


class ListComponentsResponse(BaseModel):
    """Response from listing components."""

    components: list[Component]


class UpdateComponentResponse(BaseModel):
    """Response from updating a component."""

    component: Component | None
    found: bool = True


class DeleteComponentResponse(BaseModel):
    """Response from deleting a component."""

    deleted: bool


# =============================================================================
# Relationship Responses
# =============================================================================


class CreateRelationshipResponse(BaseModel):
    """Response from creating a relationship."""

    relationship: Relationship


class GetRelationshipResponse(BaseModel):
    """Response from getting a relationship."""

    relationship: Relationship | None


class ListRelationshipsResponse(BaseModel):
    """Response from listing relationships."""

    relationships: list[Relationship]


class UpdateRelationshipResponse(BaseModel):
    """Response from updating a relationship."""

    relationship: Relationship | None
    found: bool = True


class DeleteRelationshipResponse(BaseModel):
    """Response from deleting a relationship."""

    deleted: bool


# =============================================================================
# DeploymentNode Responses
# =============================================================================


class CreateDeploymentNodeResponse(BaseModel):
    """Response from creating a deployment node."""

    deployment_node: DeploymentNode


class GetDeploymentNodeResponse(BaseModel):
    """Response from getting a deployment node."""

    deployment_node: DeploymentNode | None


class ListDeploymentNodesResponse(BaseModel):
    """Response from listing deployment nodes."""

    deployment_nodes: list[DeploymentNode]


class UpdateDeploymentNodeResponse(BaseModel):
    """Response from updating a deployment node."""

    deployment_node: DeploymentNode | None
    found: bool = True


class DeleteDeploymentNodeResponse(BaseModel):
    """Response from deleting a deployment node."""

    deleted: bool


# =============================================================================
# DynamicStep Responses
# =============================================================================


class CreateDynamicStepResponse(BaseModel):
    """Response from creating a dynamic step."""

    dynamic_step: DynamicStep


class GetDynamicStepResponse(BaseModel):
    """Response from getting a dynamic step."""

    dynamic_step: DynamicStep | None


class ListDynamicStepsResponse(BaseModel):
    """Response from listing dynamic steps."""

    dynamic_steps: list[DynamicStep]


class UpdateDynamicStepResponse(BaseModel):
    """Response from updating a dynamic step."""

    dynamic_step: DynamicStep | None
    found: bool = True


class DeleteDynamicStepResponse(BaseModel):
    """Response from deleting a dynamic step."""

    deleted: bool


# =============================================================================
# Diagram Responses
# =============================================================================


class DiagramResponse(BaseModel):
    """Response from generating a serialized diagram (PlantUML, Structurizr, etc.)."""

    content: str
    format: str
    title: str = ""


# -----------------------------------------------------------------------------
# Diagram Data Responses (domain model wrappers)
# -----------------------------------------------------------------------------

from ..models.diagrams import (
    ComponentDiagram,
    ContainerDiagram,
    DeploymentDiagram,
    DynamicDiagram,
    SystemContextDiagram,
    SystemLandscapeDiagram,
)


class GetSystemLandscapeDiagramResponse(BaseModel):
    """Response from computing a system landscape diagram."""

    diagram: SystemLandscapeDiagram


class GetSystemContextDiagramResponse(BaseModel):
    """Response from computing a system context diagram."""

    diagram: SystemContextDiagram | None


class GetContainerDiagramResponse(BaseModel):
    """Response from computing a container diagram."""

    diagram: ContainerDiagram | None


class GetComponentDiagramResponse(BaseModel):
    """Response from computing a component diagram."""

    diagram: ComponentDiagram | None


class GetDeploymentDiagramResponse(BaseModel):
    """Response from computing a deployment diagram."""

    diagram: DeploymentDiagram


class GetDynamicDiagramResponse(BaseModel):
    """Response from computing a dynamic diagram."""

    diagram: DynamicDiagram | None

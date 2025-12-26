"""CRUD use cases for C4 entities.

Generic CRUD operations using base classes from julee.core.use_cases.generic_crud.
Response classes auto-derive field names from entity types (e.g., software_system, containers).
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from julee.c4.entities.component import Component
from julee.c4.entities.container import Container, ContainerType
from julee.c4.entities.deployment_node import DeploymentNode, NodeType
from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.entities.software_system import SoftwareSystem, SystemType
from julee.c4.repositories.component import ComponentRepository
from julee.c4.repositories.container import ContainerRepository
from julee.c4.repositories.deployment_node import DeploymentNodeRepository
from julee.c4.repositories.dynamic_step import DynamicStepRepository
from julee.c4.repositories.relationship import RelationshipRepository
from julee.c4.repositories.software_system import SoftwareSystemRepository
from julee.core.use_cases import generic_crud

# =============================================================================
# SoftwareSystem
# =============================================================================


class GetSoftwareSystemRequest(generic_crud.GetRequest):
    """Get software system by slug."""


class GetSoftwareSystemResponse(generic_crud.GetResponse[SoftwareSystem]):
    """Software system get response."""


class GetSoftwareSystemUseCase(
    generic_crud.GetUseCase[SoftwareSystem, SoftwareSystemRepository]
):
    """Get a software system by slug."""

    response_cls = GetSoftwareSystemResponse


class ListSoftwareSystemsRequest(generic_crud.ListRequest):
    """List all software systems."""


class ListSoftwareSystemsResponse(generic_crud.ListResponse[SoftwareSystem]):
    """Software systems list response."""


class ListSoftwareSystemsUseCase(
    generic_crud.ListUseCase[SoftwareSystem, SoftwareSystemRepository]
):
    """List all software systems."""

    response_cls = ListSoftwareSystemsResponse


class DeleteSoftwareSystemRequest(generic_crud.DeleteRequest):
    """Delete software system by slug."""


class DeleteSoftwareSystemResponse(generic_crud.DeleteResponse):
    """Software system delete response."""


class DeleteSoftwareSystemUseCase(
    generic_crud.DeleteUseCase[SoftwareSystem, SoftwareSystemRepository]
):
    """Delete a software system by slug."""


class CreateSoftwareSystemRequest(BaseModel):
    """Request for creating a software system.

    Accepts string values for enums (e.g., system_type="internal") which are
    coerced to proper enum types. Entity validation (slug/name) runs when
    the entity is constructed.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    system_type: SystemType = Field(
        default=SystemType.INTERNAL, description="Type: internal, external, existing"
    )
    owner: str = Field(default="", description="Owning team")
    technology: str = Field(default="", description="High-level tech stack")
    url: str = Field(default="", description="Link to documentation")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("system_type", mode="before")
    @classmethod
    def coerce_system_type(cls, v):
        """Coerce string to SystemType enum."""
        if isinstance(v, str):
            return SystemType(v)
        return v


class CreateSoftwareSystemResponse(generic_crud.CreateResponse[SoftwareSystem]):
    """Software system create response."""


class CreateSoftwareSystemUseCase(
    generic_crud.CreateUseCase[SoftwareSystem, SoftwareSystemRepository]
):
    """Create a software system."""

    entity_cls = SoftwareSystem
    response_cls = CreateSoftwareSystemResponse


class UpdateSoftwareSystemRequest(generic_crud.UpdateRequest):
    """Update software system fields.

    Accepts string values for enums which are coerced to proper types.
    """

    name: str | None = None
    description: str | None = None
    system_type: SystemType | None = None
    owner: str | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    @field_validator("system_type", mode="before")
    @classmethod
    def coerce_system_type(cls, v):
        """Coerce string to SystemType enum."""
        if v is None:
            return None
        if isinstance(v, str):
            return SystemType(v)
        return v


class UpdateSoftwareSystemResponse(generic_crud.UpdateResponse[SoftwareSystem]):
    """Software system update response."""


class UpdateSoftwareSystemUseCase(
    generic_crud.UpdateUseCase[SoftwareSystem, SoftwareSystemRepository]
):
    """Update a software system."""

    response_cls = UpdateSoftwareSystemResponse


# =============================================================================
# Container
# =============================================================================


class GetContainerRequest(generic_crud.GetRequest):
    """Get container by slug."""


class GetContainerResponse(generic_crud.GetResponse[Container]):
    """Container get response."""


class GetContainerUseCase(generic_crud.GetUseCase[Container, ContainerRepository]):
    """Get a container by slug."""

    response_cls = GetContainerResponse


class ListContainersRequest(generic_crud.ListRequest):
    """List all containers."""


class ListContainersResponse(generic_crud.ListResponse[Container]):
    """Containers list response."""


class ListContainersUseCase(generic_crud.ListUseCase[Container, ContainerRepository]):
    """List all containers."""

    response_cls = ListContainersResponse


class DeleteContainerRequest(generic_crud.DeleteRequest):
    """Delete container by slug."""


class DeleteContainerResponse(generic_crud.DeleteResponse):
    """Container delete response."""


class DeleteContainerUseCase(
    generic_crud.DeleteUseCase[Container, ContainerRepository]
):
    """Delete a container by slug."""


class CreateContainerRequest(BaseModel):
    """Request for creating a container.

    Accepts string values for enums (e.g., container_type="api") which are
    coerced to proper enum types. Entity validation (slug/name) runs when
    the entity is constructed.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    system_slug: str = Field(description="Parent software system slug")
    description: str = Field(default="", description="Human-readable description")
    container_type: ContainerType = Field(
        default=ContainerType.OTHER, description="Type of container"
    )
    technology: str = Field(default="", description="Specific technology stack")
    url: str = Field(default="", description="Link to documentation")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("container_type", mode="before")
    @classmethod
    def coerce_container_type(cls, v):
        """Coerce string to ContainerType enum."""
        if isinstance(v, str):
            return ContainerType(v)
        return v


class CreateContainerResponse(generic_crud.CreateResponse[Container]):
    """Container create response."""


class CreateContainerUseCase(
    generic_crud.CreateUseCase[Container, ContainerRepository]
):
    """Create a container."""

    entity_cls = Container
    response_cls = CreateContainerResponse


class UpdateContainerRequest(generic_crud.UpdateRequest):
    """Update container fields.

    Accepts string values for enums which are coerced to proper types.
    """

    name: str | None = None
    system_slug: str | None = None
    description: str | None = None
    container_type: ContainerType | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    @field_validator("container_type", mode="before")
    @classmethod
    def coerce_container_type(cls, v):
        """Coerce string to ContainerType enum."""
        if v is None:
            return None
        if isinstance(v, str):
            return ContainerType(v)
        return v


class UpdateContainerResponse(generic_crud.UpdateResponse[Container]):
    """Container update response."""


class UpdateContainerUseCase(
    generic_crud.UpdateUseCase[Container, ContainerRepository]
):
    """Update a container."""

    response_cls = UpdateContainerResponse


# =============================================================================
# Component
# =============================================================================


class GetComponentRequest(generic_crud.GetRequest):
    """Get component by slug."""


class GetComponentResponse(generic_crud.GetResponse[Component]):
    """Component get response."""


class GetComponentUseCase(generic_crud.GetUseCase[Component, ComponentRepository]):
    """Get a component by slug."""

    response_cls = GetComponentResponse


class ListComponentsRequest(generic_crud.ListRequest):
    """List all components."""


class ListComponentsResponse(generic_crud.ListResponse[Component]):
    """Components list response."""


class ListComponentsUseCase(generic_crud.ListUseCase[Component, ComponentRepository]):
    """List all components."""

    response_cls = ListComponentsResponse


class DeleteComponentRequest(generic_crud.DeleteRequest):
    """Delete component by slug."""


class DeleteComponentResponse(generic_crud.DeleteResponse):
    """Component delete response."""


class DeleteComponentUseCase(
    generic_crud.DeleteUseCase[Component, ComponentRepository]
):
    """Delete a component by slug."""


class CreateComponentRequest(BaseModel):
    """Request for creating a component.

    Entity validation (slug/name) runs when the entity is constructed.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    container_slug: str = Field(description="Parent container slug")
    system_slug: str = Field(description="Grandparent system slug")
    description: str = Field(default="", description="Human-readable description")
    technology: str = Field(default="", description="Implementation technology")
    interface: str = Field(default="", description="Interface description")
    code_path: str = Field(default="", description="Path to source code")
    url: str = Field(default="", description="Link to documentation")
    tags: list[str] = Field(default_factory=list, description="Classification tags")


class CreateComponentResponse(generic_crud.CreateResponse[Component]):
    """Component create response."""


class CreateComponentUseCase(
    generic_crud.CreateUseCase[Component, ComponentRepository]
):
    """Create a component."""

    entity_cls = Component
    response_cls = CreateComponentResponse


class UpdateComponentRequest(generic_crud.UpdateRequest):
    """Update component fields."""

    name: str | None = None
    container_slug: str | None = None
    system_slug: str | None = None
    description: str | None = None
    technology: str | None = None
    interface: str | None = None
    code_path: str | None = None
    url: str | None = None
    tags: list[str] | None = None


class UpdateComponentResponse(generic_crud.UpdateResponse[Component]):
    """Component update response."""


class UpdateComponentUseCase(
    generic_crud.UpdateUseCase[Component, ComponentRepository]
):
    """Update a component."""

    response_cls = UpdateComponentResponse


# =============================================================================
# Relationship
# =============================================================================


class GetRelationshipRequest(generic_crud.GetRequest):
    """Get relationship by slug."""


class GetRelationshipResponse(generic_crud.GetResponse[Relationship]):
    """Relationship get response."""


class GetRelationshipUseCase(
    generic_crud.GetUseCase[Relationship, RelationshipRepository]
):
    """Get a relationship by slug."""

    response_cls = GetRelationshipResponse


class ListRelationshipsRequest(generic_crud.ListRequest):
    """List all relationships."""


class ListRelationshipsResponse(generic_crud.ListResponse[Relationship]):
    """Relationships list response."""


class ListRelationshipsUseCase(
    generic_crud.ListUseCase[Relationship, RelationshipRepository]
):
    """List all relationships."""

    response_cls = ListRelationshipsResponse


class DeleteRelationshipRequest(generic_crud.DeleteRequest):
    """Delete relationship by slug."""


class DeleteRelationshipResponse(generic_crud.DeleteResponse):
    """Relationship delete response."""


class DeleteRelationshipUseCase(
    generic_crud.DeleteUseCase[Relationship, RelationshipRepository]
):
    """Delete a relationship by slug."""


class CreateRelationshipRequest(BaseModel):
    """Request for creating a relationship.

    Accepts string values for enums (e.g., source_type="container") which are
    coerced to proper enum types. Entity validation runs when constructed.
    Slug is auto-generated if not provided.
    """

    source_type: ElementType = Field(description="Type of source element")
    source_slug: str = Field(description="Slug of source element")
    destination_type: ElementType = Field(description="Type of destination element")
    destination_slug: str = Field(description="Slug of destination element")
    slug: str = Field(
        default="", description="Optional identifier (auto-generated if empty)"
    )
    description: str = Field(default="Uses", description="Relationship description")
    technology: str = Field(default="", description="Protocol/technology used")
    bidirectional: bool = Field(default=False, description="Bidirectional relationship")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("source_type", mode="before")
    @classmethod
    def coerce_source_type(cls, v):
        """Coerce string to ElementType enum."""
        if isinstance(v, str):
            return ElementType(v)
        return v

    @field_validator("destination_type", mode="before")
    @classmethod
    def coerce_destination_type(cls, v):
        """Coerce string to ElementType enum."""
        if isinstance(v, str):
            return ElementType(v)
        return v


class CreateRelationshipResponse(generic_crud.CreateResponse[Relationship]):
    """Relationship create response."""


class CreateRelationshipUseCase(
    generic_crud.CreateUseCase[Relationship, RelationshipRepository]
):
    """Create a relationship."""

    entity_cls = Relationship
    response_cls = CreateRelationshipResponse


class UpdateRelationshipRequest(generic_crud.UpdateRequest):
    """Update relationship fields."""

    description: str | None = None
    technology: str | None = None
    bidirectional: bool | None = None
    tags: list[str] | None = None


class UpdateRelationshipResponse(generic_crud.UpdateResponse[Relationship]):
    """Relationship update response."""


class UpdateRelationshipUseCase(
    generic_crud.UpdateUseCase[Relationship, RelationshipRepository]
):
    """Update a relationship."""

    response_cls = UpdateRelationshipResponse


# =============================================================================
# DeploymentNode
# =============================================================================


class GetDeploymentNodeRequest(generic_crud.GetRequest):
    """Get deployment node by slug."""


class GetDeploymentNodeResponse(generic_crud.GetResponse[DeploymentNode]):
    """Deployment node get response."""


class GetDeploymentNodeUseCase(
    generic_crud.GetUseCase[DeploymentNode, DeploymentNodeRepository]
):
    """Get a deployment node by slug."""

    response_cls = GetDeploymentNodeResponse


class ListDeploymentNodesRequest(generic_crud.ListRequest):
    """List all deployment nodes."""


class ListDeploymentNodesResponse(generic_crud.ListResponse[DeploymentNode]):
    """Deployment nodes list response."""


class ListDeploymentNodesUseCase(
    generic_crud.ListUseCase[DeploymentNode, DeploymentNodeRepository]
):
    """List all deployment nodes."""

    response_cls = ListDeploymentNodesResponse


class DeleteDeploymentNodeRequest(generic_crud.DeleteRequest):
    """Delete deployment node by slug."""


class DeleteDeploymentNodeResponse(generic_crud.DeleteResponse):
    """Deployment node delete response."""


class DeleteDeploymentNodeUseCase(
    generic_crud.DeleteUseCase[DeploymentNode, DeploymentNodeRepository]
):
    """Delete a deployment node by slug."""


class CreateDeploymentNodeRequest(BaseModel):
    """Request for creating a deployment node.

    Accepts string values for enums (e.g., node_type="server") which are
    coerced to proper enum types. Entity validation runs when constructed.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    environment: str = Field(default="production", description="Deployment environment")
    node_type: NodeType = Field(
        default=NodeType.OTHER, description="Infrastructure type"
    )
    technology: str = Field(default="", description="Infrastructure technology")
    description: str = Field(default="", description="Human-readable description")
    parent_slug: str | None = Field(default=None, description="Parent node slug")
    container_instances: list[dict[str, Any]] = Field(
        default_factory=list, description="Deployed container instances"
    )
    properties: dict[str, str] = Field(
        default_factory=dict, description="Additional properties"
    )
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("node_type", mode="before")
    @classmethod
    def coerce_node_type(cls, v):
        """Coerce string to NodeType enum."""
        if isinstance(v, str):
            return NodeType(v)
        return v


class CreateDeploymentNodeResponse(generic_crud.CreateResponse[DeploymentNode]):
    """Deployment node create response."""


class CreateDeploymentNodeUseCase(
    generic_crud.CreateUseCase[DeploymentNode, DeploymentNodeRepository]
):
    """Create a deployment node."""

    entity_cls = DeploymentNode
    response_cls = CreateDeploymentNodeResponse


class UpdateDeploymentNodeRequest(generic_crud.UpdateRequest):
    """Update deployment node fields.

    Accepts string values for enums which are coerced to proper types.
    """

    name: str | None = None
    environment: str | None = None
    node_type: NodeType | None = None
    technology: str | None = None
    description: str | None = None
    parent_slug: str | None = None
    container_instances: list[dict[str, Any]] | None = None
    properties: dict[str, str] | None = None
    tags: list[str] | None = None

    @field_validator("node_type", mode="before")
    @classmethod
    def coerce_node_type(cls, v):
        """Coerce string to NodeType enum."""
        if v is None:
            return None
        if isinstance(v, str):
            return NodeType(v)
        return v


class UpdateDeploymentNodeResponse(generic_crud.UpdateResponse[DeploymentNode]):
    """Deployment node update response."""


class UpdateDeploymentNodeUseCase(
    generic_crud.UpdateUseCase[DeploymentNode, DeploymentNodeRepository]
):
    """Update a deployment node."""

    response_cls = UpdateDeploymentNodeResponse


# =============================================================================
# DynamicStep
# =============================================================================


class GetDynamicStepRequest(generic_crud.GetRequest):
    """Get dynamic step by slug."""


class GetDynamicStepResponse(generic_crud.GetResponse[DynamicStep]):
    """Dynamic step get response."""


class GetDynamicStepUseCase(
    generic_crud.GetUseCase[DynamicStep, DynamicStepRepository]
):
    """Get a dynamic step by slug."""

    response_cls = GetDynamicStepResponse


class ListDynamicStepsRequest(generic_crud.ListRequest):
    """List all dynamic steps."""


class ListDynamicStepsResponse(generic_crud.ListResponse[DynamicStep]):
    """Dynamic steps list response."""


class ListDynamicStepsUseCase(
    generic_crud.ListUseCase[DynamicStep, DynamicStepRepository]
):
    """List all dynamic steps."""

    response_cls = ListDynamicStepsResponse


class DeleteDynamicStepRequest(generic_crud.DeleteRequest):
    """Delete dynamic step by slug."""


class DeleteDynamicStepResponse(generic_crud.DeleteResponse):
    """Dynamic step delete response."""


class DeleteDynamicStepUseCase(
    generic_crud.DeleteUseCase[DynamicStep, DynamicStepRepository]
):
    """Delete a dynamic step by slug."""


class CreateDynamicStepRequest(BaseModel):
    """Request for creating a dynamic step.

    Accepts string values for enums (e.g., source_type="container") which are
    coerced to proper enum types. Entity validation runs when constructed.
    Slug is auto-generated if not provided.
    """

    sequence_name: str = Field(description="Name of the dynamic sequence")
    step_number: int = Field(description="Order within sequence")
    source_type: ElementType = Field(description="Type of calling element")
    source_slug: str = Field(description="Slug of calling element")
    destination_type: ElementType = Field(description="Type of called element")
    destination_slug: str = Field(description="Slug of called element")
    slug: str = Field(
        default="", description="Optional identifier (auto-generated if empty)"
    )
    description: str = Field(default="", description="Step description")
    technology: str = Field(default="", description="Protocol/technology")
    return_value: str = Field(default="", description="Return value description")
    is_async: bool = Field(default=False, description="Is this an async step")

    @field_validator("source_type", mode="before")
    @classmethod
    def coerce_source_type(cls, v):
        """Coerce string to ElementType enum."""
        if isinstance(v, str):
            return ElementType(v)
        return v

    @field_validator("destination_type", mode="before")
    @classmethod
    def coerce_destination_type(cls, v):
        """Coerce string to ElementType enum."""
        if isinstance(v, str):
            return ElementType(v)
        return v


class CreateDynamicStepResponse(generic_crud.CreateResponse[DynamicStep]):
    """Dynamic step create response."""


class CreateDynamicStepUseCase(
    generic_crud.CreateUseCase[DynamicStep, DynamicStepRepository]
):
    """Create a dynamic step."""

    entity_cls = DynamicStep
    response_cls = CreateDynamicStepResponse


class UpdateDynamicStepRequest(generic_crud.UpdateRequest):
    """Update dynamic step fields."""

    step_number: int | None = None
    description: str | None = None
    technology: str | None = None
    return_value: str | None = None
    is_async: bool | None = None


class UpdateDynamicStepResponse(generic_crud.UpdateResponse[DynamicStep]):
    """Dynamic step update response."""


class UpdateDynamicStepUseCase(
    generic_crud.UpdateUseCase[DynamicStep, DynamicStepRepository]
):
    """Update a dynamic step."""

    response_cls = UpdateDynamicStepResponse

"""Request DTOs for C4 API.

Following clean architecture principles, request models define the contract
between the API and external clients. They delegate validation to domain
models and reuse field descriptions to maintain single source of truth.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from ..sphinx_c4.domain.models.component import Component
from ..sphinx_c4.domain.models.container import Container, ContainerType
from ..sphinx_c4.domain.models.deployment_node import (
    ContainerInstance,
    DeploymentNode,
    NodeType,
)
from ..sphinx_c4.domain.models.dynamic_step import DynamicStep
from ..sphinx_c4.domain.models.relationship import ElementType, Relationship
from ..sphinx_c4.domain.models.software_system import SoftwareSystem, SystemType

# =============================================================================
# SoftwareSystem DTOs
# =============================================================================


class CreateSoftwareSystemRequest(BaseModel):
    """Request model for creating a software system."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    system_type: str = Field(default="internal", description="Type: internal, external, existing")
    owner: str = Field(default="", description="Owning team")
    technology: str = Field(default="", description="High-level tech stack")
    url: str = Field(default="", description="Link to documentation")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    def to_domain_model(self) -> SoftwareSystem:
        """Convert to SoftwareSystem."""
        return SoftwareSystem(
            slug=self.slug,
            name=self.name,
            description=self.description,
            system_type=SystemType(self.system_type),
            owner=self.owner,
            technology=self.technology,
            url=self.url,
            tags=self.tags,
            docname="",
        )


class GetSoftwareSystemRequest(BaseModel):
    """Request for getting a software system by slug."""

    slug: str


class ListSoftwareSystemsRequest(BaseModel):
    """Request for listing software systems."""

    pass


class UpdateSoftwareSystemRequest(BaseModel):
    """Request for updating a software system."""

    slug: str
    name: str | None = None
    description: str | None = None
    system_type: str | None = None
    owner: str | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: SoftwareSystem) -> SoftwareSystem:
        """Apply non-None fields to existing software system."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.description is not None:
            updates["description"] = self.description
        if self.system_type is not None:
            updates["system_type"] = SystemType(self.system_type)
        if self.owner is not None:
            updates["owner"] = self.owner
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.url is not None:
            updates["url"] = self.url
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class DeleteSoftwareSystemRequest(BaseModel):
    """Request for deleting a software system by slug."""

    slug: str


# =============================================================================
# Container DTOs
# =============================================================================


class CreateContainerRequest(BaseModel):
    """Request model for creating a container."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    system_slug: str = Field(description="Parent software system slug")
    description: str = Field(default="", description="Human-readable description")
    container_type: str = Field(default="other", description="Type of container")
    technology: str = Field(default="", description="Specific technology stack")
    url: str = Field(default="", description="Link to documentation")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("system_slug")
    @classmethod
    def validate_system_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("system_slug cannot be empty")
        return v.strip()

    def to_domain_model(self) -> Container:
        """Convert to Container."""
        return Container(
            slug=self.slug,
            name=self.name,
            system_slug=self.system_slug,
            description=self.description,
            container_type=ContainerType(self.container_type),
            technology=self.technology,
            url=self.url,
            tags=self.tags,
            docname="",
        )


class GetContainerRequest(BaseModel):
    """Request for getting a container by slug."""

    slug: str


class ListContainersRequest(BaseModel):
    """Request for listing containers."""

    pass


class UpdateContainerRequest(BaseModel):
    """Request for updating a container."""

    slug: str
    name: str | None = None
    system_slug: str | None = None
    description: str | None = None
    container_type: str | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: Container) -> Container:
        """Apply non-None fields to existing container."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.system_slug is not None:
            updates["system_slug"] = self.system_slug
        if self.description is not None:
            updates["description"] = self.description
        if self.container_type is not None:
            updates["container_type"] = ContainerType(self.container_type)
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.url is not None:
            updates["url"] = self.url
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class DeleteContainerRequest(BaseModel):
    """Request for deleting a container by slug."""

    slug: str


# =============================================================================
# Component DTOs
# =============================================================================


class CreateComponentRequest(BaseModel):
    """Request model for creating a component."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    container_slug: str = Field(description="Parent container slug")
    system_slug: str = Field(description="Grandparent system slug")
    description: str = Field(default="", description="Human-readable description")
    technology: str = Field(default="", description="Implementation technology")
    interface: str = Field(default="", description="Interface description")
    code_path: str = Field(default="", description="Link to implementation code")
    url: str = Field(default="", description="Link to documentation")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    def to_domain_model(self) -> Component:
        """Convert to Component."""
        return Component(
            slug=self.slug,
            name=self.name,
            container_slug=self.container_slug,
            system_slug=self.system_slug,
            description=self.description,
            technology=self.technology,
            interface=self.interface,
            code_path=self.code_path,
            url=self.url,
            tags=self.tags,
            docname="",
        )


class GetComponentRequest(BaseModel):
    """Request for getting a component by slug."""

    slug: str


class ListComponentsRequest(BaseModel):
    """Request for listing components."""

    pass


class UpdateComponentRequest(BaseModel):
    """Request for updating a component."""

    slug: str
    name: str | None = None
    container_slug: str | None = None
    system_slug: str | None = None
    description: str | None = None
    technology: str | None = None
    interface: str | None = None
    code_path: str | None = None
    url: str | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: Component) -> Component:
        """Apply non-None fields to existing component."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.container_slug is not None:
            updates["container_slug"] = self.container_slug
        if self.system_slug is not None:
            updates["system_slug"] = self.system_slug
        if self.description is not None:
            updates["description"] = self.description
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.interface is not None:
            updates["interface"] = self.interface
        if self.code_path is not None:
            updates["code_path"] = self.code_path
        if self.url is not None:
            updates["url"] = self.url
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class DeleteComponentRequest(BaseModel):
    """Request for deleting a component by slug."""

    slug: str


# =============================================================================
# Relationship DTOs
# =============================================================================


class CreateRelationshipRequest(BaseModel):
    """Request model for creating a relationship."""

    slug: str = Field(default="", description="URL-safe identifier (auto-generated if empty)")
    source_type: str = Field(description="Type of source element")
    source_slug: str = Field(description="Slug of source element")
    destination_type: str = Field(description="Type of destination element")
    destination_slug: str = Field(description="Slug of destination element")
    description: str = Field(default="Uses", description="Relationship description")
    technology: str = Field(default="", description="Protocol/technology used")
    bidirectional: bool = Field(default=False, description="Whether relationship goes both ways")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    def to_domain_model(self) -> Relationship:
        """Convert to Relationship."""
        slug = self.slug
        if not slug:
            slug = f"{self.source_slug}-to-{self.destination_slug}"
        return Relationship(
            slug=slug,
            source_type=ElementType(self.source_type),
            source_slug=self.source_slug,
            destination_type=ElementType(self.destination_type),
            destination_slug=self.destination_slug,
            description=self.description,
            technology=self.technology,
            bidirectional=self.bidirectional,
            tags=self.tags,
            docname="",
        )


class GetRelationshipRequest(BaseModel):
    """Request for getting a relationship by slug."""

    slug: str


class ListRelationshipsRequest(BaseModel):
    """Request for listing relationships."""

    pass


class UpdateRelationshipRequest(BaseModel):
    """Request for updating a relationship."""

    slug: str
    description: str | None = None
    technology: str | None = None
    bidirectional: bool | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: Relationship) -> Relationship:
        """Apply non-None fields to existing relationship."""
        updates: dict[str, Any] = {}
        if self.description is not None:
            updates["description"] = self.description
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.bidirectional is not None:
            updates["bidirectional"] = self.bidirectional
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class DeleteRelationshipRequest(BaseModel):
    """Request for deleting a relationship by slug."""

    slug: str


# =============================================================================
# DeploymentNode DTOs
# =============================================================================


class ContainerInstanceInput(BaseModel):
    """Input model for container instance."""

    container_slug: str = Field(description="Slug of deployed container")
    instance_id: str = Field(default="", description="Instance identifier")
    properties: dict[str, str] = Field(default_factory=dict, description="Instance properties")

    def to_domain_model(self) -> ContainerInstance:
        """Convert to ContainerInstance."""
        return ContainerInstance(
            container_slug=self.container_slug,
            instance_id=self.instance_id,
            properties=self.properties,
        )


class CreateDeploymentNodeRequest(BaseModel):
    """Request model for creating a deployment node."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    environment: str = Field(default="production", description="Deployment environment")
    node_type: str = Field(default="other", description="Type of infrastructure node")
    technology: str = Field(default="", description="Infrastructure technology")
    description: str = Field(default="", description="Human-readable description")
    parent_slug: str | None = Field(default=None, description="Parent node for nesting")
    container_instances: list[ContainerInstanceInput] = Field(
        default_factory=list, description="Containers deployed to this node"
    )
    properties: dict[str, str] = Field(default_factory=dict, description="Node properties")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    def to_domain_model(self) -> DeploymentNode:
        """Convert to DeploymentNode."""
        return DeploymentNode(
            slug=self.slug,
            name=self.name,
            environment=self.environment,
            node_type=NodeType(self.node_type),
            technology=self.technology,
            description=self.description,
            parent_slug=self.parent_slug,
            container_instances=[ci.to_domain_model() for ci in self.container_instances],
            properties=self.properties,
            tags=self.tags,
            docname="",
        )


class GetDeploymentNodeRequest(BaseModel):
    """Request for getting a deployment node by slug."""

    slug: str


class ListDeploymentNodesRequest(BaseModel):
    """Request for listing deployment nodes."""

    pass


class UpdateDeploymentNodeRequest(BaseModel):
    """Request for updating a deployment node."""

    slug: str
    name: str | None = None
    environment: str | None = None
    node_type: str | None = None
    technology: str | None = None
    description: str | None = None
    parent_slug: str | None = None
    container_instances: list[ContainerInstanceInput] | None = None
    properties: dict[str, str] | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: DeploymentNode) -> DeploymentNode:
        """Apply non-None fields to existing deployment node."""
        updates: dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name
        if self.environment is not None:
            updates["environment"] = self.environment
        if self.node_type is not None:
            updates["node_type"] = NodeType(self.node_type)
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.description is not None:
            updates["description"] = self.description
        if self.parent_slug is not None:
            updates["parent_slug"] = self.parent_slug
        if self.container_instances is not None:
            updates["container_instances"] = [ci.to_domain_model() for ci in self.container_instances]
        if self.properties is not None:
            updates["properties"] = self.properties
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class DeleteDeploymentNodeRequest(BaseModel):
    """Request for deleting a deployment node by slug."""

    slug: str


# =============================================================================
# DynamicStep DTOs
# =============================================================================


class CreateDynamicStepRequest(BaseModel):
    """Request model for creating a dynamic step."""

    slug: str = Field(default="", description="URL-safe identifier (auto-generated if empty)")
    sequence_name: str = Field(description="Name of the dynamic sequence")
    step_number: int = Field(description="Order within sequence (1-based)")
    source_type: str = Field(description="Type of source element")
    source_slug: str = Field(description="Slug of source element")
    destination_type: str = Field(description="Type of destination element")
    destination_slug: str = Field(description="Slug of destination element")
    description: str = Field(default="", description="Step description")
    technology: str = Field(default="", description="Protocol/technology used")
    return_description: str = Field(default="", description="Return value description")
    is_return: bool = Field(default=False, description="Whether this is a return step")

    def to_domain_model(self) -> DynamicStep:
        """Convert to DynamicStep."""
        slug = self.slug
        if not slug:
            slug = f"{self.sequence_name}-step-{self.step_number}"
        return DynamicStep(
            slug=slug,
            sequence_name=self.sequence_name,
            step_number=self.step_number,
            source_type=ElementType(self.source_type),
            source_slug=self.source_slug,
            destination_type=ElementType(self.destination_type),
            destination_slug=self.destination_slug,
            description=self.description,
            technology=self.technology,
            return_description=self.return_description,
            is_return=self.is_return,
            docname="",
        )


class GetDynamicStepRequest(BaseModel):
    """Request for getting a dynamic step by slug."""

    slug: str


class ListDynamicStepsRequest(BaseModel):
    """Request for listing dynamic steps."""

    pass


class UpdateDynamicStepRequest(BaseModel):
    """Request for updating a dynamic step."""

    slug: str
    step_number: int | None = None
    description: str | None = None
    technology: str | None = None
    return_description: str | None = None
    is_return: bool | None = None

    def apply_to(self, existing: DynamicStep) -> DynamicStep:
        """Apply non-None fields to existing dynamic step."""
        updates: dict[str, Any] = {}
        if self.step_number is not None:
            updates["step_number"] = self.step_number
        if self.description is not None:
            updates["description"] = self.description
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.return_description is not None:
            updates["return_description"] = self.return_description
        if self.is_return is not None:
            updates["is_return"] = self.is_return
        return existing.model_copy(update=updates) if updates else existing


class DeleteDynamicStepRequest(BaseModel):
    """Request for deleting a dynamic step by slug."""

    slug: str


# =============================================================================
# Diagram Request DTOs
# =============================================================================


class GetSystemContextDiagramRequest(BaseModel):
    """Request for generating a system context diagram."""

    system_slug: str = Field(description="Software system to show context for")
    format: str = Field(default="plantuml", description="Output format: plantuml, structurizr, data")


class GetContainerDiagramRequest(BaseModel):
    """Request for generating a container diagram."""

    system_slug: str = Field(description="Software system to show containers for")
    format: str = Field(default="plantuml", description="Output format: plantuml, structurizr, data")


class GetComponentDiagramRequest(BaseModel):
    """Request for generating a component diagram."""

    container_slug: str = Field(description="Container to show components for")
    format: str = Field(default="plantuml", description="Output format: plantuml, structurizr, data")


class GetSystemLandscapeDiagramRequest(BaseModel):
    """Request for generating a system landscape diagram."""

    format: str = Field(default="plantuml", description="Output format: plantuml, structurizr, data")


class GetDeploymentDiagramRequest(BaseModel):
    """Request for generating a deployment diagram."""

    environment: str = Field(description="Deployment environment to show")
    format: str = Field(default="plantuml", description="Output format: plantuml, structurizr, data")


class GetDynamicDiagramRequest(BaseModel):
    """Request for generating a dynamic diagram."""

    sequence_name: str = Field(description="Dynamic sequence to show")
    format: str = Field(default="plantuml", description="Output format: plantuml, structurizr, data")

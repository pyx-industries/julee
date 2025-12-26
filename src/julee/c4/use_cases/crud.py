"""CRUD use cases for C4 entities.

Generic CRUD operations using base classes from julee.core.use_cases.generic_crud.
Entity-specific Create/Update logic (validators, enum conversions) kept explicit.
"""

from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator

from julee.c4.entities.component import Component
from julee.c4.entities.container import Container, ContainerType
from julee.c4.entities.deployment_node import DeploymentNode, NodeType
from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import Relationship
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

    @computed_field
    @property
    def software_system(self) -> SoftwareSystem | None:
        """Backward-compatible alias for entity."""
        return self.entity


class GetSoftwareSystemUseCase(
    generic_crud.GetUseCase[SoftwareSystem, SoftwareSystemRepository]
):
    """Get a software system by slug."""

    response_cls = GetSoftwareSystemResponse


class ListSoftwareSystemsRequest(generic_crud.ListRequest):
    """List all software systems."""


class ListSoftwareSystemsResponse(generic_crud.ListResponse[SoftwareSystem]):
    """Software systems list response."""

    @computed_field
    @property
    def software_systems(self) -> list[SoftwareSystem]:
        """Backward-compatible alias for entities."""
        return self.entities


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
    """Request for creating a software system."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    system_type: str = Field(
        default="internal", description="Type: internal, external, existing"
    )
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


class CreateSoftwareSystemResponse(generic_crud.CreateResponse[SoftwareSystem]):
    """Software system create response."""

    @computed_field
    @property
    def software_system(self) -> SoftwareSystem:
        """Backward-compatible alias for entity."""
        return self.entity


class CreateSoftwareSystemUseCase:
    """Create a software system."""

    def __init__(self, repo: SoftwareSystemRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: CreateSoftwareSystemRequest
    ) -> CreateSoftwareSystemResponse:
        entity = SoftwareSystem(
            slug=request.slug,
            name=request.name,
            description=request.description,
            system_type=SystemType(request.system_type),
            owner=request.owner,
            technology=request.technology,
            url=request.url,
            tags=request.tags,
            docname="",
        )
        await self.repo.save(entity)
        return CreateSoftwareSystemResponse(entity=entity)


class UpdateSoftwareSystemRequest(generic_crud.UpdateRequest):
    """Update software system fields."""

    name: str | None = None
    description: str | None = None
    system_type: str | None = None
    owner: str | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None


class UpdateSoftwareSystemResponse(generic_crud.UpdateResponse[SoftwareSystem]):
    """Software system update response."""

    @computed_field
    @property
    def software_system(self) -> SoftwareSystem | None:
        """Backward-compatible alias for entity."""
        return self.entity


class UpdateSoftwareSystemUseCase:
    """Update a software system."""

    def __init__(self, repo: SoftwareSystemRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: UpdateSoftwareSystemRequest
    ) -> UpdateSoftwareSystemResponse:
        existing = await self.repo.get(request.slug)
        if not existing:
            return UpdateSoftwareSystemResponse(entity=None)

        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.system_type is not None:
            updates["system_type"] = SystemType(request.system_type)
        if request.owner is not None:
            updates["owner"] = request.owner
        if request.technology is not None:
            updates["technology"] = request.technology
        if request.url is not None:
            updates["url"] = request.url
        if request.tags is not None:
            updates["tags"] = request.tags

        updated = existing.model_copy(update=updates) if updates else existing
        await self.repo.save(updated)
        return UpdateSoftwareSystemResponse(entity=updated)


# =============================================================================
# Container
# =============================================================================


class GetContainerRequest(generic_crud.GetRequest):
    """Get container by slug."""


class GetContainerResponse(generic_crud.GetResponse[Container]):
    """Container get response."""

    @computed_field
    @property
    def container(self) -> Container | None:
        """Backward-compatible alias for entity."""
        return self.entity


class GetContainerUseCase(generic_crud.GetUseCase[Container, ContainerRepository]):
    """Get a container by slug."""

    response_cls = GetContainerResponse


class ListContainersRequest(generic_crud.ListRequest):
    """List all containers."""


class ListContainersResponse(generic_crud.ListResponse[Container]):
    """Containers list response."""

    @computed_field
    @property
    def containers(self) -> list[Container]:
        """Backward-compatible alias for entities."""
        return self.entities


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
    """Request for creating a container."""

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


class CreateContainerResponse(generic_crud.CreateResponse[Container]):
    """Container create response."""

    @computed_field
    @property
    def container(self) -> Container:
        """Backward-compatible alias for entity."""
        return self.entity


class CreateContainerUseCase:
    """Create a container."""

    def __init__(self, repo: ContainerRepository) -> None:
        self.repo = repo

    async def execute(self, request: CreateContainerRequest) -> CreateContainerResponse:
        entity = Container(
            slug=request.slug,
            name=request.name,
            system_slug=request.system_slug,
            description=request.description,
            container_type=ContainerType(request.container_type),
            technology=request.technology,
            url=request.url,
            tags=request.tags,
            docname="",
        )
        await self.repo.save(entity)
        return CreateContainerResponse(entity=entity)


class UpdateContainerRequest(generic_crud.UpdateRequest):
    """Update container fields."""

    name: str | None = None
    system_slug: str | None = None
    description: str | None = None
    container_type: str | None = None
    technology: str | None = None
    url: str | None = None
    tags: list[str] | None = None


class UpdateContainerResponse(generic_crud.UpdateResponse[Container]):
    """Container update response."""

    @computed_field
    @property
    def container(self) -> Container | None:
        """Backward-compatible alias for entity."""
        return self.entity


class UpdateContainerUseCase:
    """Update a container."""

    def __init__(self, repo: ContainerRepository) -> None:
        self.repo = repo

    async def execute(self, request: UpdateContainerRequest) -> UpdateContainerResponse:
        existing = await self.repo.get(request.slug)
        if not existing:
            return UpdateContainerResponse(entity=None)

        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.system_slug is not None:
            updates["system_slug"] = request.system_slug
        if request.description is not None:
            updates["description"] = request.description
        if request.container_type is not None:
            updates["container_type"] = ContainerType(request.container_type)
        if request.technology is not None:
            updates["technology"] = request.technology
        if request.url is not None:
            updates["url"] = request.url
        if request.tags is not None:
            updates["tags"] = request.tags

        updated = existing.model_copy(update=updates) if updates else existing
        await self.repo.save(updated)
        return UpdateContainerResponse(entity=updated)


# =============================================================================
# Component
# =============================================================================


class GetComponentRequest(generic_crud.GetRequest):
    """Get component by slug."""


class GetComponentResponse(generic_crud.GetResponse[Component]):
    """Component get response."""

    @computed_field
    @property
    def component(self) -> Component | None:
        """Backward-compatible alias for entity."""
        return self.entity


class GetComponentUseCase(generic_crud.GetUseCase[Component, ComponentRepository]):
    """Get a component by slug."""

    response_cls = GetComponentResponse


class ListComponentsRequest(generic_crud.ListRequest):
    """List all components."""


class ListComponentsResponse(generic_crud.ListResponse[Component]):
    """Components list response."""

    @computed_field
    @property
    def components(self) -> list[Component]:
        """Backward-compatible alias for entities."""
        return self.entities


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
    """Request for creating a component."""

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

    @field_validator("container_slug")
    @classmethod
    def validate_container_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("container_slug cannot be empty")
        return v.strip()

    @field_validator("system_slug")
    @classmethod
    def validate_system_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("system_slug cannot be empty")
        return v.strip()


class CreateComponentResponse(generic_crud.CreateResponse[Component]):
    """Component create response."""

    @computed_field
    @property
    def component(self) -> Component:
        """Backward-compatible alias for entity."""
        return self.entity


class CreateComponentUseCase:
    """Create a component."""

    def __init__(self, repo: ComponentRepository) -> None:
        self.repo = repo

    async def execute(self, request: CreateComponentRequest) -> CreateComponentResponse:
        entity = Component(
            slug=request.slug,
            name=request.name,
            container_slug=request.container_slug,
            system_slug=request.system_slug,
            description=request.description,
            technology=request.technology,
            interface=request.interface,
            code_path=request.code_path,
            url=request.url,
            tags=request.tags,
            docname="",
        )
        await self.repo.save(entity)
        return CreateComponentResponse(entity=entity)


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

    @computed_field
    @property
    def component(self) -> Component | None:
        """Backward-compatible alias for entity."""
        return self.entity


class UpdateComponentUseCase:
    """Update a component."""

    def __init__(self, repo: ComponentRepository) -> None:
        self.repo = repo

    async def execute(self, request: UpdateComponentRequest) -> UpdateComponentResponse:
        existing = await self.repo.get(request.slug)
        if not existing:
            return UpdateComponentResponse(entity=None)

        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.container_slug is not None:
            updates["container_slug"] = request.container_slug
        if request.system_slug is not None:
            updates["system_slug"] = request.system_slug
        if request.description is not None:
            updates["description"] = request.description
        if request.technology is not None:
            updates["technology"] = request.technology
        if request.interface is not None:
            updates["interface"] = request.interface
        if request.code_path is not None:
            updates["code_path"] = request.code_path
        if request.url is not None:
            updates["url"] = request.url
        if request.tags is not None:
            updates["tags"] = request.tags

        updated = existing.model_copy(update=updates) if updates else existing
        await self.repo.save(updated)
        return UpdateComponentResponse(entity=updated)


# =============================================================================
# Relationship
# =============================================================================


class GetRelationshipRequest(generic_crud.GetRequest):
    """Get relationship by slug."""


class GetRelationshipResponse(generic_crud.GetResponse[Relationship]):
    """Relationship get response."""

    @computed_field
    @property
    def relationship(self) -> Relationship | None:
        """Backward-compatible alias for entity."""
        return self.entity


class GetRelationshipUseCase(
    generic_crud.GetUseCase[Relationship, RelationshipRepository]
):
    """Get a relationship by slug."""

    response_cls = GetRelationshipResponse


class ListRelationshipsRequest(generic_crud.ListRequest):
    """List all relationships."""


class ListRelationshipsResponse(generic_crud.ListResponse[Relationship]):
    """Relationships list response."""

    @computed_field
    @property
    def relationships(self) -> list[Relationship]:
        """Backward-compatible alias for entities."""
        return self.entities


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
    """Request for creating a relationship."""

    source_type: str = Field(description="Type of source element")
    source_slug: str = Field(description="Slug of source element")
    destination_type: str = Field(description="Type of destination element")
    destination_slug: str = Field(description="Slug of destination element")
    slug: str = Field(default="", description="Optional identifier")
    description: str = Field(default="Uses", description="Relationship description")
    technology: str = Field(default="", description="Protocol/technology used")
    bidirectional: bool = Field(default=False, description="Bidirectional relationship")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_type cannot be empty")
        return v.strip()

    @field_validator("source_slug")
    @classmethod
    def validate_source_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_slug cannot be empty")
        return v.strip()

    @field_validator("destination_type")
    @classmethod
    def validate_destination_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("destination_type cannot be empty")
        return v.strip()

    @field_validator("destination_slug")
    @classmethod
    def validate_destination_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("destination_slug cannot be empty")
        return v.strip()


class CreateRelationshipResponse(generic_crud.CreateResponse[Relationship]):
    """Relationship create response."""

    @computed_field
    @property
    def relationship(self) -> Relationship:
        """Backward-compatible alias for entity."""
        return self.entity


class CreateRelationshipUseCase:
    """Create a relationship."""

    def __init__(self, repo: RelationshipRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: CreateRelationshipRequest
    ) -> CreateRelationshipResponse:
        # Auto-generate slug if not provided
        slug = request.slug or f"{request.source_slug}-to-{request.destination_slug}"
        entity = Relationship(
            slug=slug,
            source_type=request.source_type,
            source_slug=request.source_slug,
            destination_type=request.destination_type,
            destination_slug=request.destination_slug,
            description=request.description,
            technology=request.technology,
            bidirectional=request.bidirectional,
            tags=request.tags,
            docname="",
        )
        await self.repo.save(entity)
        return CreateRelationshipResponse(entity=entity)


class UpdateRelationshipRequest(generic_crud.UpdateRequest):
    """Update relationship fields."""

    description: str | None = None
    technology: str | None = None
    bidirectional: bool | None = None
    tags: list[str] | None = None


class UpdateRelationshipResponse(generic_crud.UpdateResponse[Relationship]):
    """Relationship update response."""

    @computed_field
    @property
    def relationship(self) -> Relationship | None:
        """Backward-compatible alias for entity."""
        return self.entity


class UpdateRelationshipUseCase:
    """Update a relationship."""

    def __init__(self, repo: RelationshipRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: UpdateRelationshipRequest
    ) -> UpdateRelationshipResponse:
        existing = await self.repo.get(request.slug)
        if not existing:
            return UpdateRelationshipResponse(entity=None)

        updates: dict[str, Any] = {}
        if request.description is not None:
            updates["description"] = request.description
        if request.technology is not None:
            updates["technology"] = request.technology
        if request.bidirectional is not None:
            updates["bidirectional"] = request.bidirectional
        if request.tags is not None:
            updates["tags"] = request.tags

        updated = existing.model_copy(update=updates) if updates else existing
        await self.repo.save(updated)
        return UpdateRelationshipResponse(entity=updated)


# =============================================================================
# DeploymentNode
# =============================================================================


class GetDeploymentNodeRequest(generic_crud.GetRequest):
    """Get deployment node by slug."""


class GetDeploymentNodeResponse(generic_crud.GetResponse[DeploymentNode]):
    """Deployment node get response."""

    @computed_field
    @property
    def deployment_node(self) -> DeploymentNode | None:
        """Backward-compatible alias for entity."""
        return self.entity


class GetDeploymentNodeUseCase(
    generic_crud.GetUseCase[DeploymentNode, DeploymentNodeRepository]
):
    """Get a deployment node by slug."""

    response_cls = GetDeploymentNodeResponse


class ListDeploymentNodesRequest(generic_crud.ListRequest):
    """List all deployment nodes."""


class ListDeploymentNodesResponse(generic_crud.ListResponse[DeploymentNode]):
    """Deployment nodes list response."""

    @computed_field
    @property
    def deployment_nodes(self) -> list[DeploymentNode]:
        """Backward-compatible alias for entities."""
        return self.entities


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
    """Request for creating a deployment node."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    environment: str = Field(default="production", description="Deployment environment")
    node_type: str = Field(default="other", description="Infrastructure type")
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


class CreateDeploymentNodeResponse(generic_crud.CreateResponse[DeploymentNode]):
    """Deployment node create response."""

    @computed_field
    @property
    def deployment_node(self) -> DeploymentNode:
        """Backward-compatible alias for entity."""
        return self.entity


class CreateDeploymentNodeUseCase:
    """Create a deployment node."""

    def __init__(self, repo: DeploymentNodeRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: CreateDeploymentNodeRequest
    ) -> CreateDeploymentNodeResponse:
        entity = DeploymentNode(
            slug=request.slug,
            name=request.name,
            environment=request.environment,
            node_type=NodeType(request.node_type),
            technology=request.technology,
            description=request.description,
            parent_slug=request.parent_slug,
            container_instances=request.container_instances,
            properties=request.properties,
            tags=request.tags,
            docname="",
        )
        await self.repo.save(entity)
        return CreateDeploymentNodeResponse(entity=entity)


class UpdateDeploymentNodeRequest(generic_crud.UpdateRequest):
    """Update deployment node fields."""

    name: str | None = None
    environment: str | None = None
    node_type: str | None = None
    technology: str | None = None
    description: str | None = None
    parent_slug: str | None = None
    container_instances: list[dict[str, Any]] | None = None
    properties: dict[str, str] | None = None
    tags: list[str] | None = None


class UpdateDeploymentNodeResponse(generic_crud.UpdateResponse[DeploymentNode]):
    """Deployment node update response."""

    @computed_field
    @property
    def deployment_node(self) -> DeploymentNode | None:
        """Backward-compatible alias for entity."""
        return self.entity


class UpdateDeploymentNodeUseCase:
    """Update a deployment node."""

    def __init__(self, repo: DeploymentNodeRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: UpdateDeploymentNodeRequest
    ) -> UpdateDeploymentNodeResponse:
        existing = await self.repo.get(request.slug)
        if not existing:
            return UpdateDeploymentNodeResponse(entity=None)

        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.environment is not None:
            updates["environment"] = request.environment
        if request.node_type is not None:
            updates["node_type"] = NodeType(request.node_type)
        if request.technology is not None:
            updates["technology"] = request.technology
        if request.description is not None:
            updates["description"] = request.description
        if request.parent_slug is not None:
            updates["parent_slug"] = request.parent_slug
        if request.container_instances is not None:
            updates["container_instances"] = request.container_instances
        if request.properties is not None:
            updates["properties"] = request.properties
        if request.tags is not None:
            updates["tags"] = request.tags

        updated = existing.model_copy(update=updates) if updates else existing
        await self.repo.save(updated)
        return UpdateDeploymentNodeResponse(entity=updated)


# =============================================================================
# DynamicStep
# =============================================================================


class GetDynamicStepRequest(generic_crud.GetRequest):
    """Get dynamic step by slug."""


class GetDynamicStepResponse(generic_crud.GetResponse[DynamicStep]):
    """Dynamic step get response."""

    @computed_field
    @property
    def dynamic_step(self) -> DynamicStep | None:
        """Backward-compatible alias for entity."""
        return self.entity


class GetDynamicStepUseCase(
    generic_crud.GetUseCase[DynamicStep, DynamicStepRepository]
):
    """Get a dynamic step by slug."""

    response_cls = GetDynamicStepResponse


class ListDynamicStepsRequest(generic_crud.ListRequest):
    """List all dynamic steps."""


class ListDynamicStepsResponse(generic_crud.ListResponse[DynamicStep]):
    """Dynamic steps list response."""

    @computed_field
    @property
    def dynamic_steps(self) -> list[DynamicStep]:
        """Backward-compatible alias for entities."""
        return self.entities


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
    """Request for creating a dynamic step."""

    sequence_name: str = Field(description="Name of the dynamic sequence")
    step_number: int = Field(description="Order within sequence")
    source_type: str = Field(description="Type of calling element")
    source_slug: str = Field(description="Slug of calling element")
    destination_type: str = Field(description="Type of called element")
    destination_slug: str = Field(description="Slug of called element")
    slug: str = Field(default="", description="Optional identifier")
    description: str = Field(default="", description="Step description")
    technology: str = Field(default="", description="Protocol/technology")
    return_description: str = Field(default="", description="Return value description")
    is_return: bool = Field(default=False, description="Is this a return step")

    @field_validator("sequence_name")
    @classmethod
    def validate_sequence_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sequence_name cannot be empty")
        return v.strip()

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_type cannot be empty")
        return v.strip()

    @field_validator("source_slug")
    @classmethod
    def validate_source_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_slug cannot be empty")
        return v.strip()

    @field_validator("destination_type")
    @classmethod
    def validate_destination_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("destination_type cannot be empty")
        return v.strip()

    @field_validator("destination_slug")
    @classmethod
    def validate_destination_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("destination_slug cannot be empty")
        return v.strip()


class CreateDynamicStepResponse(generic_crud.CreateResponse[DynamicStep]):
    """Dynamic step create response."""

    @computed_field
    @property
    def dynamic_step(self) -> DynamicStep:
        """Backward-compatible alias for entity."""
        return self.entity


class CreateDynamicStepUseCase:
    """Create a dynamic step."""

    def __init__(self, repo: DynamicStepRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: CreateDynamicStepRequest
    ) -> CreateDynamicStepResponse:
        # Auto-generate slug if not provided
        slug = request.slug or f"{request.sequence_name}-step-{request.step_number}"
        entity = DynamicStep(
            slug=slug,
            sequence_name=request.sequence_name,
            step_number=request.step_number,
            source_type=request.source_type,
            source_slug=request.source_slug,
            destination_type=request.destination_type,
            destination_slug=request.destination_slug,
            description=request.description,
            technology=request.technology,
            return_description=request.return_description,
            is_return=request.is_return,
            docname="",
        )
        await self.repo.save(entity)
        return CreateDynamicStepResponse(entity=entity)


class UpdateDynamicStepRequest(generic_crud.UpdateRequest):
    """Update dynamic step fields."""

    step_number: int | None = None
    description: str | None = None
    technology: str | None = None
    return_description: str | None = None
    is_return: bool | None = None


class UpdateDynamicStepResponse(generic_crud.UpdateResponse[DynamicStep]):
    """Dynamic step update response."""

    @computed_field
    @property
    def dynamic_step(self) -> DynamicStep | None:
        """Backward-compatible alias for entity."""
        return self.entity


class UpdateDynamicStepUseCase:
    """Update a dynamic step."""

    def __init__(self, repo: DynamicStepRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: UpdateDynamicStepRequest
    ) -> UpdateDynamicStepResponse:
        existing = await self.repo.get(request.slug)
        if not existing:
            return UpdateDynamicStepResponse(entity=None)

        updates: dict[str, Any] = {}
        if request.step_number is not None:
            updates["step_number"] = request.step_number
        if request.description is not None:
            updates["description"] = request.description
        if request.technology is not None:
            updates["technology"] = request.technology
        if request.return_description is not None:
            updates["return_description"] = request.return_description
        if request.is_return is not None:
            updates["is_return"] = request.is_return

        updated = existing.model_copy(update=updates) if updates else existing
        await self.repo.save(updated)
        return UpdateDynamicStepResponse(entity=updated)

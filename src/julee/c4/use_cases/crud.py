"""CRUD use cases for C4 entities.

Uses generic_crud.generate() for standard CRUD operations.
Custom Create/Update requests with enum validators are defined manually.
"""

from typing import Any

from pydantic import field_validator

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
# SoftwareSystem - with enum validators
# =============================================================================

generic_crud.generate(SoftwareSystem, SoftwareSystemRepository)


class CreateSoftwareSystemRequest(CreateSoftwareSystemRequest):  # type: ignore[no-redef]  # noqa: F821
    """Create software system with enum coercion."""

    @field_validator("system_type", mode="before")
    @classmethod
    def coerce_system_type(cls, v: Any) -> SystemType:
        if isinstance(v, str):
            return SystemType(v)
        return v


class UpdateSoftwareSystemRequest(UpdateSoftwareSystemRequest):  # type: ignore[no-redef]  # noqa: F821
    """Update software system with enum coercion."""

    @field_validator("system_type", mode="before")
    @classmethod
    def coerce_system_type(cls, v: Any) -> SystemType | None:
        if v is None:
            return None
        if isinstance(v, str):
            return SystemType(v)
        return v


# =============================================================================
# Container - with enum validators
# =============================================================================

generic_crud.generate(Container, ContainerRepository)


class CreateContainerRequest(CreateContainerRequest):  # type: ignore[no-redef]  # noqa: F821
    """Create container with enum coercion."""

    @field_validator("container_type", mode="before")
    @classmethod
    def coerce_container_type(cls, v: Any) -> ContainerType:
        if isinstance(v, str):
            return ContainerType(v)
        return v


class UpdateContainerRequest(UpdateContainerRequest):  # type: ignore[no-redef]  # noqa: F821
    """Update container with enum coercion."""

    @field_validator("container_type", mode="before")
    @classmethod
    def coerce_container_type(cls, v: Any) -> ContainerType | None:
        if v is None:
            return None
        if isinstance(v, str):
            return ContainerType(v)
        return v


# =============================================================================
# Component - no enums, simple CRUD
# =============================================================================

generic_crud.generate(Component, ComponentRepository)


# =============================================================================
# Relationship - with enum validators
# =============================================================================

generic_crud.generate(Relationship, RelationshipRepository)


class CreateRelationshipRequest(CreateRelationshipRequest):  # type: ignore[no-redef]  # noqa: F821
    """Create relationship with enum coercion."""

    @field_validator("source_type", mode="before")
    @classmethod
    def coerce_source_type(cls, v: Any) -> ElementType:
        if isinstance(v, str):
            return ElementType(v)
        return v

    @field_validator("destination_type", mode="before")
    @classmethod
    def coerce_destination_type(cls, v: Any) -> ElementType:
        if isinstance(v, str):
            return ElementType(v)
        return v


# UpdateRelationshipRequest doesn't have enum fields to coerce


# =============================================================================
# DeploymentNode - with enum validators
# =============================================================================

generic_crud.generate(DeploymentNode, DeploymentNodeRepository)


class CreateDeploymentNodeRequest(CreateDeploymentNodeRequest):  # type: ignore[no-redef]  # noqa: F821
    """Create deployment node with enum coercion."""

    @field_validator("node_type", mode="before")
    @classmethod
    def coerce_node_type(cls, v: Any) -> NodeType:
        if isinstance(v, str):
            return NodeType(v)
        return v


class UpdateDeploymentNodeRequest(UpdateDeploymentNodeRequest):  # type: ignore[no-redef]  # noqa: F821
    """Update deployment node with enum coercion."""

    @field_validator("node_type", mode="before")
    @classmethod
    def coerce_node_type(cls, v: Any) -> NodeType | None:
        if v is None:
            return None
        if isinstance(v, str):
            return NodeType(v)
        return v


# =============================================================================
# DynamicStep - with enum validators
# =============================================================================

generic_crud.generate(DynamicStep, DynamicStepRepository)


class CreateDynamicStepRequest(CreateDynamicStepRequest):  # type: ignore[no-redef]  # noqa: F821
    """Create dynamic step with enum coercion."""

    @field_validator("source_type", mode="before")
    @classmethod
    def coerce_source_type(cls, v: Any) -> ElementType:
        if isinstance(v, str):
            return ElementType(v)
        return v

    @field_validator("destination_type", mode="before")
    @classmethod
    def coerce_destination_type(cls, v: Any) -> ElementType:
        if isinstance(v, str):
            return ElementType(v)
        return v


# UpdateDynamicStepRequest doesn't have enum fields to coerce

"""Repository and use-case context for C4 MCP tools.

Provides repository instances and use-case factories for MCP tool functions.
"""

import os
from functools import lru_cache
from pathlib import Path

from julee.c4.use_cases.component import (
    CreateComponentUseCase,
    DeleteComponentUseCase,
    GetComponentUseCase,
    ListComponentsUseCase,
    UpdateComponentUseCase,
)
from julee.c4.use_cases.container import (
    CreateContainerUseCase,
    DeleteContainerUseCase,
    GetContainerUseCase,
    ListContainersUseCase,
    UpdateContainerUseCase,
)
from julee.c4.use_cases.deployment_node import (
    CreateDeploymentNodeUseCase,
    DeleteDeploymentNodeUseCase,
    GetDeploymentNodeUseCase,
    ListDeploymentNodesUseCase,
    UpdateDeploymentNodeUseCase,
)
from julee.c4.use_cases.diagrams import (
    GetComponentDiagramUseCase,
    GetContainerDiagramUseCase,
    GetDeploymentDiagramUseCase,
    GetDynamicDiagramUseCase,
    GetSystemContextDiagramUseCase,
    GetSystemLandscapeDiagramUseCase,
)
from julee.c4.use_cases.dynamic_step import (
    CreateDynamicStepUseCase,
    DeleteDynamicStepUseCase,
    GetDynamicStepUseCase,
    ListDynamicStepsUseCase,
    UpdateDynamicStepUseCase,
)
from julee.c4.use_cases.relationship import (
    CreateRelationshipUseCase,
    DeleteRelationshipUseCase,
    GetRelationshipUseCase,
    ListRelationshipsUseCase,
    UpdateRelationshipUseCase,
)
from julee.c4.use_cases.software_system import (
    CreateSoftwareSystemUseCase,
    DeleteSoftwareSystemUseCase,
    GetSoftwareSystemUseCase,
    ListSoftwareSystemsUseCase,
    UpdateSoftwareSystemUseCase,
)
from julee.c4.infrastructure.repositories.file import (
    FileComponentRepository,
    FileContainerRepository,
    FileDeploymentNodeRepository,
    FileDynamicStepRepository,
    FileRelationshipRepository,
    FileSoftwareSystemRepository,
)


def get_c4_root() -> Path:
    """Get the C4 data root directory from environment.

    Returns:
        Path to the C4 data root directory
    """
    return Path(os.getenv("C4_DATA_ROOT", "c4"))


# =============================================================================
# Repository Factories
# =============================================================================


@lru_cache
def get_software_system_repository() -> FileSoftwareSystemRepository:
    """Get the software system repository singleton."""
    c4_root = get_c4_root()
    return FileSoftwareSystemRepository(c4_root / "systems")


@lru_cache
def get_container_repository() -> FileContainerRepository:
    """Get the container repository singleton."""
    c4_root = get_c4_root()
    return FileContainerRepository(c4_root / "containers")


@lru_cache
def get_component_repository() -> FileComponentRepository:
    """Get the component repository singleton."""
    c4_root = get_c4_root()
    return FileComponentRepository(c4_root / "components")


@lru_cache
def get_relationship_repository() -> FileRelationshipRepository:
    """Get the relationship repository singleton."""
    c4_root = get_c4_root()
    return FileRelationshipRepository(c4_root / "relationships")


@lru_cache
def get_deployment_node_repository() -> FileDeploymentNodeRepository:
    """Get the deployment node repository singleton."""
    c4_root = get_c4_root()
    return FileDeploymentNodeRepository(c4_root / "deployment")


@lru_cache
def get_dynamic_step_repository() -> FileDynamicStepRepository:
    """Get the dynamic step repository singleton."""
    c4_root = get_c4_root()
    return FileDynamicStepRepository(c4_root / "dynamic")


# =============================================================================
# SoftwareSystem Use-Case Factories
# =============================================================================


def get_create_software_system_use_case() -> CreateSoftwareSystemUseCase:
    """Get CreateSoftwareSystemUseCase with repository dependency."""
    return CreateSoftwareSystemUseCase(get_software_system_repository())


def get_get_software_system_use_case() -> GetSoftwareSystemUseCase:
    """Get GetSoftwareSystemUseCase with repository dependency."""
    return GetSoftwareSystemUseCase(get_software_system_repository())


def get_list_software_systems_use_case() -> ListSoftwareSystemsUseCase:
    """Get ListSoftwareSystemsUseCase with repository dependency."""
    return ListSoftwareSystemsUseCase(get_software_system_repository())


def get_update_software_system_use_case() -> UpdateSoftwareSystemUseCase:
    """Get UpdateSoftwareSystemUseCase with repository dependency."""
    return UpdateSoftwareSystemUseCase(get_software_system_repository())


def get_delete_software_system_use_case() -> DeleteSoftwareSystemUseCase:
    """Get DeleteSoftwareSystemUseCase with repository dependency."""
    return DeleteSoftwareSystemUseCase(get_software_system_repository())


# =============================================================================
# Container Use-Case Factories
# =============================================================================


def get_create_container_use_case() -> CreateContainerUseCase:
    """Get CreateContainerUseCase with repository dependency."""
    return CreateContainerUseCase(get_container_repository())


def get_get_container_use_case() -> GetContainerUseCase:
    """Get GetContainerUseCase with repository dependency."""
    return GetContainerUseCase(get_container_repository())


def get_list_containers_use_case() -> ListContainersUseCase:
    """Get ListContainersUseCase with repository dependency."""
    return ListContainersUseCase(get_container_repository())


def get_update_container_use_case() -> UpdateContainerUseCase:
    """Get UpdateContainerUseCase with repository dependency."""
    return UpdateContainerUseCase(get_container_repository())


def get_delete_container_use_case() -> DeleteContainerUseCase:
    """Get DeleteContainerUseCase with repository dependency."""
    return DeleteContainerUseCase(get_container_repository())


# =============================================================================
# Component Use-Case Factories
# =============================================================================


def get_create_component_use_case() -> CreateComponentUseCase:
    """Get CreateComponentUseCase with repository dependency."""
    return CreateComponentUseCase(get_component_repository())


def get_get_component_use_case() -> GetComponentUseCase:
    """Get GetComponentUseCase with repository dependency."""
    return GetComponentUseCase(get_component_repository())


def get_list_components_use_case() -> ListComponentsUseCase:
    """Get ListComponentsUseCase with repository dependency."""
    return ListComponentsUseCase(get_component_repository())


def get_update_component_use_case() -> UpdateComponentUseCase:
    """Get UpdateComponentUseCase with repository dependency."""
    return UpdateComponentUseCase(get_component_repository())


def get_delete_component_use_case() -> DeleteComponentUseCase:
    """Get DeleteComponentUseCase with repository dependency."""
    return DeleteComponentUseCase(get_component_repository())


# =============================================================================
# Relationship Use-Case Factories
# =============================================================================


def get_create_relationship_use_case() -> CreateRelationshipUseCase:
    """Get CreateRelationshipUseCase with repository dependency."""
    return CreateRelationshipUseCase(get_relationship_repository())


def get_get_relationship_use_case() -> GetRelationshipUseCase:
    """Get GetRelationshipUseCase with repository dependency."""
    return GetRelationshipUseCase(get_relationship_repository())


def get_list_relationships_use_case() -> ListRelationshipsUseCase:
    """Get ListRelationshipsUseCase with repository dependency."""
    return ListRelationshipsUseCase(get_relationship_repository())


def get_update_relationship_use_case() -> UpdateRelationshipUseCase:
    """Get UpdateRelationshipUseCase with repository dependency."""
    return UpdateRelationshipUseCase(get_relationship_repository())


def get_delete_relationship_use_case() -> DeleteRelationshipUseCase:
    """Get DeleteRelationshipUseCase with repository dependency."""
    return DeleteRelationshipUseCase(get_relationship_repository())


# =============================================================================
# DeploymentNode Use-Case Factories
# =============================================================================


def get_create_deployment_node_use_case() -> CreateDeploymentNodeUseCase:
    """Get CreateDeploymentNodeUseCase with repository dependency."""
    return CreateDeploymentNodeUseCase(get_deployment_node_repository())


def get_get_deployment_node_use_case() -> GetDeploymentNodeUseCase:
    """Get GetDeploymentNodeUseCase with repository dependency."""
    return GetDeploymentNodeUseCase(get_deployment_node_repository())


def get_list_deployment_nodes_use_case() -> ListDeploymentNodesUseCase:
    """Get ListDeploymentNodesUseCase with repository dependency."""
    return ListDeploymentNodesUseCase(get_deployment_node_repository())


def get_update_deployment_node_use_case() -> UpdateDeploymentNodeUseCase:
    """Get UpdateDeploymentNodeUseCase with repository dependency."""
    return UpdateDeploymentNodeUseCase(get_deployment_node_repository())


def get_delete_deployment_node_use_case() -> DeleteDeploymentNodeUseCase:
    """Get DeleteDeploymentNodeUseCase with repository dependency."""
    return DeleteDeploymentNodeUseCase(get_deployment_node_repository())


# =============================================================================
# DynamicStep Use-Case Factories
# =============================================================================


def get_create_dynamic_step_use_case() -> CreateDynamicStepUseCase:
    """Get CreateDynamicStepUseCase with repository dependency."""
    return CreateDynamicStepUseCase(get_dynamic_step_repository())


def get_get_dynamic_step_use_case() -> GetDynamicStepUseCase:
    """Get GetDynamicStepUseCase with repository dependency."""
    return GetDynamicStepUseCase(get_dynamic_step_repository())


def get_list_dynamic_steps_use_case() -> ListDynamicStepsUseCase:
    """Get ListDynamicStepsUseCase with repository dependency."""
    return ListDynamicStepsUseCase(get_dynamic_step_repository())


def get_update_dynamic_step_use_case() -> UpdateDynamicStepUseCase:
    """Get UpdateDynamicStepUseCase with repository dependency."""
    return UpdateDynamicStepUseCase(get_dynamic_step_repository())


def get_delete_dynamic_step_use_case() -> DeleteDynamicStepUseCase:
    """Get DeleteDynamicStepUseCase with repository dependency."""
    return DeleteDynamicStepUseCase(get_dynamic_step_repository())


# =============================================================================
# Diagram Use-Case Factories
# =============================================================================


def get_system_context_diagram_use_case() -> GetSystemContextDiagramUseCase:
    """Get GetSystemContextDiagramUseCase with repository dependencies."""
    return GetSystemContextDiagramUseCase(
        software_system_repo=get_software_system_repository(),
        relationship_repo=get_relationship_repository(),
    )


def get_container_diagram_use_case() -> GetContainerDiagramUseCase:
    """Get GetContainerDiagramUseCase with repository dependencies."""
    return GetContainerDiagramUseCase(
        software_system_repo=get_software_system_repository(),
        container_repo=get_container_repository(),
        relationship_repo=get_relationship_repository(),
    )


def get_component_diagram_use_case() -> GetComponentDiagramUseCase:
    """Get GetComponentDiagramUseCase with repository dependencies."""
    return GetComponentDiagramUseCase(
        software_system_repo=get_software_system_repository(),
        container_repo=get_container_repository(),
        component_repo=get_component_repository(),
        relationship_repo=get_relationship_repository(),
    )


def get_system_landscape_diagram_use_case() -> GetSystemLandscapeDiagramUseCase:
    """Get GetSystemLandscapeDiagramUseCase with repository dependencies."""
    return GetSystemLandscapeDiagramUseCase(
        software_system_repo=get_software_system_repository(),
        relationship_repo=get_relationship_repository(),
    )


def get_deployment_diagram_use_case() -> GetDeploymentDiagramUseCase:
    """Get GetDeploymentDiagramUseCase with repository dependencies."""
    return GetDeploymentDiagramUseCase(
        deployment_node_repo=get_deployment_node_repository(),
        container_repo=get_container_repository(),
        relationship_repo=get_relationship_repository(),
    )


def get_dynamic_diagram_use_case() -> GetDynamicDiagramUseCase:
    """Get GetDynamicDiagramUseCase with repository dependencies."""
    return GetDynamicDiagramUseCase(
        dynamic_step_repo=get_dynamic_step_repository(),
        software_system_repo=get_software_system_repository(),
        container_repo=get_container_repository(),
        component_repo=get_component_repository(),
    )

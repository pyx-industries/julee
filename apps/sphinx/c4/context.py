"""C4 context for sphinx integration.

Provides centralized access to C4 use cases within the Sphinx extension context.

Use cases are exposed as properties for clean architecture compliance:
    response = context.list_software_systems.execute_sync(ListSoftwareSystemsRequest())
    systems = response.entities
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from julee.c4.use_cases.crud import (
    # Component use cases
    CreateComponentUseCase,
    GetComponentUseCase,
    ListComponentsUseCase,
    # Container use cases
    CreateContainerUseCase,
    GetContainerUseCase,
    ListContainersUseCase,
    # DeploymentNode use cases
    CreateDeploymentNodeUseCase,
    GetDeploymentNodeUseCase,
    ListDeploymentNodesUseCase,
    # DynamicStep use cases
    CreateDynamicStepUseCase,
    GetDynamicStepUseCase,
    ListDynamicStepsUseCase,
    # Relationship use cases
    CreateRelationshipUseCase,
    GetRelationshipUseCase,
    ListRelationshipsUseCase,
    # SoftwareSystem use cases
    CreateSoftwareSystemUseCase,
    GetSoftwareSystemUseCase,
    ListSoftwareSystemsUseCase,
)
from julee.c4.use_cases.diagrams.component_diagram import GetComponentDiagramUseCase
from julee.c4.use_cases.diagrams.container_diagram import GetContainerDiagramUseCase
from julee.c4.use_cases.diagrams.deployment_diagram import GetDeploymentDiagramUseCase
from julee.c4.use_cases.diagrams.dynamic_diagram import GetDynamicDiagramUseCase
from julee.c4.use_cases.diagrams.system_context import GetSystemContextDiagramUseCase
from julee.c4.use_cases.diagrams.system_landscape import GetSystemLandscapeDiagramUseCase

from .repositories import (
    SphinxEnvComponentRepository,
    SphinxEnvContainerRepository,
    SphinxEnvDeploymentNodeRepository,
    SphinxEnvDynamicStepRepository,
    SphinxEnvRelationshipRepository,
    SphinxEnvSoftwareSystemRepository,
)

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment


@dataclass
class C4Context:
    """Context providing access to C4 use cases.

    Use cases are exposed as properties for clean architecture compliance.
    Repositories are internal implementation details.
    """

    # Internal repositories (not for direct access)
    _software_system_repo: SphinxEnvSoftwareSystemRepository = field(repr=False)
    _container_repo: SphinxEnvContainerRepository = field(repr=False)
    _component_repo: SphinxEnvComponentRepository = field(repr=False)
    _relationship_repo: SphinxEnvRelationshipRepository = field(repr=False)
    _deployment_node_repo: SphinxEnvDeploymentNodeRepository = field(repr=False)
    _dynamic_step_repo: SphinxEnvDynamicStepRepository = field(repr=False)

    # SoftwareSystem use cases
    @property
    def get_software_system(self) -> GetSoftwareSystemUseCase:
        return GetSoftwareSystemUseCase(self._software_system_repo)

    @property
    def list_software_systems(self) -> ListSoftwareSystemsUseCase:
        return ListSoftwareSystemsUseCase(self._software_system_repo)

    @property
    def create_software_system(self) -> CreateSoftwareSystemUseCase:
        return CreateSoftwareSystemUseCase(self._software_system_repo)

    # Container use cases
    @property
    def get_container(self) -> GetContainerUseCase:
        return GetContainerUseCase(self._container_repo)

    @property
    def list_containers(self) -> ListContainersUseCase:
        return ListContainersUseCase(self._container_repo)

    @property
    def create_container(self) -> CreateContainerUseCase:
        return CreateContainerUseCase(self._container_repo)

    # Component use cases
    @property
    def get_component(self) -> GetComponentUseCase:
        return GetComponentUseCase(self._component_repo)

    @property
    def list_components(self) -> ListComponentsUseCase:
        return ListComponentsUseCase(self._component_repo)

    @property
    def create_component(self) -> CreateComponentUseCase:
        return CreateComponentUseCase(self._component_repo)

    # Relationship use cases
    @property
    def get_relationship(self) -> GetRelationshipUseCase:
        return GetRelationshipUseCase(self._relationship_repo)

    @property
    def list_relationships(self) -> ListRelationshipsUseCase:
        return ListRelationshipsUseCase(self._relationship_repo)

    @property
    def create_relationship(self) -> CreateRelationshipUseCase:
        return CreateRelationshipUseCase(self._relationship_repo)

    # DeploymentNode use cases
    @property
    def get_deployment_node(self) -> GetDeploymentNodeUseCase:
        return GetDeploymentNodeUseCase(self._deployment_node_repo)

    @property
    def list_deployment_nodes(self) -> ListDeploymentNodesUseCase:
        return ListDeploymentNodesUseCase(self._deployment_node_repo)

    @property
    def create_deployment_node(self) -> CreateDeploymentNodeUseCase:
        return CreateDeploymentNodeUseCase(self._deployment_node_repo)

    # DynamicStep use cases
    @property
    def get_dynamic_step(self) -> GetDynamicStepUseCase:
        return GetDynamicStepUseCase(self._dynamic_step_repo)

    @property
    def list_dynamic_steps(self) -> ListDynamicStepsUseCase:
        return ListDynamicStepsUseCase(self._dynamic_step_repo)

    @property
    def create_dynamic_step(self) -> CreateDynamicStepUseCase:
        return CreateDynamicStepUseCase(self._dynamic_step_repo)

    # Diagram use cases (require multiple repositories)
    @property
    def get_system_context_diagram(self) -> GetSystemContextDiagramUseCase:
        return GetSystemContextDiagramUseCase(
            self._software_system_repo,
            self._relationship_repo,
        )

    @property
    def get_container_diagram(self) -> GetContainerDiagramUseCase:
        return GetContainerDiagramUseCase(
            self._software_system_repo,
            self._container_repo,
            self._relationship_repo,
        )

    @property
    def get_component_diagram(self) -> GetComponentDiagramUseCase:
        return GetComponentDiagramUseCase(
            self._software_system_repo,
            self._container_repo,
            self._component_repo,
            self._relationship_repo,
        )

    @property
    def get_system_landscape_diagram(self) -> GetSystemLandscapeDiagramUseCase:
        return GetSystemLandscapeDiagramUseCase(
            self._software_system_repo,
            self._relationship_repo,
        )

    @property
    def get_deployment_diagram(self) -> GetDeploymentDiagramUseCase:
        return GetDeploymentDiagramUseCase(
            self._container_repo,
            self._deployment_node_repo,
            self._relationship_repo,
        )

    @property
    def get_dynamic_diagram(self) -> GetDynamicDiagramUseCase:
        return GetDynamicDiagramUseCase(
            self._software_system_repo,
            self._container_repo,
            self._component_repo,
            self._dynamic_step_repo,
        )


def create_c4_context(env: "BuildEnvironment") -> C4Context:
    """Create a C4Context from a Sphinx environment.

    Args:
        env: Sphinx build environment

    Returns:
        C4Context with all use cases initialized
    """
    return C4Context(
        _software_system_repo=SphinxEnvSoftwareSystemRepository(env),
        _container_repo=SphinxEnvContainerRepository(env),
        _component_repo=SphinxEnvComponentRepository(env),
        _relationship_repo=SphinxEnvRelationshipRepository(env),
        _deployment_node_repo=SphinxEnvDeploymentNodeRepository(env),
        _dynamic_step_repo=SphinxEnvDynamicStepRepository(env),
    )


_context_cache: dict[int, C4Context] = {}


def get_c4_context(app: "Sphinx") -> C4Context:
    """Get or create C4Context for a Sphinx application.

    Uses a cache keyed by env id to avoid recreating context on every call.

    Args:
        app: Sphinx application instance

    Returns:
        C4Context for this build
    """
    env_id = id(app.env)
    if env_id not in _context_cache:
        _context_cache[env_id] = create_c4_context(app.env)
    return _context_cache[env_id]


def clear_c4_context_cache() -> None:
    """Clear the context cache.

    Called on builder-inited to ensure fresh context for each build.
    """
    _context_cache.clear()

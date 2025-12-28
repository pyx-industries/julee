"""C4 context for sphinx integration.

Provides centralized access to C4 repositories and services within
the Sphinx extension context.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from julee.core.repositories.sync_adapter import SyncRepositoryAdapter

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

    from julee.c4.entities.component import Component
    from julee.c4.entities.container import Container
    from julee.c4.entities.deployment_node import DeploymentNode
    from julee.c4.entities.dynamic_step import DynamicStep
    from julee.c4.entities.relationship import Relationship
    from julee.c4.entities.software_system import SoftwareSystem


@dataclass
class C4Context:
    """Context providing access to C4 repositories.

    All repositories are wrapped in SyncRepositoryAdapter for synchronous
    use in Sphinx directives, while maintaining async interface compatibility.
    """

    software_system_repo: "SyncRepositoryAdapter[SoftwareSystem]"
    container_repo: "SyncRepositoryAdapter[Container]"
    component_repo: "SyncRepositoryAdapter[Component]"
    relationship_repo: "SyncRepositoryAdapter[Relationship]"
    deployment_node_repo: "SyncRepositoryAdapter[DeploymentNode]"
    dynamic_step_repo: "SyncRepositoryAdapter[DynamicStep]"


def create_c4_context(env: "BuildEnvironment") -> C4Context:
    """Create a C4Context from a Sphinx environment.

    Args:
        env: Sphinx build environment

    Returns:
        C4Context with all repositories initialized
    """
    return C4Context(
        software_system_repo=SyncRepositoryAdapter(
            SphinxEnvSoftwareSystemRepository(env)
        ),
        container_repo=SyncRepositoryAdapter(SphinxEnvContainerRepository(env)),
        component_repo=SyncRepositoryAdapter(SphinxEnvComponentRepository(env)),
        relationship_repo=SyncRepositoryAdapter(SphinxEnvRelationshipRepository(env)),
        deployment_node_repo=SyncRepositoryAdapter(
            SphinxEnvDeploymentNodeRepository(env)
        ),
        dynamic_step_repo=SyncRepositoryAdapter(SphinxEnvDynamicStepRepository(env)),
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

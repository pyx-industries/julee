"""Deployment repository protocol.

Defines the interface for discovering and accessing deployments
in a codebase. Implementations may read from the filesystem, from
cached state, or from other sources.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.deployment import Deployment, DeploymentType


@runtime_checkable
class DeploymentRepository(Protocol):
    """Repository for deployment discovery and access.

    Unlike typical CRUD repositories, this repository is primarily
    read-oriented - deployments are defined by the filesystem
    structure, not created through the repository.

    The repository may filter results based on infrastructure type
    and other deployment characteristics.
    """

    async def list_all(self) -> list[Deployment]:
        """List all discovered deployments.

        Returns:
            All deployments in the solution's deployments/ directory
        """
        ...

    async def get(self, slug: str) -> Deployment | None:
        """Get a deployment by its slug.

        Args:
            slug: The directory name / identifier

        Returns:
            Deployment if found, None otherwise
        """
        ...

    async def list_by_type(self, deployment_type: DeploymentType) -> list[Deployment]:
        """List deployments of a specific type.

        Args:
            deployment_type: The deployment type to filter by

        Returns:
            Deployments matching the specified type
        """
        ...

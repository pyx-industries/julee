"""Deployment doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

Deployments are infrastructure-as-code configurations that provision and run
applications on target environments. They form the outermost layer of Clean
Architecture in an IaC world.

Doctrine:
- Deployment → Application → BoundedContext (dependency chain flows outward)
- Solution MAY contain one or more Deployments
- Deployments MAY reference applications they provision
"""

import pytest

from julee.core.infrastructure.repositories.introspection import (
    FilesystemDeploymentRepository,
    FilesystemSolutionRepository,
)

# =============================================================================
# DOCTRINE: Deployment Discovery
# =============================================================================


class TestDeploymentDiscovery:
    """Doctrine about deployment discovery."""

    @pytest.mark.asyncio
    async def test_deployments_MAY_be_discovered(
        self, deployment_repo: FilesystemDeploymentRepository
    ) -> None:
        """Deployments MAY be discovered at {solution}/deployments/.

        This tests the discovery capability. A solution is not required to
        have deployments - they are optional infrastructure-as-code configs.
        """
        deployments = await deployment_repo.list_all()

        # The result should be a list (possibly empty)
        assert isinstance(deployments, list)

        # If deployments exist, verify their structure
        for dep in deployments:
            assert dep.slug, "Each deployment MUST have a slug"
            assert dep.path, "Each deployment MUST have a path"
            assert dep.deployment_type, "Each deployment MUST have a type"


# =============================================================================
# DOCTRINE: Deployment in Solution
# =============================================================================


class TestDeploymentInSolution:
    """Doctrine about deployments within solutions."""

    @pytest.mark.asyncio
    async def test_solution_MAY_contain_deployments(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """A solution MAY contain one or more deployments.

        Deployments are discovered at {solution}/deployments/. This tests
        the capability, not a specific count.
        """
        solution = await solution_repo.get()

        # The solution's deployments property returns deployments in this solution
        assert isinstance(solution.deployments, list)

        # If there are deployments, verify their structure
        for dep in solution.deployments:
            assert dep.slug, "Each deployment MUST have a slug"
            assert dep.deployment_type, "Each deployment MUST have a type"

    @pytest.mark.asyncio
    async def test_solution_all_deployments_MUST_include_nested(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """Solution.all_deployments MUST include deployments from nested solutions.

        This aggregate property flattens the hierarchy for convenient access.
        """
        solution = await solution_repo.get()

        # all_deployments should include nested
        all_deps = solution.all_deployments

        # Count deployments in nested solutions
        nested_dep_count = sum(
            len(nested.deployments) for nested in solution.nested_solutions
        )

        # all_deployments should equal direct + nested
        expected_count = len(solution.deployments) + nested_dep_count
        assert len(all_deps) == expected_count, (
            f"all_deployments ({len(all_deps)}) MUST equal "
            f"direct ({len(solution.deployments)}) + "
            f"nested ({nested_dep_count})"
        )


# =============================================================================
# DOCTRINE: Deployment Types
# =============================================================================


class TestDeploymentTypes:
    """Doctrine about deployment type classification."""

    @pytest.mark.asyncio
    async def test_deployment_type_MUST_be_classified(
        self, deployment_repo: FilesystemDeploymentRepository
    ) -> None:
        """Each deployment MUST have a classified type.

        Types include: DOCKER-COMPOSE, KUBERNETES, TERRAFORM, CLOUDFORMATION,
        ANSIBLE, or UNKNOWN if the type cannot be determined.
        """
        deployments = await deployment_repo.list_all()

        for dep in deployments:
            assert (
                dep.deployment_type is not None
            ), f"Deployment '{dep.slug}' MUST have a type"
            # Verify it's a valid enum value
            assert dep.deployment_type.value in [
                "DOCKER-COMPOSE",
                "KUBERNETES",
                "TERRAFORM",
                "CLOUDFORMATION",
                "ANSIBLE",
                "UNKNOWN",
            ], f"Deployment '{dep.slug}' has invalid type: {dep.deployment_type}"


# =============================================================================
# DOCTRINE: Deployment Dependencies
# =============================================================================


class TestDeploymentDependencies:
    """Doctrine about deployment dependencies on applications."""

    @pytest.mark.asyncio
    async def test_deployments_MAY_reference_applications(
        self, deployment_repo: FilesystemDeploymentRepository
    ) -> None:
        """Deployments MAY reference applications they provision.

        The application_refs field contains slugs of applications this
        deployment depends on. This is detected heuristically from
        configuration files.
        """
        deployments = await deployment_repo.list_all()

        for dep in deployments:
            # application_refs should be a list (possibly empty)
            assert isinstance(
                dep.application_refs, list
            ), f"Deployment '{dep.slug}' application_refs MUST be a list"

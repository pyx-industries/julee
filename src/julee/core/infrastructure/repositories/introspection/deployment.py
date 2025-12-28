"""Filesystem-based deployment repository.

Discovers deployments by scanning the filesystem structure.
This is a read-only repository - deployments are defined by
the filesystem, not created through this repository.
"""

from pathlib import Path

from julee.core.doctrine_constants import DEPLOYMENTS_ROOT
from julee.core.entities.deployment import (
    Deployment,
    DeploymentStructuralMarkers,
    DeploymentType,
)

__all__ = ["FilesystemDeploymentRepository"]


def _get_description_from_readme(path: Path) -> str | None:
    """Extract first meaningful line from README file.

    Args:
        path: Directory to search for README

    Returns:
        First non-empty, non-header line from README, or None if not found
    """
    for readme_name in ("README.md", "README.rst", "README.txt", "README"):
        readme_file = path / readme_name
        if readme_file.exists():
            try:
                content = readme_file.read_text()
                for line in content.split("\n"):
                    line = line.strip()
                    # Skip empty lines and markdown headers
                    if not line:
                        continue
                    if line.startswith("#"):
                        continue
                    if line.startswith("=") or line.startswith("-"):
                        continue
                    # Return first meaningful line
                    return line[:200] if len(line) > 200 else line
            except OSError:
                pass
    return None


class FilesystemDeploymentRepository:
    """Repository that discovers deployments by scanning filesystem.

    Inspects directory structure to find deployments under {solution}/deployments/.
    Deployments are classified by type based on structural markers.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize repository.

        Args:
            project_root: Root directory of the project (solution)
        """
        self.project_root = project_root
        self._cache: list[Deployment] | None = None

    def _has_file(self, path: Path, name: str) -> bool:
        """Check if path contains a file with the given name."""
        return (path / name).is_file()

    def _has_files_matching(self, path: Path, pattern: str) -> bool:
        """Check if path contains files matching a glob pattern."""
        return any(path.glob(pattern))

    def _has_subdir(self, path: Path, name: str) -> bool:
        """Check if path contains a subdirectory with the given name."""
        return (path / name).is_dir()

    def _detect_markers(self, path: Path) -> DeploymentStructuralMarkers:
        """Detect structural markers in a deployment directory."""
        return DeploymentStructuralMarkers(
            # Docker Compose markers
            has_docker_compose=(
                self._has_file(path, "docker-compose.yml")
                or self._has_file(path, "docker-compose.yaml")
            ),
            has_dockerfiles=self._has_files_matching(path, "Dockerfile*"),
            # Kubernetes markers
            has_manifests=self._has_subdir(path, "manifests"),
            has_helm=self._has_subdir(path, "helm"),
            has_kustomize=(
                self._has_subdir(path, "kustomize")
                or self._has_file(path, "kustomization.yaml")
            ),
            # Terraform markers
            has_terraform=self._has_files_matching(path, "*.tf"),
            # CloudFormation markers
            has_cloudformation=(
                self._has_file(path, "template.yaml")
                or self._has_file(path, "template.json")
                or self._has_subdir(path, "cloudformation")
            ),
            # Ansible markers
            has_ansible=(
                self._has_subdir(path, "playbooks")
                or self._has_file(path, "ansible.cfg")
            ),
            # Common markers
            has_env_files=self._has_files_matching(path, "*.env*"),
            has_secrets=self._has_subdir(path, "secrets"),
        )

    def _infer_deployment_type(
        self, path: Path, markers: DeploymentStructuralMarkers
    ) -> DeploymentType:
        """Infer deployment type from structural markers."""
        # Priority order matters - more specific types first
        if markers.has_manifests or markers.has_helm or markers.has_kustomize:
            return DeploymentType.KUBERNETES
        if markers.has_terraform:
            return DeploymentType.TERRAFORM
        if markers.has_cloudformation:
            return DeploymentType.CLOUDFORMATION
        if markers.has_ansible:
            return DeploymentType.ANSIBLE
        if markers.has_docker_compose or markers.has_dockerfiles:
            return DeploymentType.DOCKER_COMPOSE
        return DeploymentType.UNKNOWN

    def _detect_application_refs(self, path: Path) -> list[str]:
        """Detect which applications this deployment references.

        Looks for references in configuration files, Dockerfiles, etc.
        This is a heuristic - it looks for app names in common patterns.
        """
        app_refs: set[str] = set()

        # Check Dockerfiles for app references (e.g., Dockerfile.api)
        for dockerfile in path.glob("Dockerfile*"):
            suffix = dockerfile.suffix or dockerfile.name.replace("Dockerfile", "")
            if suffix.startswith("."):
                suffix = suffix[1:]
            if suffix:
                app_refs.add(suffix)

        # Check docker-compose for service definitions
        for compose_file in ["docker-compose.yml", "docker-compose.yaml"]:
            compose_path = path / compose_file
            if compose_path.exists():
                try:
                    content = compose_path.read_text()
                    # Simple heuristic: look for service names that match app patterns
                    # A proper implementation would parse YAML
                    for line in content.split("\n"):
                        stripped = line.strip()
                        if stripped.endswith(":") and not stripped.startswith("#"):
                            service = stripped[:-1].strip()
                            if service and not service.startswith("-"):
                                app_refs.add(service)
                except OSError:
                    pass

        return sorted(app_refs)

    def _discover_all(self) -> list[Deployment]:
        """Discover all deployments."""
        deployments_path = self.project_root / DEPLOYMENTS_ROOT

        if not deployments_path.exists():
            return []

        deployments = []

        for candidate in deployments_path.iterdir():
            if not candidate.is_dir():
                continue

            # Skip dot-prefixed directories
            if candidate.name.startswith("."):
                continue

            # Skip __pycache__
            if candidate.name == "__pycache__":
                continue

            markers = self._detect_markers(candidate)
            deployment_type = self._infer_deployment_type(candidate, markers)
            app_refs = self._detect_application_refs(candidate)

            deployment = Deployment(
                slug=candidate.name,
                path=str(candidate),
                description=_get_description_from_readme(candidate),
                deployment_type=deployment_type,
                markers=markers,
                application_refs=app_refs,
            )
            deployments.append(deployment)

        return sorted(deployments, key=lambda d: d.slug)

    async def list_all(self) -> list[Deployment]:
        """List all discovered deployments."""
        if self._cache is None:
            self._cache = self._discover_all()
        return self._cache

    async def get(self, slug: str) -> Deployment | None:
        """Get a deployment by slug."""
        deployments = await self.list_all()
        for deployment in deployments:
            if deployment.slug == slug:
                return deployment
        return None

    async def list_by_type(self, deployment_type: DeploymentType) -> list[Deployment]:
        """List deployments of a specific type."""
        deployments = await self.list_all()
        return [d for d in deployments if d.deployment_type == deployment_type]

    def invalidate_cache(self) -> None:
        """Clear the discovery cache."""
        self._cache = None

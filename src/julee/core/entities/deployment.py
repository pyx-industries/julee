"""Deployment domain model.

Represents a deployment as infrastructure-as-code that provisions applications
on target environments, forming the outermost layer of Clean Architecture in
an IaC world.

Deployments depend on applications which depend on bounded contexts, completing
the dependency chain: Deployment → Application → BoundedContext.

In Uncle Bob's original Clean Architecture, the application layer is described
as the outermost layer. However, in an infrastructure-as-code world, deployments
represent a distinct concern outside applications - they describe WHERE and HOW
applications run, not WHAT they do.

The `deployments/` directory is a reserved word - it cannot be a bounded context
name. Deployments live at `{solution}/deployments/` and may contain multiple
deployment configurations for different environments or infrastructure targets.
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class DeploymentType(str, Enum):
    """Classification of deployment types.

    Each type represents a different infrastructure-as-code approach or
    container orchestration platform.
    """

    DOCKER_COMPOSE = "DOCKER-COMPOSE"
    KUBERNETES = "KUBERNETES"
    TERRAFORM = "TERRAFORM"
    CLOUDFORMATION = "CLOUDFORMATION"
    ANSIBLE = "ANSIBLE"
    UNKNOWN = "UNKNOWN"


class DeploymentStructuralMarkers(BaseModel):
    """Structural markers indicating what a deployment contains.

    These markers reflect the infrastructure-as-code patterns present in a
    deployment. Detection of these markers helps classify deployment type.
    """

    # Docker Compose markers
    has_docker_compose: bool = False
    has_dockerfiles: bool = False

    # Kubernetes markers
    has_manifests: bool = False
    has_helm: bool = False
    has_kustomize: bool = False

    # Terraform markers
    has_terraform: bool = False

    # CloudFormation markers
    has_cloudformation: bool = False

    # Ansible markers
    has_ansible: bool = False

    # Common markers
    has_env_files: bool = False
    has_secrets: bool = False


class Deployment(BaseModel):
    """A deployment configuration for running applications on infrastructure.

    Deployments are the outermost layer of the Clean Architecture in julee,
    representing the infrastructure-as-code that provisions and runs applications.
    They depend on applications but are not depended upon by anything else in
    the solution.
    """

    # Identity
    slug: str = Field(description="Deployment identifier, typically directory name")
    path: str = Field(description="Absolute filesystem path to deployment directory")

    # Classification
    deployment_type: DeploymentType = Field(
        description="Type of deployment (Docker Compose, Kubernetes, etc.)"
    )

    # Structure
    markers: DeploymentStructuralMarkers = Field(
        default_factory=DeploymentStructuralMarkers,
        description="Structural markers indicating deployment contents",
    )

    # Dependencies
    application_refs: list[str] = Field(
        default_factory=list,
        description="Slugs of applications this deployment depends on",
    )

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty and is lowercase."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip().lower()

    @property
    def absolute_path(self) -> Path:
        """Get path as a Path object."""
        return Path(self.path)

    @property
    def display_name(self) -> str:
        """Human-readable name derived from slug."""
        return self.slug.replace("-", " ").replace("_", " ").title()

    @property
    def is_containerized(self) -> bool:
        """True if deployment uses container technology."""
        return self.markers.has_docker_compose or self.markers.has_dockerfiles

    @property
    def is_orchestrated(self) -> bool:
        """True if deployment uses container orchestration."""
        return (
            self.markers.has_manifests
            or self.markers.has_helm
            or self.markers.has_kustomize
        )

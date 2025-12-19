"""DeploymentNode domain model.

Infrastructure where containers are deployed.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from ...utils import slugify


class NodeType(str, Enum):
    """Classification of deployment nodes."""

    PHYSICAL_SERVER = "physical_server"
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER_RUNTIME = "container_runtime"  # Docker, containerd, etc.
    KUBERNETES_CLUSTER = "kubernetes_cluster"
    KUBERNETES_POD = "kubernetes_pod"
    CLOUD_REGION = "cloud_region"
    AVAILABILITY_ZONE = "availability_zone"
    BROWSER = "browser"
    MOBILE_DEVICE = "mobile_device"
    DNS = "dns"
    LOAD_BALANCER = "load_balancer"
    FIREWALL = "firewall"
    CDN = "cdn"
    OTHER = "other"


class ContainerInstance(BaseModel):
    """A deployed instance of a container.

    Represents a container running within a deployment node.

    Attributes:
        container_slug: Reference to the Container being deployed
        instance_count: Number of instances (for scaling)
        properties: Key-value properties (version, config, etc.)
    """

    container_slug: str
    instance_count: int = 1
    properties: dict[str, str] = Field(default_factory=dict)

    @field_validator("container_slug", mode="before")
    @classmethod
    def validate_container_slug(cls, v: str) -> str:
        """Validate container_slug is not empty."""
        if not v or not v.strip():
            raise ValueError("container_slug cannot be empty")
        return v.strip()


class DeploymentNode(BaseModel):
    """DeploymentNode entity.

    Represents infrastructure where containers run - physical servers,
    VMs, Docker hosts, Kubernetes clusters, execution environments, etc.

    Deployment nodes can be nested to represent infrastructure hierarchy
    (e.g., Cloud Region > Availability Zone > Kubernetes Cluster > Pod).

    Attributes:
        slug: URL-safe identifier
        name: Display name (e.g., "Production Web Server")
        environment: Deployment environment (e.g., "production", "staging")
        node_type: Classification of infrastructure
        description: What this node represents
        technology: Infrastructure technology (e.g., "AWS EC2 t3.large")
        instances: Number of node instances (for scaling representation)
        parent_slug: Parent deployment node (for nesting)
        container_instances: Containers deployed to this node
        properties: Key-value properties (IP, URL, etc.)
        tags: Arbitrary tags
        docname: RST document where defined
    """

    slug: str
    name: str
    environment: str = "production"
    node_type: NodeType = NodeType.OTHER
    description: str = ""
    technology: str = ""
    instances: int = 1
    parent_slug: str | None = None
    container_instances: list[ContainerInstance] = Field(default_factory=list)
    properties: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    docname: str = ""

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate and normalize slug."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return slugify(v.strip())

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @property
    def has_parent(self) -> bool:
        """Check if this node has a parent node."""
        return self.parent_slug is not None

    @property
    def has_containers(self) -> bool:
        """Check if this node has deployed containers."""
        return len(self.container_instances) > 0

    @property
    def total_container_instances(self) -> int:
        """Get total count of container instances."""
        return sum(ci.instance_count for ci in self.container_instances)

    def deploys_container(self, container_slug: str) -> bool:
        """Check if a specific container is deployed here."""
        return any(
            ci.container_slug == container_slug for ci in self.container_instances
        )

    def add_container_instance(
        self,
        container_slug: str,
        instance_count: int = 1,
        properties: dict[str, str] | None = None,
    ) -> None:
        """Add a container instance to this node."""
        # Check if already deployed, update count
        for ci in self.container_instances:
            if ci.container_slug == container_slug:
                ci.instance_count += instance_count
                if properties:
                    ci.properties.update(properties)
                return
        # Add new instance
        self.container_instances.append(
            ContainerInstance(
                container_slug=container_slug,
                instance_count=instance_count,
                properties=properties or {},
            )
        )

    def has_tag(self, tag: str) -> bool:
        """Check if node has a specific tag (case-insensitive)."""
        return tag.lower() in [t.lower() for t in self.tags]

    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        if not self.has_tag(tag):
            self.tags.append(tag)

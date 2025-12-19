"""Tests for DeploymentNode domain model."""

import pytest
from pydantic import ValidationError

from julee.docs.sphinx_c4.domain.models.deployment_node import (
    ContainerInstance,
    DeploymentNode,
    NodeType,
)


class TestContainerInstanceCreation:
    """Test ContainerInstance model creation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating a container instance with minimum fields."""
        instance = ContainerInstance(container_slug="api-app")

        assert instance.container_slug == "api-app"
        assert instance.instance_count == 1
        assert instance.properties == {}

    def test_create_with_all_fields(self) -> None:
        """Test creating a container instance with all fields."""
        instance = ContainerInstance(
            container_slug="api-app",
            instance_count=3,
            properties={"version": "1.0.0", "port": "8080"},
        )

        assert instance.container_slug == "api-app"
        assert instance.instance_count == 3
        assert instance.properties["version"] == "1.0.0"

    def test_empty_container_slug_raises_error(self) -> None:
        """Test that empty container_slug raises validation error."""
        with pytest.raises(ValidationError, match="container_slug cannot be empty"):
            ContainerInstance(container_slug="")


class TestDeploymentNodeCreation:
    """Test DeploymentNode model creation and validation."""

    def test_create_with_required_fields(self) -> None:
        """Test creating a deployment node with minimum fields."""
        node = DeploymentNode(
            slug="web-server-1",
            name="Web Server 1",
        )

        assert node.slug == "web-server-1"
        assert node.name == "Web Server 1"
        assert node.environment == "production"
        assert node.node_type == NodeType.OTHER
        assert node.parent_slug is None
        assert node.container_instances == []

    def test_create_with_all_fields(self) -> None:
        """Test creating a deployment node with all fields."""
        node = DeploymentNode(
            slug="web-server-1",
            name="Web Server 1",
            environment="production",
            node_type=NodeType.VIRTUAL_MACHINE,
            description="Primary web server",
            technology="AWS EC2 t3.large",
            instances=2,
            parent_slug="aws-us-east-1",
            container_instances=[ContainerInstance(container_slug="api-app")],
            properties={"ip": "10.0.1.10"},
            tags=["primary", "web"],
            docname="architecture/deployment",
        )

        assert node.technology == "AWS EC2 t3.large"
        assert node.instances == 2
        assert node.parent_slug == "aws-us-east-1"
        assert len(node.container_instances) == 1
        assert node.properties["ip"] == "10.0.1.10"

    def test_empty_slug_raises_error(self) -> None:
        """Test that empty slug raises validation error."""
        with pytest.raises(ValidationError, match="slug cannot be empty"):
            DeploymentNode(slug="", name="Test")

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError, match="name cannot be empty"):
            DeploymentNode(slug="test", name="")

    def test_slug_is_normalized(self) -> None:
        """Test that slug is normalized (slugified)."""
        node = DeploymentNode(slug="Web Server 1", name="Test")
        assert node.slug == "web-server-1"


class TestDeploymentNodeProperties:
    """Test deployment node properties."""

    def test_has_parent_true(self) -> None:
        """Test has_parent when parent_slug is set."""
        node = DeploymentNode(
            slug="test", name="Test", parent_slug="parent-node"
        )
        assert node.has_parent is True

    def test_has_parent_false(self) -> None:
        """Test has_parent when no parent."""
        node = DeploymentNode(slug="test", name="Test")
        assert node.has_parent is False

    def test_has_containers_true(self) -> None:
        """Test has_containers when containers deployed."""
        node = DeploymentNode(
            slug="test",
            name="Test",
            container_instances=[ContainerInstance(container_slug="api-app")],
        )
        assert node.has_containers is True

    def test_has_containers_false(self) -> None:
        """Test has_containers when no containers."""
        node = DeploymentNode(slug="test", name="Test")
        assert node.has_containers is False

    def test_total_container_instances(self) -> None:
        """Test total_container_instances calculation."""
        node = DeploymentNode(
            slug="test",
            name="Test",
            container_instances=[
                ContainerInstance(container_slug="api-app", instance_count=3),
                ContainerInstance(container_slug="web-app", instance_count=2),
            ],
        )
        assert node.total_container_instances == 5

    def test_total_container_instances_empty(self) -> None:
        """Test total_container_instances with no containers."""
        node = DeploymentNode(slug="test", name="Test")
        assert node.total_container_instances == 0


class TestDeploymentNodeContainerOperations:
    """Test container instance operations."""

    def test_deploys_container_true(self) -> None:
        """Test deploys_container returns True for deployed container."""
        node = DeploymentNode(
            slug="test",
            name="Test",
            container_instances=[ContainerInstance(container_slug="api-app")],
        )
        assert node.deploys_container("api-app") is True

    def test_deploys_container_false(self) -> None:
        """Test deploys_container returns False for non-deployed container."""
        node = DeploymentNode(
            slug="test",
            name="Test",
            container_instances=[ContainerInstance(container_slug="api-app")],
        )
        assert node.deploys_container("other-app") is False

    def test_add_container_instance_new(self) -> None:
        """Test adding a new container instance."""
        node = DeploymentNode(slug="test", name="Test")
        node.add_container_instance("api-app", instance_count=2)

        assert len(node.container_instances) == 1
        assert node.container_instances[0].container_slug == "api-app"
        assert node.container_instances[0].instance_count == 2

    def test_add_container_instance_existing(self) -> None:
        """Test adding to existing container instance updates count."""
        node = DeploymentNode(
            slug="test",
            name="Test",
            container_instances=[
                ContainerInstance(container_slug="api-app", instance_count=2)
            ],
        )
        node.add_container_instance("api-app", instance_count=3)

        assert len(node.container_instances) == 1
        assert node.container_instances[0].instance_count == 5

    def test_add_container_instance_with_properties(self) -> None:
        """Test adding container instance with properties."""
        node = DeploymentNode(slug="test", name="Test")
        node.add_container_instance(
            "api-app", instance_count=1, properties={"version": "1.0"}
        )

        assert node.container_instances[0].properties["version"] == "1.0"


class TestDeploymentNodeTags:
    """Test tag operations."""

    def test_has_tag(self) -> None:
        """Test tag lookup."""
        node = DeploymentNode(
            slug="test", name="Test", tags=["production", "primary"]
        )
        assert node.has_tag("production") is True
        assert node.has_tag("PRODUCTION") is True
        assert node.has_tag("staging") is False

    def test_add_tag(self) -> None:
        """Test adding a tag."""
        node = DeploymentNode(slug="test", name="Test", tags=["existing"])
        node.add_tag("new")
        assert "new" in node.tags
        assert len(node.tags) == 2


class TestNodeType:
    """Test NodeType enum."""

    @pytest.mark.parametrize(
        "node_type,expected_value",
        [
            (NodeType.PHYSICAL_SERVER, "physical_server"),
            (NodeType.VIRTUAL_MACHINE, "virtual_machine"),
            (NodeType.CONTAINER_RUNTIME, "container_runtime"),
            (NodeType.KUBERNETES_CLUSTER, "kubernetes_cluster"),
            (NodeType.KUBERNETES_POD, "kubernetes_pod"),
            (NodeType.CLOUD_REGION, "cloud_region"),
            (NodeType.AVAILABILITY_ZONE, "availability_zone"),
            (NodeType.BROWSER, "browser"),
            (NodeType.MOBILE_DEVICE, "mobile_device"),
            (NodeType.DNS, "dns"),
            (NodeType.LOAD_BALANCER, "load_balancer"),
            (NodeType.FIREWALL, "firewall"),
            (NodeType.CDN, "cdn"),
            (NodeType.OTHER, "other"),
        ],
    )
    def test_node_type_values(
        self, node_type: NodeType, expected_value: str
    ) -> None:
        """Test all node type values."""
        assert node_type.value == expected_value

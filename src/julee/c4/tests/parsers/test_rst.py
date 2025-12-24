"""Tests for C4 RST directive parsers."""

from pathlib import Path

from julee.c4.entities.component import Component
from julee.c4.entities.container import Container, ContainerType
from julee.c4.entities.deployment_node import (
    DeploymentNode,
    NodeType,
)
from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import (
    ElementType,
    Relationship,
)
from julee.c4.entities.software_system import (
    SoftwareSystem,
    SystemType,
)
from julee.c4.parsers.rst import (
    parse_component_content,
    parse_component_file,
    parse_container_content,
    parse_container_file,
    parse_deployment_node_content,
    parse_deployment_node_file,
    parse_dynamic_step_content,
    parse_dynamic_step_file,
    parse_relationship_content,
    parse_relationship_file,
    parse_software_system_content,
    parse_software_system_file,
    scan_software_system_directory,
)
from julee.c4.serializers.rst import (
    serialize_component,
    serialize_container,
    serialize_deployment_node,
    serialize_dynamic_step,
    serialize_relationship,
    serialize_software_system,
)

# =============================================================================
# SoftwareSystem Parser Tests
# =============================================================================


class TestParseSoftwareSystemContent:
    """Test parse_software_system_content function."""

    def test_parse_simple_system(self) -> None:
        """Test parsing a simple software system directive."""
        content = """.. define-software-system:: banking-system
   :name: Internet Banking System
   :type: internal
   :owner: Digital Team
   :technology: Java, Spring Boot

   Allows customers to view balances and make payments.
"""
        result = parse_software_system_content(content)

        assert result is not None
        assert result.slug == "banking-system"
        assert result.name == "Internet Banking System"
        assert result.system_type == "internal"
        assert result.owner == "Digital Team"
        assert "customers" in result.description

    def test_parse_system_with_tags(self) -> None:
        """Test parsing system with tags."""
        content = """.. define-software-system:: email-service
   :name: Email Service
   :type: external
   :tags: core, infrastructure

   External email delivery service.
"""
        result = parse_software_system_content(content)

        assert result is not None
        assert result.tags == ["core", "infrastructure"]
        assert result.system_type == "external"

    def test_parse_no_directive(self) -> None:
        """Test parsing content without directive returns None."""
        content = "No directive here."
        result = parse_software_system_content(content)
        assert result is None


class TestParseSoftwareSystemFile:
    """Test parse_software_system_file function."""

    def test_parse_valid_file(self, tmp_path: Path) -> None:
        """Test parsing a valid RST file."""
        file_path = tmp_path / "test-system.rst"
        file_path.write_text(
            """.. define-software-system:: test-system
   :name: Test System
   :type: internal

   A test system.
"""
        )
        result = parse_software_system_file(file_path)

        assert result is not None
        assert isinstance(result, SoftwareSystem)
        assert result.slug == "test-system"
        assert result.system_type == SystemType.INTERNAL

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing nonexistent file returns None."""
        result = parse_software_system_file(tmp_path / "nonexistent.rst")
        assert result is None


class TestScanSoftwareSystemDirectory:
    """Test scan_software_system_directory function."""

    def test_scan_finds_all_systems(self, tmp_path: Path) -> None:
        """Test scanning finds all system files."""
        (tmp_path / "sys1.rst").write_text(
            ".. define-software-system:: sys-one\n   :name: System One\n\n   First.\n"
        )
        (tmp_path / "sys2.rst").write_text(
            ".. define-software-system:: sys-two\n   :name: System Two\n\n   Second.\n"
        )

        systems = scan_software_system_directory(tmp_path)

        assert len(systems) == 2
        slugs = {s.slug for s in systems}
        assert slugs == {"sys-one", "sys-two"}

    def test_scan_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test scanning nonexistent directory returns empty list."""
        systems = scan_software_system_directory(tmp_path / "nonexistent")
        assert systems == []


class TestSoftwareSystemRoundTrip:
    """Test serialize -> parse round-trip for software systems."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple round-trip."""
        original = SoftwareSystem(
            slug="round-trip-system",
            name="Round Trip System",
            description="Test round-trip.",
            system_type=SystemType.INTERNAL,
            owner="Test Team",
            technology="Python, FastAPI",
            tags=["test", "demo"],
        )

        content = serialize_software_system(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        parsed = parse_software_system_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.name == original.name
        assert parsed.system_type == original.system_type
        assert parsed.owner == original.owner


# =============================================================================
# Container Parser Tests
# =============================================================================


class TestParseContainerContent:
    """Test parse_container_content function."""

    def test_parse_simple_container(self) -> None:
        """Test parsing a simple container directive."""
        content = """.. define-container:: web-app
   :name: Web Application
   :system: banking-system
   :type: web_application
   :technology: React, TypeScript

   Delivers the banking UI.
"""
        result = parse_container_content(content)

        assert result is not None
        assert result.slug == "web-app"
        assert result.name == "Web Application"
        assert result.system_slug == "banking-system"
        assert result.container_type == "web_application"


class TestParseContainerFile:
    """Test parse_container_file function."""

    def test_parse_valid_file(self, tmp_path: Path) -> None:
        """Test parsing a valid container RST file."""
        file_path = tmp_path / "test-container.rst"
        file_path.write_text(
            """.. define-container:: test-container
   :name: Test Container
   :system: test-system
   :type: api

   Test container.
"""
        )
        result = parse_container_file(file_path)

        assert result is not None
        assert isinstance(result, Container)
        assert result.slug == "test-container"
        assert result.container_type == ContainerType.API


class TestContainerRoundTrip:
    """Test serialize -> parse round-trip for containers."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple round-trip."""
        original = Container(
            slug="round-trip-container",
            name="Round Trip Container",
            system_slug="parent-system",
            description="Test round-trip.",
            container_type=ContainerType.DATABASE,
            technology="PostgreSQL",
        )

        content = serialize_container(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        parsed = parse_container_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.name == original.name
        assert parsed.system_slug == original.system_slug
        assert parsed.container_type == original.container_type


# =============================================================================
# Component Parser Tests
# =============================================================================


class TestParseComponentContent:
    """Test parse_component_content function."""

    def test_parse_simple_component(self) -> None:
        """Test parsing a simple component directive."""
        content = """.. define-component:: auth-controller
   :name: Authentication Controller
   :container: api-app
   :system: banking-system
   :technology: Spring MVC
   :interface: REST API

   Handles authentication.
"""
        result = parse_component_content(content)

        assert result is not None
        assert result.slug == "auth-controller"
        assert result.name == "Authentication Controller"
        assert result.container_slug == "api-app"
        assert result.system_slug == "banking-system"


class TestComponentRoundTrip:
    """Test serialize -> parse round-trip for components."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple round-trip."""
        original = Component(
            slug="round-trip-component",
            name="Round Trip Component",
            container_slug="parent-container",
            system_slug="parent-system",
            description="Test round-trip.",
            technology="Python",
            interface="gRPC",
        )

        content = serialize_component(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        parsed = parse_component_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.container_slug == original.container_slug
        assert parsed.system_slug == original.system_slug


# =============================================================================
# Relationship Parser Tests
# =============================================================================


class TestParseRelationshipContent:
    """Test parse_relationship_content function."""

    def test_parse_simple_relationship(self) -> None:
        """Test parsing a simple relationship directive."""
        content = """.. define-relationship:: user-to-webapp
   :source-type: person
   :source: customer
   :destination-type: container
   :destination: web-app
   :technology: HTTPS

   Uses
"""
        result = parse_relationship_content(content)

        assert result is not None
        assert result.slug == "user-to-webapp"
        assert result.source_type == "person"
        assert result.source_slug == "customer"
        assert result.destination_type == "container"
        assert result.destination_slug == "web-app"


class TestRelationshipRoundTrip:
    """Test serialize -> parse round-trip for relationships."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple round-trip."""
        original = Relationship(
            slug="round-trip-rel",
            source_type=ElementType.CONTAINER,
            source_slug="container-a",
            destination_type=ElementType.CONTAINER,
            destination_slug="container-b",
            description="Sends data to",
            technology="HTTPS/JSON",
        )

        content = serialize_relationship(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        parsed = parse_relationship_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.source_type == original.source_type
        assert parsed.destination_type == original.destination_type


# =============================================================================
# DeploymentNode Parser Tests
# =============================================================================


class TestParseDeploymentNodeContent:
    """Test parse_deployment_node_content function."""

    def test_parse_simple_node(self) -> None:
        """Test parsing a simple deployment node directive."""
        content = """.. define-deployment-node:: prod-web-server
   :name: Production Web Server
   :environment: production
   :type: virtual_machine
   :technology: Ubuntu 22.04

   Hosts the web application.
"""
        result = parse_deployment_node_content(content)

        assert result is not None
        assert result.slug == "prod-web-server"
        assert result.name == "Production Web Server"
        assert result.environment == "production"
        assert result.node_type == "virtual_machine"


class TestDeploymentNodeRoundTrip:
    """Test serialize -> parse round-trip for deployment nodes."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple round-trip."""
        original = DeploymentNode(
            slug="round-trip-node",
            name="Round Trip Node",
            environment="staging",
            node_type=NodeType.KUBERNETES_CLUSTER,
            description="Test round-trip.",
            technology="AWS EKS",
        )

        content = serialize_deployment_node(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        parsed = parse_deployment_node_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.name == original.name
        assert parsed.environment == original.environment


# =============================================================================
# DynamicStep Parser Tests
# =============================================================================


class TestParseDynamicStepContent:
    """Test parse_dynamic_step_content function."""

    def test_parse_simple_step(self) -> None:
        """Test parsing a simple dynamic step directive."""
        content = """.. define-dynamic-step:: login-step-1
   :sequence: user-login
   :step: 1
   :source-type: person
   :source: customer
   :destination-type: container
   :destination: web-app
   :technology: HTTPS

   Submits credentials
"""
        result = parse_dynamic_step_content(content)

        assert result is not None
        assert result.slug == "login-step-1"
        assert result.sequence_name == "user-login"
        assert result.step_number == 1
        assert result.source_type == "person"


class TestDynamicStepRoundTrip:
    """Test serialize -> parse round-trip for dynamic steps."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Test simple round-trip."""
        original = DynamicStep(
            slug="round-trip-step",
            sequence_name="test-sequence",
            step_number=1,
            source_type=ElementType.CONTAINER,
            source_slug="container-a",
            destination_type=ElementType.CONTAINER,
            destination_slug="container-b",
            description="Requests data",
            technology="gRPC",
        )

        content = serialize_dynamic_step(original)
        file_path = tmp_path / "round-trip.rst"
        file_path.write_text(content)

        parsed = parse_dynamic_step_file(file_path)

        assert parsed is not None
        assert parsed.slug == original.slug
        assert parsed.sequence_name == original.sequence_name
        assert parsed.step_number == original.step_number

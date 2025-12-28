"""Tests for C4 bridge use case and renderer."""


from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App, AppType
from julee.hcd.entities.persona import Persona
from julee.hcd.infrastructure.renderers import C4PlantUMLRenderer
from julee.hcd.use_cases.c4_bridge import (
    C4Container,
    C4ContainerDiagramData,
    C4Person,
    C4Relationship,
    generate_c4_container_diagram,
)


class TestGenerateC4ContainerDiagram:
    """Test C4 diagram data generation."""

    def test_empty_entities_returns_empty_diagram(self) -> None:
        """Test with no entities returns empty diagram data."""
        diagram = generate_c4_container_diagram(
            apps=[],
            accelerators=[],
            contribs=[],
            personas=[],
        )

        assert diagram.title == "Container Diagram"
        assert diagram.system_name == "System"
        assert len(diagram.containers) == 0
        assert len(diagram.persons) == 0
        assert len(diagram.relationships) == 0

    def test_apps_become_containers(self) -> None:
        """Test apps are converted to containers."""
        app = App(
            slug="test-app",
            name="Test App",
            description="A test application",
            app_type=AppType.STAFF,
            accelerators=[],
        )

        diagram = generate_c4_container_diagram(
            apps=[app],
            accelerators=[],
            contribs=[],
            personas=[],
        )

        assert len(diagram.containers) == 1
        container = diagram.containers[0]
        assert container.id == "test_app"
        assert container.name == "Test App"
        assert container.container_type == "app"

    def test_accelerators_become_containers(self) -> None:
        """Test accelerators are converted to containers."""
        accel = Accelerator(
            slug="test-accel",
            name="Test Accelerator",
            objective="Test objective",
            technology="Python",
        )

        diagram = generate_c4_container_diagram(
            apps=[],
            accelerators=[accel],
            contribs=[],
            personas=[],
        )

        assert len(diagram.containers) == 1
        container = diagram.containers[0]
        assert container.id == "test_accel"
        assert container.container_type == "accelerator"

    def test_personas_with_relationships_become_persons(self) -> None:
        """Test personas with app references become persons."""
        persona = Persona(
            name="Test User",
            app_slugs=["test-app"],
        )

        diagram = generate_c4_container_diagram(
            apps=[],
            accelerators=[],
            contribs=[],
            personas=[persona],
        )

        assert len(diagram.persons) == 1
        assert diagram.persons[0].name == "Test User"

    def test_personas_without_relationships_excluded(self) -> None:
        """Test personas without relationships are excluded."""
        persona = Persona(
            name="Isolated User",
            app_slugs=[],
        )

        diagram = generate_c4_container_diagram(
            apps=[],
            accelerators=[],
            contribs=[],
            personas=[persona],
        )

        assert len(diagram.persons) == 0

    def test_foundation_layer_added_when_enabled(self) -> None:
        """Test foundation container added when show_foundation=True."""
        diagram = generate_c4_container_diagram(
            apps=[],
            accelerators=[],
            contribs=[],
            personas=[],
            show_foundation=True,
            foundation_name="Core Foundation",
        )

        foundation = [c for c in diagram.containers if c.container_type == "foundation"]
        assert len(foundation) == 1
        assert foundation[0].name == "Core Foundation"

    def test_external_systems_added_when_enabled(self) -> None:
        """Test external systems added when show_external=True."""
        diagram = generate_c4_container_diagram(
            apps=[],
            accelerators=[],
            contribs=[],
            personas=[],
            show_external=True,
            external_name="Third Party APIs",
        )

        assert len(diagram.external_systems) == 1
        assert diagram.external_systems[0][1] == "Third Party APIs"

    def test_app_to_accelerator_relationships(self) -> None:
        """Test relationships created from apps to accelerators."""
        app = App(
            slug="my-app",
            name="My App",
            app_type=AppType.STAFF,
            accelerators=["my-accel"],
        )
        accel = Accelerator(
            slug="my-accel",
            name="My Accelerator",
            technology="Python",
        )

        diagram = generate_c4_container_diagram(
            apps=[app],
            accelerators=[accel],
            contribs=[],
            personas=[],
        )

        app_to_accel = [r for r in diagram.relationships if r.source_id == "my_app"]
        assert len(app_to_accel) == 1
        assert app_to_accel[0].target_id == "my_accel"


class TestC4PlantUMLRenderer:
    """Test PlantUML rendering."""

    def test_render_empty_diagram(self) -> None:
        """Test rendering empty diagram produces valid PlantUML."""
        diagram = C4ContainerDiagramData(
            title="Test Diagram",
            system_name="Test System",
        )

        renderer = C4PlantUMLRenderer()
        output = renderer.render(diagram)

        assert "@startuml" in output
        assert "@enduml" in output
        assert "!include <C4/C4_Container>" in output
        assert "title Test Diagram" in output
        assert 'System_Boundary(Test_System, "Test System")' in output

    def test_render_with_persons(self) -> None:
        """Test rendering persons outside system boundary."""
        diagram = C4ContainerDiagramData(
            title="Test",
            system_name="System",
            persons=[
                C4Person(id="user1", name="User One", description="A user"),
            ],
        )

        renderer = C4PlantUMLRenderer()
        output = renderer.render(diagram)

        assert 'Person(user1, "User One", "A user")' in output

    def test_render_with_containers(self) -> None:
        """Test rendering containers inside system boundary."""
        diagram = C4ContainerDiagramData(
            title="Test",
            system_name="System",
            containers=[
                C4Container(
                    id="app1",
                    name="App One",
                    technology="Python",
                    description="An application",
                    container_type="app",
                ),
            ],
        )

        renderer = C4PlantUMLRenderer()
        output = renderer.render(diagram)

        assert 'Container(app1, "App One", "Python", "An application")' in output

    def test_render_with_relationships(self) -> None:
        """Test rendering relationships."""
        diagram = C4ContainerDiagramData(
            title="Test",
            system_name="System",
            relationships=[
                C4Relationship(source_id="a", target_id="b", label="Uses"),
            ],
        )

        renderer = C4PlantUMLRenderer()
        output = renderer.render(diagram)

        assert 'Rel(a, b, "Uses")' in output

    def test_render_with_external_systems(self) -> None:
        """Test rendering external systems."""
        diagram = C4ContainerDiagramData(
            title="Test",
            system_name="System",
            external_systems=[("ext", "External API", "Third party")],
        )

        renderer = C4PlantUMLRenderer()
        output = renderer.render(diagram)

        assert 'System_Ext(ext, "External API", "Third party")' in output

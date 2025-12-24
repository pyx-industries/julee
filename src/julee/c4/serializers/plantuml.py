"""PlantUML C4 serializer.

Generates C4-PlantUML syntax from diagram data.

Reference: https://github.com/plantuml-stdlib/C4-PlantUML
"""

from julee.c4.entities.diagrams import (
    ComponentDiagram,
    ContainerDiagram,
    DeploymentDiagram,
    DynamicDiagram,
    SystemContextDiagram,
    SystemLandscapeDiagram,
)
from julee.c4.entities.relationship import ElementType


class PlantUMLSerializer:
    """Serializer for C4-PlantUML output format."""

    def __init__(self) -> None:
        """Initialize the serializer."""
        pass

    def _header(self, diagram_type: str) -> str:
        """Generate PlantUML header with C4 includes.

        Args:
            diagram_type: Type of C4 diagram (Context, Container, Component, etc.)

        Returns:
            PlantUML header with appropriate includes
        """
        includes = {
            "Context": "C4_Context",
            "Container": "C4_Container",
            "Component": "C4_Component",
            "Deployment": "C4_Deployment",
            "Dynamic": "C4_Dynamic",
            "Landscape": "C4_Context",
        }
        include_name = includes.get(diagram_type, "C4_Context")
        # Use PlantUML stdlib format (works with standard PlantUML installation)
        return f"""@startuml
!include <C4/{include_name}>

"""

    def _footer(self) -> str:
        """Generate PlantUML footer."""
        return "\n@enduml\n"

    def _escape(self, text: str) -> str:
        """Escape special characters for PlantUML."""
        return text.replace('"', '\\"').replace("\n", "\\n")

    def _id(self, slug: str) -> str:
        """Convert slug to valid PlantUML identifier (no hyphens)."""
        return slug.replace("-", "_")

    def _element_type_to_func(self, element_type: ElementType) -> str:
        """Map element type to PlantUML function name."""
        mapping = {
            ElementType.PERSON: "Person",
            ElementType.SOFTWARE_SYSTEM: "System",
            ElementType.CONTAINER: "Container",
            ElementType.COMPONENT: "Component",
        }
        return mapping.get(element_type, "System")

    def serialize_system_context(
        self, data: SystemContextDiagram, title: str = ""
    ) -> str:
        """Serialize system context diagram to PlantUML.

        Args:
            data: System context diagram data
            title: Optional diagram title

        Returns:
            PlantUML C4 Context diagram
        """
        lines = [self._header("Context")]

        if title:
            lines.append(f'title "{self._escape(title)}"')
            lines.append("")

        # Persons - use enriched data if available, fall back to slugs
        person_by_slug = {p.slug: p for p in data.persons}
        for slug in data.person_slugs:
            pid = self._id(slug)
            if slug in person_by_slug:
                person = person_by_slug[slug]
                if person.description:
                    lines.append(
                        f'Person({pid}, "{self._escape(person.name)}", '
                        f'"{self._escape(person.description)}")'
                    )
                else:
                    lines.append(f'Person({pid}, "{self._escape(person.name)}")')
            else:
                lines.append(f'Person({pid}, "{slug}")')

        # Main system (internal)
        system = data.system
        lines.append(
            f'System({self._id(system.slug)}, "{self._escape(system.name)}", '
            f'"{self._escape(system.description)}")'
        )

        # External systems
        for ext_sys in data.external_systems:
            lines.append(
                f'System_Ext({self._id(ext_sys.slug)}, "{self._escape(ext_sys.name)}", '
                f'"{self._escape(ext_sys.description)}")'
            )

        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = self._id(rel.source_slug)
            dst = self._id(rel.destination_slug)
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'Rel({src}, {dst}, "{desc}", "{rel.technology}")')
            else:
                lines.append(f'Rel({src}, {dst}, "{desc}")')

        lines.append(self._footer())
        return "\n".join(lines)

    def serialize_container_diagram(
        self, data: ContainerDiagram, title: str = ""
    ) -> str:
        """Serialize container diagram to PlantUML.

        Args:
            data: Container diagram data
            title: Optional diagram title

        Returns:
            PlantUML C4 Container diagram
        """
        lines = [self._header("Container")]

        if title:
            lines.append(f'title "{self._escape(title)}"')
            lines.append("")

        # Persons
        for slug in data.person_slugs:
            lines.append(f'Person({slug}, "{slug}")')

        # External systems
        for ext_sys in data.external_systems:
            lines.append(
                f'System_Ext({ext_sys.slug}, "{self._escape(ext_sys.name)}", '
                f'"{self._escape(ext_sys.description)}")'
            )

        lines.append("")

        # System boundary with containers
        system = data.system
        lines.append(
            f'System_Boundary({system.slug}, "{self._escape(system.name)}") {{'
        )

        for container in data.containers:
            tech = container.technology
            desc = self._escape(container.description)

            if container.is_data_store:
                lines.append(
                    f'    ContainerDb({container.slug}, "{self._escape(container.name)}", '
                    f'"{tech}", "{desc}")'
                )
            else:
                lines.append(
                    f'    Container({container.slug}, "{self._escape(container.name)}", '
                    f'"{tech}", "{desc}")'
                )

        lines.append("}")
        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'Rel({src}, {dst}, "{desc}", "{rel.technology}")')
            else:
                lines.append(f'Rel({src}, {dst}, "{desc}")')

        lines.append(self._footer())
        return "\n".join(lines)

    def serialize_component_diagram(
        self, data: ComponentDiagram, title: str = ""
    ) -> str:
        """Serialize component diagram to PlantUML.

        Args:
            data: Component diagram data
            title: Optional diagram title

        Returns:
            PlantUML C4 Component diagram
        """
        lines = [self._header("Component")]

        if title:
            lines.append(f'title "{self._escape(title)}"')
            lines.append("")

        # Persons
        for slug in data.person_slugs:
            lines.append(f'Person({slug}, "{slug}")')

        # External systems
        for ext_sys in data.external_systems:
            lines.append(
                f'System_Ext({ext_sys.slug}, "{self._escape(ext_sys.name)}", '
                f'"{self._escape(ext_sys.description)}")'
            )

        # External containers
        for ext_cont in data.external_containers:
            lines.append(
                f'Container({ext_cont.slug}, "{self._escape(ext_cont.name)}", '
                f'"{ext_cont.technology}", "{self._escape(ext_cont.description)}")'
            )

        lines.append("")

        # Container boundary with components
        container = data.container
        lines.append(
            f'Container_Boundary({container.slug}, "{self._escape(container.name)}") {{'
        )

        for component in data.components:
            tech = component.technology
            desc = self._escape(component.description)
            lines.append(
                f'    Component({component.slug}, "{self._escape(component.name)}", '
                f'"{tech}", "{desc}")'
            )

        lines.append("}")
        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'Rel({src}, {dst}, "{desc}", "{rel.technology}")')
            else:
                lines.append(f'Rel({src}, {dst}, "{desc}")')

        lines.append(self._footer())
        return "\n".join(lines)

    def serialize_system_landscape(
        self, data: SystemLandscapeDiagram, title: str = ""
    ) -> str:
        """Serialize system landscape diagram to PlantUML.

        Args:
            data: System landscape diagram data
            title: Optional diagram title

        Returns:
            PlantUML C4 System Landscape diagram
        """
        lines = [self._header("Landscape")]

        if title:
            lines.append(f'title "{self._escape(title)}"')
            lines.append("")

        # Persons
        for slug in data.person_slugs:
            lines.append(f'Person({slug}, "{slug}")')

        lines.append("")

        # All systems
        for system in data.systems:
            if system.system_type.value == "external":
                lines.append(
                    f'System_Ext({system.slug}, "{self._escape(system.name)}", '
                    f'"{self._escape(system.description)}")'
                )
            else:
                lines.append(
                    f'System({system.slug}, "{self._escape(system.name)}", '
                    f'"{self._escape(system.description)}")'
                )

        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'Rel({src}, {dst}, "{desc}", "{rel.technology}")')
            else:
                lines.append(f'Rel({src}, {dst}, "{desc}")')

        lines.append(self._footer())
        return "\n".join(lines)

    def serialize_deployment_diagram(
        self, data: DeploymentDiagram, title: str = ""
    ) -> str:
        """Serialize deployment diagram to PlantUML.

        Args:
            data: Deployment diagram data
            title: Optional diagram title

        Returns:
            PlantUML C4 Deployment diagram
        """
        lines = [self._header("Deployment")]

        if title:
            lines.append(f'title "{self._escape(title)}"')
            lines.append("")

        lines.append(f'Deployment_Node(env, "{data.environment}") {{')

        # Build node hierarchy
        root_nodes = [n for n in data.nodes if not n.parent_slug]

        def render_node(node, indent=1):
            """Recursively render node and children."""
            prefix = "    " * indent
            tech = node.technology or ""
            lines.append(
                f'{prefix}Deployment_Node({node.slug}, "{self._escape(node.name)}", '
                f'"{tech}") {{'
            )

            # Container instances
            for instance in node.container_instances:
                cont_slug = instance.container_slug
                instance_id = instance.instance_id or ""
                lines.append(
                    f'{prefix}    Container({cont_slug}_{instance_id or "1"}, '
                    f'"{cont_slug}", "{instance_id}")'
                )

            # Child nodes
            children = [n for n in data.nodes if n.parent_slug == node.slug]
            for child in children:
                render_node(child, indent + 1)

            lines.append(f"{prefix}}}")

        for node in root_nodes:
            render_node(node)

        lines.append("}")
        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'Rel({src}, {dst}, "{desc}", "{rel.technology}")')
            else:
                lines.append(f'Rel({src}, {dst}, "{desc}")')

        lines.append(self._footer())
        return "\n".join(lines)

    def serialize_dynamic_diagram(self, data: DynamicDiagram, title: str = "") -> str:
        """Serialize dynamic diagram to PlantUML.

        Args:
            data: Dynamic diagram data
            title: Optional diagram title

        Returns:
            PlantUML C4 Dynamic (sequence) diagram
        """
        lines = [self._header("Dynamic")]

        if title:
            lines.append(f'title "{self._escape(title)}"')
            lines.append("")

        # Declare all participants
        for slug in data.person_slugs:
            lines.append(f'Person({slug}, "{slug}")')

        for system in data.systems:
            lines.append(f'System({system.slug}, "{self._escape(system.name)}")')

        for container in data.containers:
            lines.append(
                f'Container({container.slug}, "{self._escape(container.name)}")'
            )

        for component in data.components:
            lines.append(
                f'Component({component.slug}, "{self._escape(component.name)}")'
            )

        lines.append("")

        # Numbered sequence steps
        for step in data.steps:
            src = step.source_slug
            dst = step.destination_slug
            desc = self._escape(step.description)
            step_num = step.step_number

            if step.technology:
                lines.append(
                    f'Rel({src}, {dst}, "{step_num}. {desc}", "{step.technology}")'
                )
            else:
                lines.append(f'Rel({src}, {dst}, "{step_num}. {desc}")')

            # Return step if specified
            if step.is_return and step.return_description:
                ret_desc = self._escape(step.return_description)
                lines.append(f'Rel({dst}, {src}, "{ret_desc}")')

        lines.append(self._footer())
        return "\n".join(lines)

"""Structurizr DSL serializer.

Generates Structurizr DSL from diagram data.

Reference: https://structurizr.com/dsl
"""

from julee.c4.entities.diagrams import (
    ComponentDiagram,
    ContainerDiagram,
    DeploymentDiagram,
    DynamicDiagram,
    SystemContextDiagram,
    SystemLandscapeDiagram,
)


class StructurizrSerializer:
    """Serializer for Structurizr DSL output format."""

    def __init__(self) -> None:
        """Initialize the serializer."""
        pass

    def _escape(self, text: str) -> str:
        """Escape special characters for Structurizr DSL."""
        return text.replace('"', '\\"').replace("\n", " ")

    def _indent(self, text: str, level: int = 1) -> str:
        """Indent text by specified level."""
        prefix = "    " * level
        return "\n".join(prefix + line for line in text.split("\n"))

    def serialize_system_context(
        self, data: SystemContextDiagram, title: str = ""
    ) -> str:
        """Serialize system context diagram to Structurizr DSL.

        Note: Structurizr DSL defines models, not diagrams directly.
        This generates a workspace with model and views.

        Args:
            data: System context diagram data
            title: Optional diagram title

        Returns:
            Structurizr DSL workspace
        """
        lines = ["workspace {", "", "    model {"]

        # Persons
        for slug in data.person_slugs:
            lines.append(f'        {slug} = person "{slug}"')

        # Main system
        system = data.system
        lines.append(
            f'        {system.slug} = softwareSystem "{self._escape(system.name)}" '
            f'"{self._escape(system.description)}"'
        )

        # External systems
        for ext_sys in data.external_systems:
            lines.append(
                f'        {ext_sys.slug} = softwareSystem "{self._escape(ext_sys.name)}" '
                f'"{self._escape(ext_sys.description)}" {{',
            )
            lines.append('            tags "External"')
            lines.append("        }")

        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'        {src} -> {dst} "{desc}" "{rel.technology}"')
            else:
                lines.append(f'        {src} -> {dst} "{desc}"')

        lines.append("    }")
        lines.append("")

        # Views
        lines.append("    views {")
        view_title = title or f"System Context for {system.name}"
        lines.append(
            f'        systemContext {system.slug} "{self._escape(view_title)}" {{'
        )
        lines.append("            include *")
        lines.append("            autoLayout")
        lines.append("        }")
        lines.append("    }")

        lines.append("}")
        return "\n".join(lines)

    def serialize_container_diagram(
        self, data: ContainerDiagram, title: str = ""
    ) -> str:
        """Serialize container diagram to Structurizr DSL.

        Args:
            data: Container diagram data
            title: Optional diagram title

        Returns:
            Structurizr DSL workspace
        """
        lines = ["workspace {", "", "    model {"]

        # Persons
        for slug in data.person_slugs:
            lines.append(f'        {slug} = person "{slug}"')

        # External systems
        for ext_sys in data.external_systems:
            lines.append(
                f'        {ext_sys.slug} = softwareSystem "{self._escape(ext_sys.name)}" '
                f'"{self._escape(ext_sys.description)}" {{',
            )
            lines.append('            tags "External"')
            lines.append("        }")

        # Main system with containers
        system = data.system
        lines.append(
            f'        {system.slug} = softwareSystem "{self._escape(system.name)}" '
            f'"{self._escape(system.description)}" {{'
        )

        for container in data.containers:
            desc = self._escape(container.description)
            tech = container.technology

            if container.is_data_store:
                lines.append(
                    f"            {container.slug} = container "
                    f'"{self._escape(container.name)}" "{desc}" "{tech}" {{'
                )
                lines.append('                tags "Database"')
                lines.append("            }")
            else:
                lines.append(
                    f"            {container.slug} = container "
                    f'"{self._escape(container.name)}" "{desc}" "{tech}"'
                )

        lines.append("        }")
        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'        {src} -> {dst} "{desc}" "{rel.technology}"')
            else:
                lines.append(f'        {src} -> {dst} "{desc}"')

        lines.append("    }")
        lines.append("")

        # Views
        lines.append("    views {")
        view_title = title or f"Containers for {system.name}"
        lines.append(f'        container {system.slug} "{self._escape(view_title)}" {{')
        lines.append("            include *")
        lines.append("            autoLayout")
        lines.append("        }")
        lines.append("    }")

        lines.append("}")
        return "\n".join(lines)

    def serialize_component_diagram(
        self, data: ComponentDiagram, title: str = ""
    ) -> str:
        """Serialize component diagram to Structurizr DSL.

        Args:
            data: Component diagram data
            title: Optional diagram title

        Returns:
            Structurizr DSL workspace
        """
        lines = ["workspace {", "", "    model {"]

        # Persons
        for slug in data.person_slugs:
            lines.append(f'        {slug} = person "{slug}"')

        # External systems
        for ext_sys in data.external_systems:
            lines.append(
                f'        {ext_sys.slug} = softwareSystem "{self._escape(ext_sys.name)}" {{',
            )
            lines.append('            tags "External"')
            lines.append("        }")

        # Main system with container and components
        system = data.system
        container = data.container

        lines.append(
            f'        {system.slug} = softwareSystem "{self._escape(system.name)}" {{'
        )

        # External containers (from same system)
        for ext_cont in data.external_containers:
            lines.append(
                f"            {ext_cont.slug} = container "
                f'"{self._escape(ext_cont.name)}" "{self._escape(ext_cont.description)}" '
                f'"{ext_cont.technology}"'
            )

        # Main container with components
        lines.append(
            f"            {container.slug} = container "
            f'"{self._escape(container.name)}" "{self._escape(container.description)}" '
            f'"{container.technology}" {{'
        )

        for component in data.components:
            desc = self._escape(component.description)
            tech = component.technology
            lines.append(
                f"                {component.slug} = component "
                f'"{self._escape(component.name)}" "{desc}" "{tech}"'
            )

        lines.append("            }")
        lines.append("        }")
        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'        {src} -> {dst} "{desc}" "{rel.technology}"')
            else:
                lines.append(f'        {src} -> {dst} "{desc}"')

        lines.append("    }")
        lines.append("")

        # Views
        lines.append("    views {")
        view_title = title or f"Components for {container.name}"
        lines.append(
            f'        component {container.slug} "{self._escape(view_title)}" {{'
        )
        lines.append("            include *")
        lines.append("            autoLayout")
        lines.append("        }")
        lines.append("    }")

        lines.append("}")
        return "\n".join(lines)

    def serialize_system_landscape(
        self, data: SystemLandscapeDiagram, title: str = ""
    ) -> str:
        """Serialize system landscape diagram to Structurizr DSL.

        Args:
            data: System landscape diagram data
            title: Optional diagram title

        Returns:
            Structurizr DSL workspace
        """
        lines = ["workspace {", "", "    model {"]

        # Persons
        for slug in data.person_slugs:
            lines.append(f'        {slug} = person "{slug}"')

        # All systems
        for system in data.systems:
            desc = self._escape(system.description)
            if system.system_type.value == "external":
                lines.append(
                    f"        {system.slug} = softwareSystem "
                    f'"{self._escape(system.name)}" "{desc}" {{'
                )
                lines.append('            tags "External"')
                lines.append("        }")
            else:
                lines.append(
                    f"        {system.slug} = softwareSystem "
                    f'"{self._escape(system.name)}" "{desc}"'
                )

        lines.append("")

        # Relationships
        for rel in data.relationships:
            src = rel.source_slug
            dst = rel.destination_slug
            desc = self._escape(rel.description)
            if rel.technology:
                lines.append(f'        {src} -> {dst} "{desc}" "{rel.technology}"')
            else:
                lines.append(f'        {src} -> {dst} "{desc}"')

        lines.append("    }")
        lines.append("")

        # Views
        lines.append("    views {")
        view_title = title or "System Landscape"
        lines.append(f'        systemLandscape "{self._escape(view_title)}" {{')
        lines.append("            include *")
        lines.append("            autoLayout")
        lines.append("        }")
        lines.append("    }")

        lines.append("}")
        return "\n".join(lines)

    def serialize_deployment_diagram(
        self, data: DeploymentDiagram, title: str = ""
    ) -> str:
        """Serialize deployment diagram to Structurizr DSL.

        Args:
            data: Deployment diagram data
            title: Optional diagram title

        Returns:
            Structurizr DSL workspace
        """
        lines = ["workspace {", "", "    model {"]

        # Define containers first (as placeholders)
        container_slugs = {c.slug for c in data.containers}
        if container_slugs:
            lines.append('        system = softwareSystem "System" {')
            for container in data.containers:
                lines.append(
                    f"            {container.slug} = container "
                    f'"{self._escape(container.name)}"'
                )
            lines.append("        }")
            lines.append("")

        # Deployment environment
        env = data.environment
        lines.append(f'        {env} = deploymentEnvironment "{env}" {{')

        def render_node(node, indent=3):
            """Recursively render deployment nodes."""
            prefix = "    " * indent
            tech = node.technology or ""

            lines.append(
                f'{prefix}deploymentNode "{self._escape(node.name)}" "{tech}" {{'
            )

            # Container instances
            for instance in node.container_instances:
                cont_slug = instance.container_slug
                lines.append(f"{prefix}    containerInstance {cont_slug}")

            # Child nodes
            children = [n for n in data.nodes if n.parent_slug == node.slug]
            for child in children:
                render_node(child, indent + 1)

            lines.append(f"{prefix}}}")

        root_nodes = [n for n in data.nodes if not n.parent_slug]
        for node in root_nodes:
            render_node(node)

        lines.append("        }")
        lines.append("    }")
        lines.append("")

        # Views
        lines.append("    views {")
        view_title = title or f"Deployment - {env}"
        lines.append(f'        deployment * {env} "{self._escape(view_title)}" {{')
        lines.append("            include *")
        lines.append("            autoLayout")
        lines.append("        }")
        lines.append("    }")

        lines.append("}")
        return "\n".join(lines)

    def serialize_dynamic_diagram(self, data: DynamicDiagram, title: str = "") -> str:
        """Serialize dynamic diagram to Structurizr DSL.

        Note: Structurizr dynamic views have limited DSL support.
        This generates a basic representation.

        Args:
            data: Dynamic diagram data
            title: Optional diagram title

        Returns:
            Structurizr DSL workspace
        """
        lines = ["workspace {", "", "    model {"]

        # Persons
        for slug in data.person_slugs:
            lines.append(f'        {slug} = person "{slug}"')

        # Systems
        for system in data.systems:
            lines.append(
                f'        {system.slug} = softwareSystem "{self._escape(system.name)}"'
            )

        # Build container/component hierarchy
        if data.containers:
            lines.append('        system = softwareSystem "System" {')
            for container in data.containers:
                if data.components and any(
                    c.container_slug == container.slug for c in data.components
                ):
                    lines.append(
                        f"            {container.slug} = container "
                        f'"{self._escape(container.name)}" {{'
                    )
                    for component in data.components:
                        if component.container_slug == container.slug:
                            lines.append(
                                f"                {component.slug} = component "
                                f'"{self._escape(component.name)}"'
                            )
                    lines.append("            }")
                else:
                    lines.append(
                        f"            {container.slug} = container "
                        f'"{self._escape(container.name)}"'
                    )
            lines.append("        }")

        lines.append("")

        # Relationships from steps
        for step in data.steps:
            src = step.source_slug
            dst = step.destination_slug
            desc = self._escape(f"{step.step_number}. {step.description}")
            if step.technology:
                lines.append(f'        {src} -> {dst} "{desc}" "{step.technology}"')
            else:
                lines.append(f'        {src} -> {dst} "{desc}"')

        lines.append("    }")
        lines.append("")

        # Dynamic view
        lines.append("    views {")
        view_title = title or f"Dynamic - {data.sequence_name}"
        lines.append(f'        dynamic * "{self._escape(view_title)}" {{')

        # Steps in order
        for step in data.steps:
            src = step.source_slug
            dst = step.destination_slug
            desc = self._escape(step.description)
            lines.append(f'            {src} -> {dst} "{desc}"')

        lines.append("            autoLayout")
        lines.append("        }")
        lines.append("    }")

        lines.append("}")
        return "\n".join(lines)

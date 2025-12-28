"""PlantUML renderers for C4 diagrams.

Converts C4 diagram data into PlantUML source code.
"""

from julee.hcd.use_cases.c4_bridge import C4ContainerDiagramData


class C4PlantUMLRenderer:
    """Renders C4 container diagrams as PlantUML source."""

    def render(self, diagram: C4ContainerDiagramData) -> str:
        """Render a C4 container diagram to PlantUML source.

        Args:
            diagram: C4ContainerDiagramData with diagram elements

        Returns:
            PlantUML source string
        """
        lines = [
            "@startuml",
            "!include <C4/C4_Container>",
            "",
            f"title {diagram.title}",
            "",
        ]

        # Render persons (outside system boundary)
        for person in diagram.persons:
            lines.append(
                f'Person({person.id}, "{person.name}", "{person.description}")'
            )
        if diagram.persons:
            lines.append("")

        # System boundary
        system_id = diagram.system_name.replace(" ", "_").replace("-", "_")
        lines.append(f'System_Boundary({system_id}, "{diagram.system_name}") {{')
        lines.append("")

        # Render containers grouped by type
        container_types = ["app", "accelerator", "contrib", "foundation"]
        for ctype in container_types:
            typed_containers = [c for c in diagram.containers if c.container_type == ctype]
            for container in typed_containers:
                lines.append(
                    f'   Container({container.id}, "{container.name}", '
                    f'"{container.technology}", "{container.description}")'
                )
            if typed_containers:
                lines.append("")

        lines.append("}")  # End system boundary
        lines.append("")

        # External systems
        for ext_id, ext_name, ext_desc in diagram.external_systems:
            lines.append(f'System_Ext({ext_id}, "{ext_name}", "{ext_desc}")')
        if diagram.external_systems:
            lines.append("")

        # Render relationships
        for rel in diagram.relationships:
            lines.append(f'Rel({rel.source_id}, {rel.target_id}, "{rel.label}")')
        lines.append("")

        lines.append("@enduml")

        return "\n".join(lines)

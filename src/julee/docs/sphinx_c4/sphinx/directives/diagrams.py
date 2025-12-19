"""Diagram directives for C4 Sphinx integration.

Provides directives for generating C4 diagrams using PlantUML.
"""

from docutils import nodes
from docutils.parsers.rst import directives

from ...serializers.plantuml import PlantUMLSerializer
from .base import C4Directive


class DiagramDirective(C4Directive):
    """Base class for diagram directives."""

    option_spec = {
        "title": directives.unchanged,
        "format": directives.unchanged,
    }

    def get_serializer(self) -> PlantUMLSerializer:
        """Get the PlantUML serializer."""
        return PlantUMLSerializer()

    def make_plantuml_node(self, puml_source: str) -> nodes.Node:
        """Create a PlantUML node or fallback to literal block.

        Args:
            puml_source: PlantUML source code

        Returns:
            PlantUML node or literal block
        """
        try:
            from sphinxcontrib.plantuml import plantuml

            node = plantuml(puml_source)
            node["uml"] = puml_source
            return node
        except ImportError:
            # Fallback to literal block if PlantUML not available
            return nodes.literal_block(puml_source, puml_source)


class SystemContextDiagramDirective(DiagramDirective):
    """Generate a system context diagram.

    Usage::

        .. system-context-diagram:: banking-system
           :title: Banking System Context

    Shows the software system in its environment with users and external systems.
    """

    required_arguments = 1
    has_content = False

    def run(self) -> list[nodes.Node]:
        system_slug = self.arguments[0]
        title = self.options.get("title", f"System Context: {system_slug}")

        storage = self.get_c4_storage()
        system = storage["software_systems"].get(system_slug)

        if not system:
            return self.empty_result(f"Software system '{system_slug}' not found")

        # Gather relationships involving this system
        relationships = [
            r for r in storage["relationships"].values()
            if r.involves_element_by_slug(system_slug)
        ]

        # Gather external systems
        external_systems = []
        person_slugs = []
        for rel in relationships:
            for el_type, el_slug in [
                (rel.source_type, rel.source_slug),
                (rel.destination_type, rel.destination_slug),
            ]:
                if el_slug == system_slug:
                    continue
                if el_type.value == "software_system":
                    ext_sys = storage["software_systems"].get(el_slug)
                    if ext_sys and ext_sys not in external_systems:
                        external_systems.append(ext_sys)
                elif el_type.value == "person":
                    if el_slug not in person_slugs:
                        person_slugs.append(el_slug)

        # Build diagram data
        from ...domain.use_cases.diagrams.system_context import SystemContextDiagramData

        data = SystemContextDiagramData(
            system=system,
            external_systems=external_systems,
            person_slugs=person_slugs,
            relationships=relationships,
        )

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_system_context(data, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml))
        return result_nodes


class ContainerDiagramDirective(DiagramDirective):
    """Generate a container diagram.

    Usage::

        .. container-diagram:: banking-system
           :title: Banking System Containers

    Shows containers within a software system.
    """

    required_arguments = 1
    has_content = False

    def run(self) -> list[nodes.Node]:
        system_slug = self.arguments[0]
        title = self.options.get("title", f"Containers: {system_slug}")

        storage = self.get_c4_storage()
        system = storage["software_systems"].get(system_slug)

        if not system:
            return self.empty_result(f"Software system '{system_slug}' not found")

        # Gather containers for this system
        containers = [
            c for c in storage["containers"].values()
            if c.system_slug == system_slug
        ]

        # Gather relationships
        container_slugs = {c.slug for c in containers}
        relationships = []
        external_systems = []
        person_slugs = []

        for rel in storage["relationships"].values():
            if rel.source_slug in container_slugs or rel.destination_slug in container_slugs:
                relationships.append(rel)

                for el_type, el_slug in [
                    (rel.source_type, rel.source_slug),
                    (rel.destination_type, rel.destination_slug),
                ]:
                    if el_slug in container_slugs:
                        continue
                    if el_type.value == "software_system":
                        ext_sys = storage["software_systems"].get(el_slug)
                        if ext_sys and ext_sys not in external_systems:
                            external_systems.append(ext_sys)
                    elif el_type.value == "person":
                        if el_slug not in person_slugs:
                            person_slugs.append(el_slug)

        # Build diagram data
        from ...domain.use_cases.diagrams.container_diagram import ContainerDiagramData

        data = ContainerDiagramData(
            system=system,
            containers=containers,
            external_systems=external_systems,
            person_slugs=person_slugs,
            relationships=relationships,
        )

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_container_diagram(data, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml))
        return result_nodes


class ComponentDiagramDirective(DiagramDirective):
    """Generate a component diagram.

    Usage::

        .. component-diagram:: api-app
           :title: API Application Components

    Shows components within a container.
    """

    required_arguments = 1
    has_content = False

    def run(self) -> list[nodes.Node]:
        container_slug = self.arguments[0]
        title = self.options.get("title", f"Components: {container_slug}")

        storage = self.get_c4_storage()
        container = storage["containers"].get(container_slug)

        if not container:
            return self.empty_result(f"Container '{container_slug}' not found")

        system = storage["software_systems"].get(container.system_slug)
        if not system:
            return self.empty_result(f"System '{container.system_slug}' not found")

        # Gather components for this container
        components = [
            c for c in storage["components"].values()
            if c.container_slug == container_slug
        ]

        # Gather relationships
        component_slugs = {c.slug for c in components}
        relationships = []
        external_containers = []
        external_systems = []
        person_slugs = []

        for rel in storage["relationships"].values():
            if rel.source_slug in component_slugs or rel.destination_slug in component_slugs:
                relationships.append(rel)

                for el_type, el_slug in [
                    (rel.source_type, rel.source_slug),
                    (rel.destination_type, rel.destination_slug),
                ]:
                    if el_slug in component_slugs:
                        continue
                    if el_type.value == "container":
                        ext_cont = storage["containers"].get(el_slug)
                        if ext_cont and ext_cont not in external_containers:
                            external_containers.append(ext_cont)
                    elif el_type.value == "software_system":
                        ext_sys = storage["software_systems"].get(el_slug)
                        if ext_sys and ext_sys not in external_systems:
                            external_systems.append(ext_sys)
                    elif el_type.value == "person":
                        if el_slug not in person_slugs:
                            person_slugs.append(el_slug)

        # Build diagram data
        from ...domain.use_cases.diagrams.component_diagram import ComponentDiagramData

        data = ComponentDiagramData(
            system=system,
            container=container,
            components=components,
            external_containers=external_containers,
            external_systems=external_systems,
            person_slugs=person_slugs,
            relationships=relationships,
        )

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_component_diagram(data, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml))
        return result_nodes


class SystemLandscapeDiagramDirective(DiagramDirective):
    """Generate a system landscape diagram.

    Usage::

        .. system-landscape-diagram::
           :title: Enterprise System Landscape

    Shows all software systems and their relationships.
    """

    has_content = False

    def run(self) -> list[nodes.Node]:
        title = self.options.get("title", "System Landscape")

        storage = self.get_c4_storage()
        systems = list(storage["software_systems"].values())

        if not systems:
            return self.empty_result("No software systems defined")

        # Gather person relationships and cross-system relationships
        relationships = []
        person_slugs = []

        for rel in storage["relationships"].values():
            is_system_rel = (
                rel.source_type.value == "software_system"
                or rel.destination_type.value == "software_system"
            )
            is_person_rel = (
                rel.source_type.value == "person"
                or rel.destination_type.value == "person"
            )

            if is_system_rel or is_person_rel:
                relationships.append(rel)

            if rel.source_type.value == "person":
                if rel.source_slug not in person_slugs:
                    person_slugs.append(rel.source_slug)
            if rel.destination_type.value == "person":
                if rel.destination_slug not in person_slugs:
                    person_slugs.append(rel.destination_slug)

        # Build diagram data
        from ...domain.use_cases.diagrams.system_landscape import SystemLandscapeDiagramData

        data = SystemLandscapeDiagramData(
            systems=systems,
            person_slugs=person_slugs,
            relationships=relationships,
        )

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_system_landscape(data, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml))
        return result_nodes


class DeploymentDiagramDirective(DiagramDirective):
    """Generate a deployment diagram.

    Usage::

        .. deployment-diagram:: production
           :title: Production Deployment

    Shows how containers are deployed to infrastructure nodes.
    """

    required_arguments = 1
    has_content = False

    def run(self) -> list[nodes.Node]:
        environment = self.arguments[0]
        title = self.options.get("title", f"Deployment: {environment}")

        storage = self.get_c4_storage()
        deployment_nodes = storage.get("deployment_nodes", {})

        # Filter nodes by environment
        nodes_in_env = [
            n for n in deployment_nodes.values()
            if n.environment == environment
        ]

        if not nodes_in_env:
            return self.empty_result(f"No deployment nodes for environment '{environment}'")

        # Gather container instances
        container_slugs = set()
        for node in nodes_in_env:
            for instance in node.container_instances:
                container_slugs.add(instance.container_slug)

        containers = [
            storage["containers"].get(slug)
            for slug in container_slugs
            if storage["containers"].get(slug)
        ]

        # Gather relationships between deployed containers
        relationships = [
            rel for rel in storage["relationships"].values()
            if rel.source_slug in container_slugs or rel.destination_slug in container_slugs
        ]

        # Build diagram data
        from ...domain.use_cases.diagrams.deployment_diagram import DeploymentDiagramData

        data = DeploymentDiagramData(
            environment=environment,
            nodes=nodes_in_env,
            containers=containers,
            relationships=relationships,
        )

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_deployment_diagram(data, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml))
        return result_nodes


class DynamicDiagramDirective(DiagramDirective):
    """Generate a dynamic (sequence) diagram.

    Usage::

        .. dynamic-diagram:: user-login
           :title: User Login Flow

    Shows a sequence of interactions for a specific scenario.
    """

    required_arguments = 1
    has_content = False

    def run(self) -> list[nodes.Node]:
        sequence_name = self.arguments[0]
        title = self.options.get("title", f"Dynamic: {sequence_name}")

        storage = self.get_c4_storage()
        dynamic_steps = storage.get("dynamic_steps", {})

        # Filter steps by sequence name and sort by step number
        steps = sorted(
            [s for s in dynamic_steps.values() if s.sequence_name == sequence_name],
            key=lambda s: s.step_number,
        )

        if not steps:
            return self.empty_result(f"No dynamic steps for sequence '{sequence_name}'")

        # Gather participating elements
        system_slugs = set()
        container_slugs = set()
        component_slugs = set()
        person_slugs = []

        for step in steps:
            for el_type, el_slug in [
                (step.source_type, step.source_slug),
                (step.destination_type, step.destination_slug),
            ]:
                if el_type.value == "software_system":
                    system_slugs.add(el_slug)
                elif el_type.value == "container":
                    container_slugs.add(el_slug)
                elif el_type.value == "component":
                    component_slugs.add(el_slug)
                elif el_type.value == "person":
                    if el_slug not in person_slugs:
                        person_slugs.append(el_slug)

        systems = [
            storage["software_systems"].get(slug)
            for slug in system_slugs
            if storage["software_systems"].get(slug)
        ]
        containers = [
            storage["containers"].get(slug)
            for slug in container_slugs
            if storage["containers"].get(slug)
        ]
        components = [
            storage["components"].get(slug)
            for slug in component_slugs
            if storage["components"].get(slug)
        ]

        # Build diagram data
        from ...domain.use_cases.diagrams.dynamic_diagram import DynamicDiagramData

        data = DynamicDiagramData(
            sequence_name=sequence_name,
            steps=steps,
            systems=systems,
            containers=containers,
            components=components,
            person_slugs=person_slugs,
        )

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_dynamic_diagram(data, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml))
        return result_nodes

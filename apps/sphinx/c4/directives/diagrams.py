"""Diagram directives for C4 Sphinx integration.

Provides directives for generating C4 diagrams using PlantUML.
"""

import os

from docutils import nodes
from docutils.parsers.rst import directives

from julee.c4.serializers.plantuml import PlantUMLSerializer
from julee.c4.use_cases.diagrams.component_diagram import GetComponentDiagramRequest
from julee.c4.use_cases.diagrams.container_diagram import GetContainerDiagramRequest
from julee.c4.use_cases.diagrams.deployment_diagram import GetDeploymentDiagramRequest
from julee.c4.use_cases.diagrams.dynamic_diagram import GetDynamicDiagramRequest
from julee.c4.use_cases.diagrams.system_landscape import GetSystemLandscapeDiagramRequest

from .base import C4Directive


class SystemContextDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for system-context-diagram, replaced at doctree-resolved."""

    pass


class DiagramDirective(C4Directive):
    """Base class for diagram directives."""

    option_spec = {
        "title": directives.unchanged,
        "format": directives.unchanged,
    }

    def get_serializer(self) -> PlantUMLSerializer:
        """Get the PlantUML serializer."""
        return PlantUMLSerializer()

    def make_plantuml_node(self, puml_source: str, docname: str) -> nodes.Node:
        """Create a PlantUML node or fallback to literal block.

        Args:
            puml_source: PlantUML source code
            docname: Document name for path resolution

        Returns:
            PlantUML node or literal block
        """
        try:
            from sphinxcontrib.plantuml import plantuml

            node = plantuml(puml_source)
            node["uml"] = puml_source
            # Required by sphinxcontrib.plantuml for rendering
            node["incdir"] = os.path.dirname(docname)
            node["filename"] = os.path.basename(docname)
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
    Uses placeholder pattern for deferred rendering after all docs are read.
    """

    required_arguments = 1
    has_content = False

    def run(self) -> list[nodes.Node]:
        system_slug = self.arguments[0]
        title = self.options.get("title", f"System Context: {system_slug}")

        # Return placeholder - rendering in doctree-resolved
        # so we can access HCD personas after all docs are read
        node = SystemContextDiagramPlaceholder()
        node["system_slug"] = system_slug
        node["title"] = title
        return [node]


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

        # Get diagram data via use case
        response = self.c4_context.get_container_diagram.execute_sync(
            GetContainerDiagramRequest(system_slug=system_slug)
        )

        if not response.diagram:
            return self.empty_result(f"Software system '{system_slug}' not found")

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_container_diagram(response.diagram, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml, self.env.docname))
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

        # Get diagram data via use case
        response = self.c4_context.get_component_diagram.execute_sync(
            GetComponentDiagramRequest(container_slug=container_slug)
        )

        if not response.diagram:
            return self.empty_result(f"Container '{container_slug}' not found")

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_component_diagram(response.diagram, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml, self.env.docname))
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

        # Get diagram data via use case
        response = self.c4_context.get_system_landscape_diagram.execute_sync(
            GetSystemLandscapeDiagramRequest()
        )

        if not response.diagram or not response.diagram.systems:
            return self.empty_result("No software systems defined")

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_system_landscape(response.diagram, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml, self.env.docname))
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

        # Get diagram data via use case
        response = self.c4_context.get_deployment_diagram.execute_sync(
            GetDeploymentDiagramRequest(environment=environment)
        )

        if not response.diagram or not response.diagram.nodes:
            return self.empty_result(
                f"No deployment nodes for environment '{environment}'"
            )

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_deployment_diagram(response.diagram, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml, self.env.docname))
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

        # Get diagram data via use case
        response = self.c4_context.get_dynamic_diagram.execute_sync(
            GetDynamicDiagramRequest(sequence_name=sequence_name)
        )

        if not response.diagram or not response.diagram.steps:
            return self.empty_result(f"No dynamic steps for sequence '{sequence_name}'")

        # Generate PlantUML
        serializer = self.get_serializer()
        puml = serializer.serialize_dynamic_diagram(response.diagram, title)

        result_nodes = []
        result_nodes.append(self.make_plantuml_node(puml, self.env.docname))
        return result_nodes


def _first_sentence(text: str) -> str:
    """Extract the first sentence from text.

    Args:
        text: Multi-sentence text

    Returns:
        First sentence (up to first period followed by space or end)
    """
    if not text:
        return ""
    # Find first sentence-ending punctuation followed by space or end
    for i, char in enumerate(text):
        if char in ".!?" and (i + 1 >= len(text) or text[i + 1] in " \n"):
            return text[: i + 1]
    # No sentence ending found, return as-is (but truncate if too long)
    if len(text) > 100:
        return text[:97] + "..."
    return text


def _get_c4_storage(app):
    """Get C4 storage from app environment.

    Ensures all expected keys exist, even if storage was initialized
    elsewhere with a different structure.
    """
    if not hasattr(app.env, "c4_storage"):
        app.env.c4_storage = {}
    storage = app.env.c4_storage
    # Ensure all expected keys exist (handles case where repository
    # initialized storage before this function was called)
    for key in [
        "software_systems",
        "containers",
        "components",
        "relationships",
        "deployment_nodes",
        "dynamic_steps",
    ]:
        if key not in storage:
            storage[key] = {}
    return storage


def _make_plantuml_node(puml_source: str, docname: str) -> nodes.Node:
    """Create a PlantUML node or fallback to literal block."""
    try:
        from sphinxcontrib.plantuml import plantuml

        node = plantuml(puml_source)
        node["uml"] = puml_source
        node["incdir"] = os.path.dirname(docname)
        node["filename"] = os.path.basename(docname)
        return node
    except ImportError:
        return nodes.literal_block(puml_source, puml_source)


def build_system_context_diagram(system_slug: str, title: str, docname: str, app):
    """Build the system context diagram for a software system.

    Args:
        system_slug: Slug of the software system
        title: Diagram title
        docname: Document name for path resolution
        app: Sphinx application

    Returns:
        List of docutils nodes
    """
    from julee.c4.entities.diagrams import PersonInfo, SystemContextDiagram
    from julee.c4.serializers.plantuml import PlantUMLSerializer

    storage = _get_c4_storage(app)
    system = storage["software_systems"].get(system_slug)

    if not system:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"Software system '{system_slug}' not found")
        return [para]

    # Gather relationships involving this system
    relationships = [
        r for r in storage["relationships"].values() if r.involves_system(system_slug)
    ]

    # Gather external systems and person slugs
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

    # Try to look up HCD personas for richer person data
    persons = []
    try:
        from apps.sphinx.hcd.context import get_hcd_context
        from julee.hcd.use_cases.crud import GetPersonaRequest

        hcd_context = get_hcd_context(app)
        for slug in person_slugs:
            response = hcd_context.get_persona.execute_sync(GetPersonaRequest(slug=slug))
            if response.persona:
                persons.append(
                    PersonInfo(
                        slug=response.persona.slug,
                        name=response.persona.name,
                        description=_first_sentence(response.persona.context or ""),
                    )
                )
    except (ImportError, AttributeError):
        # HCD extension not loaded or no personas - use slugs only
        pass
    except Exception:
        # Log unexpected errors
        pass

    data = SystemContextDiagram(
        system=system,
        external_systems=external_systems,
        person_slugs=person_slugs,
        persons=persons,
        relationships=relationships,
    )

    # Generate PlantUML
    serializer = PlantUMLSerializer()
    puml = serializer.serialize_system_context(data, title)

    return [_make_plantuml_node(puml, docname)]


def process_c4_diagram_placeholders(app, doctree, docname):
    """Replace C4 diagram placeholders with rendered content.

    Called at doctree-resolved event, after all documents have been read.
    """
    # Process system-context-diagram placeholders
    for node in doctree.traverse(SystemContextDiagramPlaceholder):
        system_slug = node["system_slug"]
        title = node["title"]
        content = build_system_context_diagram(system_slug, title, docname, app)
        node.replace_self(content)

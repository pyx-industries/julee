"""C4 Bridge directives for sphinx_hcd.

Generates C4 diagrams and lists from HCD data, bridging human-centered design
documentation to architectural visualizations.

- c4-container-diagram: Generate C4 container diagram from apps/accelerators
- app-list-by-interface: List apps grouped by interface type
- accelerator-list: List accelerators with their concepts
"""

import os

from docutils import nodes
from docutils.parsers.rst import directives

from julee.hcd.infrastructure.renderers import C4PlantUMLRenderer
from julee.hcd.use_cases.c4_bridge import generate_c4_container_diagram
from julee.hcd.use_cases.crud import (
    ListAcceleratorsRequest,
    ListAppsRequest,
    ListContribModulesRequest,
    ListPersonasRequest,
)

from .base import HCDDirective


class C4ContainerDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder for c4-container-diagram, replaced at doctree-resolved."""

    pass


class AppListByInterfacePlaceholder(nodes.General, nodes.Element):
    """Placeholder for app-list-by-interface, replaced at doctree-resolved."""

    pass


class AcceleratorListPlaceholder(nodes.General, nodes.Element):
    """Placeholder for accelerator-list, replaced at doctree-resolved."""

    pass


class AppListByInterfaceDirective(HCDDirective):
    """List apps grouped by interface type.

    Usage::

        .. app-list-by-interface::

    Generates a list of apps grouped by Sphinx Extensions, REST APIs, MCP Servers, etc.
    """

    has_content = False

    def run(self):
        return [AppListByInterfacePlaceholder()]


class AcceleratorListDirective(HCDDirective):
    """List accelerators with their domain concepts.

    Usage::

        .. accelerator-list::

    Generates a list of accelerators with their concepts and descriptions.
    """

    has_content = False

    def run(self):
        return [AcceleratorListPlaceholder()]


class C4ContainerDiagramDirective(HCDDirective):
    """Generate a C4 container diagram from HCD apps and accelerators.

    Usage::

        .. c4-container-diagram::
           :title: Container Diagram - Julee Tooling
           :system-name: Julee Tooling
           :show-foundation: true
           :show-external: true

    The directive reads all apps and accelerators from the HCD repositories
    and generates a PlantUML C4 container diagram showing:
    - Apps grouped by interface type (Sphinx, API, MCP)
    - Accelerators as bounded contexts
    - Relationships from apps to the accelerators they expose
    """

    has_content = False
    option_spec = {
        "title": directives.unchanged,
        "system-name": directives.unchanged,
        "show-foundation": directives.flag,
        "show-external": directives.flag,
        "foundation-name": directives.unchanged,
        "external-name": directives.unchanged,
    }

    def run(self):
        node = C4ContainerDiagramPlaceholder()
        node["title"] = self.options.get("title", "Container Diagram")
        node["system_name"] = self.options.get("system-name", "System")
        node["show_foundation"] = "show-foundation" in self.options
        node["show_external"] = "show-external" in self.options
        node["foundation_name"] = self.options.get("foundation-name", "Foundation")
        node["external_name"] = self.options.get("external-name", "External Systems")
        return [node]


def build_c4_container_diagram(
    docname: str,
    hcd_context,
    title: str,
    system_name: str,
    show_foundation: bool,
    show_external: bool,
    foundation_name: str,
    external_name: str,
):
    """Build a C4 container diagram from HCD data.

    Uses the C4 bridge use case for data generation and
    PlantUML renderer for diagram output.
    """
    from ..config import get_config

    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        para = nodes.paragraph()
        para += nodes.emphasis(text="PlantUML extension not available")
        return [para]

    config = get_config()
    solution = config.solution_slug
    all_apps = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    ).apps
    all_accelerators = hcd_context.list_accelerators.execute_sync(
        ListAcceleratorsRequest(solution_slug=solution)
    ).accelerators
    all_contribs = hcd_context.list_contribs.execute_sync(
        ListContribModulesRequest(solution_slug=solution)
    ).entities
    all_personas = hcd_context.list_personas.execute_sync(
        ListPersonasRequest(solution_slug=solution)
    ).personas

    if not all_apps and not all_accelerators and not all_contribs:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No apps, accelerators, or contrib modules defined")
        return [para]

    # Generate diagram data via use case
    diagram_data = generate_c4_container_diagram(
        apps=all_apps,
        accelerators=all_accelerators,
        contribs=all_contribs,
        personas=all_personas,
        title=title,
        system_name=system_name,
        show_foundation=show_foundation,
        foundation_name=foundation_name,
        show_external=show_external,
        external_name=external_name,
    )

    # Render to PlantUML
    renderer = C4PlantUMLRenderer()
    puml_source = renderer.render(diagram_data)

    node = plantuml(puml_source)
    node["uml"] = puml_source
    node["incdir"] = os.path.dirname(docname)
    node["filename"] = os.path.basename(docname)

    return [node]


def build_app_list_by_interface(docname: str, hcd_context):
    """Build a simple bullet list of apps."""
    from apps.sphinx.shared import path_to_root

    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    all_apps = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    ).apps
    prefix = path_to_root(docname)

    if not all_apps:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No apps defined")
        return [para]

    bullet_list = nodes.bullet_list()
    for app in sorted(all_apps, key=lambda a: a.slug):
        item = nodes.list_item()
        item_para = nodes.paragraph()

        # Link to app doc
        if app.docname:
            ref = nodes.reference("", "", refuri=f"{prefix}{app.docname}.html")
            ref += nodes.Text(app.name)
            item_para += ref
        else:
            item_para += nodes.Text(app.name)

        # Description
        if app.description:
            first_sentence = app.description.split(".")[0]
            item_para += nodes.Text(f" - {first_sentence}")

        item += item_para
        bullet_list += item

    return [bullet_list]


def build_accelerator_list(docname: str, hcd_context):
    """Build a simple bullet list of accelerators."""
    from apps.sphinx.shared import path_to_root

    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    all_accelerators = hcd_context.list_accelerators.execute_sync(
        ListAcceleratorsRequest(solution_slug=solution)
    ).accelerators
    prefix = path_to_root(docname)

    if not all_accelerators:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No accelerators defined")
        return [para]

    bullet_list = nodes.bullet_list()
    for accel in sorted(all_accelerators, key=lambda a: a.slug):
        item = nodes.list_item()
        item_para = nodes.paragraph()

        # Link to accelerator doc
        if accel.docname:
            ref = nodes.reference("", "", refuri=f"{prefix}{accel.docname}.html")
            ref += nodes.Text(accel.display_title)
            item_para += ref
        else:
            item_para += nodes.Text(accel.display_title)

        # Description
        if accel.objective:
            first_sentence = accel.objective.split(".")[0]
            item_para += nodes.Text(f" - {first_sentence}")

        item += item_para
        bullet_list += item

    return [bullet_list]


def process_c4_bridge_placeholders(app, doctree, docname):
    """Replace C4 bridge placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    for node in doctree.traverse(C4ContainerDiagramPlaceholder):
        content = build_c4_container_diagram(
            docname,
            hcd_context,
            title=node["title"],
            system_name=node["system_name"],
            show_foundation=node["show_foundation"],
            show_external=node["show_external"],
            foundation_name=node["foundation_name"],
            external_name=node["external_name"],
        )
        node.replace_self(content)

    for node in doctree.traverse(AppListByInterfacePlaceholder):
        content = build_app_list_by_interface(docname, hcd_context)
        node.replace_self(content)

    for node in doctree.traverse(AcceleratorListPlaceholder):
        content = build_accelerator_list(docname, hcd_context)
        node.replace_self(content)

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
    """Build a C4 container diagram from HCD data."""
    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        para = nodes.paragraph()
        para += nodes.emphasis(text="PlantUML extension not available")
        return [para]

    all_apps = hcd_context.app_repo.list_all()
    all_accelerators = hcd_context.accelerator_repo.list_all()
    all_contribs = hcd_context.contrib_repo.list_all()
    all_personas = hcd_context.persona_repo.list_all()

    if not all_apps and not all_accelerators and not all_contribs:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No apps, accelerators, or contrib modules defined")
        return [para]

    # Build PlantUML
    lines = [
        "@startuml",
        "!include <C4/C4_Container>",
        "",
        f"title {title}",
        "",
    ]

    # Personas (outside system boundary) - only those with relationships
    shown_personas = [
        p for p in all_personas
        if p.app_slugs or p.accelerator_slugs or p.contrib_slugs
    ]
    for persona in sorted(shown_personas, key=lambda p: p.slug):
        persona_id = _safe_id(persona.slug)
        desc = _escape(persona.context) if persona.context else persona.name
        lines.append(f'Person({persona_id}, "{persona.name}", "{desc}")')
    if shown_personas:
        lines.append("")

    lines.append(f'System_Boundary({_safe_id(system_name)}, "{system_name}") {{')
    lines.append("")

    # Apps as containers
    for app in sorted(all_apps, key=lambda a: a.slug):
        app_id = _safe_id(app.slug)
        tech = app.c4_technology
        desc = app.description or app.interface_label
        lines.append(f'   Container({app_id}, "{app.name}", "{tech}", "{_escape(desc)}")')
    if all_apps:
        lines.append("")

    # Accelerators as containers
    for accel in sorted(all_accelerators, key=lambda a: a.slug):
        accel_id = _safe_id(accel.slug)
        tech = accel.technology
        desc = accel.c4_description
        lines.append(f'   Container({accel_id}, "{accel.display_title}", "{tech}", "{_escape(desc)}")')
    if all_accelerators:
        lines.append("")

    # Contrib modules as containers
    for contrib in sorted(all_contribs, key=lambda c: c.slug):
        contrib_id = _safe_id(contrib.slug)
        tech = contrib.technology
        desc = contrib.c4_description
        lines.append(f'   Container({contrib_id}, "{contrib.display_title}", "{tech}", "{_escape(desc)}")')
    if all_contribs:
        lines.append("")

    # Foundation layer
    if show_foundation:
        lines.append(f'   Container(foundation, "{foundation_name}", "Python", "Clean architecture idioms and utilities")')
        lines.append("")

    lines.append("}")  # End system boundary
    lines.append("")

    # External systems
    if show_external:
        lines.append(f'System_Ext(external, "{external_name}", "External dependencies")')
        lines.append("")

    # Relationships: Personas to apps
    app_by_slug = {app.slug: app for app in all_apps}
    for persona in all_personas:
        persona_id = _safe_id(persona.slug)
        for app_slug in persona.app_slugs:
            if app_slug in app_by_slug:
                app = app_by_slug[app_slug]
                lines.append(f'Rel({persona_id}, {_safe_id(app_slug)}, "{app.interface.user_relationship}")')
    if all_personas:
        lines.append("")

    # Relationships: Personas to accelerators (direct usage)
    accel_by_slug = {accel.slug: accel for accel in all_accelerators}
    for persona in all_personas:
        persona_id = _safe_id(persona.slug)
        for accel_slug in persona.accelerator_slugs:
            if accel_slug in accel_by_slug:
                lines.append(f'Rel({persona_id}, {_safe_id(accel_slug)}, "Uses")')
    lines.append("")

    # Relationships: Personas to contrib modules
    contrib_by_slug = {contrib.slug: contrib for contrib in all_contribs}
    for persona in all_personas:
        persona_id = _safe_id(persona.slug)
        for contrib_slug in persona.contrib_slugs:
            if contrib_slug in contrib_by_slug:
                lines.append(f'Rel({persona_id}, {_safe_id(contrib_slug)}, "Uses")')
    lines.append("")

    # Relationships: Apps to accelerators
    for app in all_apps:
        app_id = _safe_id(app.slug)
        for accel_slug in app.accelerators:
            accel_id = _safe_id(accel_slug)
            lines.append(f'Rel({app_id}, {accel_id}, "{app.interface.accelerator_relationship}")')

    lines.append("")

    # Relationships: Accelerators to foundation
    if show_foundation:
        for accel in all_accelerators:
            accel_id = _safe_id(accel.slug)
            lines.append(f'Rel({accel_id}, foundation, "Built on")')
        lines.append("")

    # Relationships: Contrib modules to foundation
    if show_foundation:
        for contrib in all_contribs:
            contrib_id = _safe_id(contrib.slug)
            lines.append(f'Rel({contrib_id}, foundation, "Built on")')
        lines.append("")

    # Relationships: Foundation to external (foundation provides infrastructure)
    if show_external and show_foundation:
        lines.append(f'Rel(foundation, external, "Connects to")')
        lines.append("")

    lines.append("@enduml")

    puml_source = "\n".join(lines)
    node = plantuml(puml_source)
    node["uml"] = puml_source
    node["incdir"] = os.path.dirname(docname)
    node["filename"] = os.path.basename(docname)

    return [node]


def build_app_list_by_interface(docname: str, hcd_context):
    """Build a simple bullet list of apps."""
    from apps.sphinx.shared import path_to_root

    all_apps = hcd_context.app_repo.list_all()
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

    all_accelerators = hcd_context.accelerator_repo.list_all()
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


def _safe_id(name: str) -> str:
    """Convert name to a safe PlantUML identifier."""
    return name.replace("-", "_").replace(" ", "_").replace(".", "_")


def _escape(text: str) -> str:
    """Escape text for PlantUML strings, using only the first sentence."""
    # Normalize whitespace
    text = " ".join(text.split())
    # Extract first sentence
    for end in [". ", ".\n", ".\t"]:
        if end[0] in text:
            idx = text.find(end[0])
            if idx > 0:
                text = text[:idx]
                break
    return text.replace('"', '\\"')


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

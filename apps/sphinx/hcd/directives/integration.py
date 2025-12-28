"""Integration directives for sphinx_hcd.

Provides directives to render integration information with external dependencies.

Provides directives:
- define-integration: Render integration info from YAML
- integration-index: Generate index with architecture diagram
"""

import os

from docutils import nodes

from julee.hcd.entities.integration import Direction
from julee.hcd.use_cases.crud import (
    GetIntegrationRequest,
    ListIntegrationsRequest,
)

from .base import HCDDirective


class DefineIntegrationPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for define-integration, replaced at doctree-resolved."""

    pass


class DefineIntegrationDirective(HCDDirective):
    """Render integration info from YAML manifest.

    Usage::

        .. define-integration:: pilot-data-collection
    """

    required_arguments = 1

    def run(self):
        slug = self.arguments[0]

        # Track documented integrations
        if not hasattr(self.env, "documented_integrations"):
            self.env.documented_integrations = set()
        self.env.documented_integrations.add(slug)

        node = DefineIntegrationPlaceholder()
        node["integration_slug"] = slug
        return [node]


def build_integration_content(slug: str, docname: str, hcd_context):
    """Build content nodes for an integration page."""
    from sphinx.addnodes import seealso

    response = hcd_context.get_integration.execute_sync(
        GetIntegrationRequest(slug=slug)
    )
    integration = response.integration

    if not integration:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"Integration '{slug}' not found")
        return [para]

    result_nodes = []

    # Description
    if integration.description:
        desc_para = nodes.paragraph()
        desc_para += nodes.Text(integration.description)
        result_nodes.append(desc_para)

    # Seealso with metadata
    seealso_node = seealso()

    # Direction
    direction_labels = {
        Direction.INBOUND: "Inbound (data source)",
        Direction.OUTBOUND: "Outbound (data sink)",
        Direction.BIDIRECTIONAL: "Bidirectional",
    }
    dir_para = nodes.paragraph()
    dir_para += nodes.strong(text="Direction: ")
    dir_para += nodes.Text(
        direction_labels.get(integration.direction, str(integration.direction))
    )
    seealso_node += dir_para

    # Module
    mod_para = nodes.paragraph()
    mod_para += nodes.strong(text="Module: ")
    mod_para += nodes.literal(text=f"integrations.{integration.module}")
    seealso_node += mod_para

    # External dependencies
    if integration.depends_on:
        deps_para = nodes.paragraph()
        deps_para += nodes.strong(text="Depends On: ")
        for i, dep in enumerate(integration.depends_on):
            if dep.url:
                ref = nodes.reference("", "", refuri=dep.url)
                ref += nodes.Text(dep.name)
                deps_para += ref
            else:
                deps_para += nodes.Text(dep.name)
            if i < len(integration.depends_on) - 1:
                deps_para += nodes.Text(", ")
        seealso_node += deps_para

    result_nodes.append(seealso_node)
    return result_nodes


def build_integration_index(docname: str, hcd_context):
    """Build integration index with architecture diagram."""
    from ..config import get_config

    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        para = nodes.paragraph()
        para += nodes.emphasis(text="PlantUML extension not available")
        return [para]

    config = get_config()
    solution = config.solution_slug
    all_integrations = hcd_context.list_integrations.execute_sync(
        ListIntegrationsRequest(solution_slug=solution)
    ).integrations

    if not all_integrations:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No integrations defined")
        return [para]

    # Build PlantUML diagram
    lines = [
        "@startuml",
        "skinparam componentStyle rectangle",
        "skinparam defaultTextAlignment center",
        "skinparam component {",
        "  BackgroundColor<<integration>> LightBlue",
        "  BackgroundColor<<external>> LightYellow",
        "  BackgroundColor<<core>> LightGreen",
        "}",
        "",
        'title "Integration Architecture"',
        "",
        "' Core system",
        'component "Julee\\nSolution" as core <<core>>',
        "",
        "' Integrations and their external dependencies",
    ]

    for integration in sorted(all_integrations, key=lambda i: i.slug):
        int_id = integration.slug.replace("-", "_")
        lines.append(f'component "{integration.name}" as {int_id} <<integration>>')

        for dep in integration.depends_on:
            dep_id = dep.name.lower().replace(" ", "_").replace("-", "_")
            dep_label = dep.name
            if dep.description:
                dep_label += f"\\n({dep.description})"
            lines.append(f'component "{dep_label}" as {dep_id} <<external>>')

    lines.append("")
    lines.append("' Relationships")

    for integration in sorted(all_integrations, key=lambda i: i.slug):
        int_id = integration.slug.replace("-", "_")

        # Core to/from integration
        if integration.direction == Direction.INBOUND:
            lines.append(f"{int_id} --> core")
        elif integration.direction == Direction.OUTBOUND:
            lines.append(f"core --> {int_id}")
        else:
            lines.append(f"core <--> {int_id}")

        # Integration to external dependencies
        for dep in integration.depends_on:
            dep_id = dep.name.lower().replace(" ", "_").replace("-", "_")
            if integration.direction == Direction.INBOUND:
                lines.append(f"{dep_id} --> {int_id}")
            elif integration.direction == Direction.OUTBOUND:
                lines.append(f"{int_id} --> {dep_id}")
            else:
                lines.append(f"{int_id} <--> {dep_id}")

    lines.append("")
    lines.append("@enduml")

    puml_source = "\n".join(lines)
    node = plantuml(puml_source)
    node["uml"] = puml_source
    node["incdir"] = os.path.dirname(docname)
    node["filename"] = os.path.basename(docname) + ".rst"

    return [node]


# NOTE: process_integration_placeholders removed - now handled by
# infrastructure/handlers/placeholder_resolution.py via IntegrationPlaceholderHandler

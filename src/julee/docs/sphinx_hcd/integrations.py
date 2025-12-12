"""Sphinx extension for integrations.

Scans integration manifests for definitions and provides directives to render
integration information with external dependencies.

Provides directives:
- define-integration: Render integration info from YAML
- integration-index: Generate index with architecture diagram
"""

import os

import yaml
from docutils import nodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from .config import get_config

logger = logging.getLogger(__name__)

# Global registry populated at build init
_integration_registry: dict = {}


def get_integration_registry() -> dict:
    """Get the integration registry."""
    return _integration_registry


def get_documented_integrations(env) -> set:
    """Get documented integrations set from env, creating if needed."""
    if not hasattr(env, "documented_integrations"):
        env.documented_integrations = set()
    return env.documented_integrations


def scan_integration_manifests(app):
    """Scan integration manifests and build the registry."""
    global _integration_registry
    _integration_registry = {}

    config = get_config()
    integrations_dir = config.get_path("integration_manifests")

    if not integrations_dir.exists():
        logger.info(
            f"Integrations directory not found at {integrations_dir} - no integration manifests to index"
        )
        return

    for int_dir in integrations_dir.iterdir():
        if not int_dir.is_dir() or int_dir.name.startswith("_"):
            continue

        manifest_path = int_dir / "integration.yaml"
        if not manifest_path.exists():
            continue

        module_name = int_dir.name

        try:
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not read {manifest_path}: {e}")
            continue

        slug = manifest.get("slug", module_name.replace("_", "-"))
        _integration_registry[slug] = {
            "slug": slug,
            "module": module_name,
            "name": manifest.get("name", slug.replace("-", " ").title()),
            "description": manifest.get("description", "").strip(),
            "direction": manifest.get("direction", "bidirectional"),
            "depends_on": manifest.get("depends_on", []),
            "manifest_path": str(manifest_path),
        }

    logger.info(f"Indexed {len(_integration_registry)} integrations from manifests")


def validate_integrations(app, env):
    """Validate integration coverage after all documents are read."""
    documented = get_documented_integrations(env)

    # Check for integrations without documentation
    for slug in _integration_registry:
        if slug not in documented:
            logger.warning(
                f"Integration '{slug}' has no docs page. "
                f"Create integrations/{slug}.rst with '.. define-integration:: {slug}'"
            )

    # Check for documented integrations without manifests
    for slug in documented:
        if slug not in _integration_registry:
            logger.warning(
                f"Integration '{slug}' documented but has no manifest. "
                f"Create integration.yaml in the appropriate directory"
            )


class DefineIntegrationDirective(SphinxDirective):
    """Render integration info from YAML manifest.

    Usage::

        .. define-integration:: pilot-data-collection
    """

    required_arguments = 1

    def run(self):
        slug = self.arguments[0]
        get_documented_integrations(self.env).add(slug)

        node = DefineIntegrationPlaceholder()
        node["integration_slug"] = slug
        return [node]


class DefineIntegrationPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for define-integration, replaced at doctree-resolved."""

    pass


class IntegrationIndexDirective(SphinxDirective):
    """Generate integration index with architecture diagram.

    Usage::

        .. integration-index::
    """

    def run(self):
        return [IntegrationIndexPlaceholder()]


class IntegrationIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for integration-index, replaced at doctree-resolved."""

    pass


def build_integration_content(slug, docname):
    """Build content nodes for an integration page."""
    from sphinx.addnodes import seealso

    if slug not in _integration_registry:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"Integration '{slug}' not found")
        return [para]

    data = _integration_registry[slug]
    result_nodes = []

    # Description
    if data["description"]:
        desc_para = nodes.paragraph()
        desc_para += nodes.Text(data["description"])
        result_nodes.append(desc_para)

    # Seealso with metadata
    seealso_node = seealso()

    # Direction
    direction_labels = {
        "inbound": "Inbound (data source)",
        "outbound": "Outbound (data sink)",
        "bidirectional": "Bidirectional",
    }
    dir_para = nodes.paragraph()
    dir_para += nodes.strong(text="Direction: ")
    dir_para += nodes.Text(direction_labels.get(data["direction"], data["direction"]))
    seealso_node += dir_para

    # Module
    mod_para = nodes.paragraph()
    mod_para += nodes.strong(text="Module: ")
    mod_para += nodes.literal(text=f"integrations.{data['module']}")
    seealso_node += mod_para

    # External dependencies
    if data["depends_on"]:
        deps_para = nodes.paragraph()
        deps_para += nodes.strong(text="Depends On: ")
        for i, dep in enumerate(data["depends_on"]):
            if dep.get("url"):
                ref = nodes.reference("", "", refuri=dep["url"])
                ref += nodes.Text(dep["name"])
                deps_para += ref
            else:
                deps_para += nodes.Text(dep["name"])
            if i < len(data["depends_on"]) - 1:
                deps_para += nodes.Text(", ")
        seealso_node += deps_para

    result_nodes.append(seealso_node)
    return result_nodes


def build_integration_index(docname):
    """Build integration index with architecture diagram."""
    from sphinxcontrib.plantuml import plantuml

    result_nodes = []

    if not _integration_registry:
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

    for slug, data in sorted(_integration_registry.items()):
        int_id = slug.replace("-", "_")
        lines.append(f'component "{data["name"]}" as {int_id} <<integration>>')

        for dep in data.get("depends_on", []):
            dep_id = dep["name"].lower().replace(" ", "_").replace("-", "_")
            dep_label = dep["name"]
            if dep.get("description"):
                dep_label += f"\\n({dep['description']})"
            lines.append(f'component "{dep_label}" as {dep_id} <<external>>')

    lines.append("")
    lines.append("' Relationships")

    for slug, data in sorted(_integration_registry.items()):
        int_id = slug.replace("-", "_")
        direction = data.get("direction", "bidirectional")

        # Core to/from integration
        if direction == "inbound":
            lines.append(f"{int_id} --> core")
        elif direction == "outbound":
            lines.append(f"core --> {int_id}")
        else:
            lines.append(f"core <--> {int_id}")

        # Integration to external dependencies
        for dep in data.get("depends_on", []):
            dep_id = dep["name"].lower().replace(" ", "_").replace("-", "_")
            if direction == "inbound":
                lines.append(f"{dep_id} --> {int_id}")
            elif direction == "outbound":
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
    result_nodes.append(node)

    return result_nodes


def process_integration_placeholders(app, doctree, docname):
    """Replace integration placeholders after all documents are read."""
    for node in doctree.traverse(DefineIntegrationPlaceholder):
        slug = node["integration_slug"]
        content = build_integration_content(slug, docname)
        node.replace_self(content)

    for node in doctree.traverse(IntegrationIndexPlaceholder):
        content = build_integration_index(docname)
        node.replace_self(content)


def setup(app):
    app.connect("builder-inited", scan_integration_manifests)
    app.connect("env-check-consistency", validate_integrations)
    app.connect("doctree-resolved", process_integration_placeholders)

    app.add_directive("define-integration", DefineIntegrationDirective)
    app.add_directive("integration-index", IntegrationIndexDirective)

    app.add_node(DefineIntegrationPlaceholder)
    app.add_node(IntegrationIndexPlaceholder)

    return {
        "version": "1.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }

"""Accelerator directives for sphinx_hcd.

Provides directives for accelerators with code introspection:
- define-accelerator: Define accelerator with metadata + introspected code
- accelerator-index: Generate index table grouped by status
- accelerators-for-app: List accelerators an app exposes
- dependent-accelerators: List accelerators that depend on an integration
- accelerator-dependency-diagram: Generate PlantUML component diagram
- accelerator-status: Show status, milestone, and acceptance info
"""

import os

from docutils import nodes
from docutils.parsers.rst import directives

from ...domain.models.accelerator import Accelerator, IntegrationReference
from ...domain.use_cases import (
    get_accelerator_cross_references,
    get_apps_for_accelerator,
    get_code_info_for_accelerator,
    get_dependent_accelerators,
    get_fed_by_accelerators,
    get_journeys_for_accelerator,
    get_publish_integrations,
    get_source_integrations,
    get_stories_for_accelerator,
)
from ...utils import (
    normalize_name,
    parse_integration_options,
    parse_list_option,
    path_to_root,
)
from .base import HCDDirective


class DefineAcceleratorPlaceholder(nodes.General, nodes.Element):
    """Placeholder for define-accelerator, replaced at doctree-resolved."""

    pass


class AcceleratorIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder for accelerator-index, replaced at doctree-resolved."""

    pass


class AcceleratorsForAppPlaceholder(nodes.General, nodes.Element):
    """Placeholder for accelerators-for-app, replaced at doctree-resolved."""

    pass


class DependentAcceleratorsPlaceholder(nodes.General, nodes.Element):
    """Placeholder for dependent-accelerators, replaced at doctree-resolved."""

    pass


class AcceleratorDependencyDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder for accelerator-dependency-diagram, replaced at doctree-resolved."""

    pass


class DefineAcceleratorDirective(HCDDirective):
    """Define an accelerator with metadata and introspected code.

    Usage::

        .. define-accelerator:: vocabulary-catalog
           :status: active
           :milestone: MVP
           :acceptance: All vocab terms published to CDC
           :sources-from: kafka
           :publishes-to: elasticsearch
           :depends-on: document-processor
           :feeds-into: compliance-mapper
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "status": directives.unchanged,
        "milestone": directives.unchanged,
        "acceptance": directives.unchanged,
        "sources-from": directives.unchanged,
        "publishes-to": directives.unchanged,
        "depends-on": directives.unchanged,
        "feeds-into": directives.unchanged,
    }

    def run(self):
        slug = self.arguments[0]
        docname = self.env.docname

        # Parse options
        status = self.options.get("status", "").strip()
        milestone = self.options.get("milestone", "").strip() or None
        acceptance = self.options.get("acceptance", "").strip() or None
        sources_from = parse_integration_options(self.options.get("sources-from", ""))
        publishes_to = parse_integration_options(self.options.get("publishes-to", ""))
        depends_on = parse_list_option(self.options.get("depends-on", ""))
        feeds_into = parse_list_option(self.options.get("feeds-into", ""))
        objective = "\n".join(self.content).strip()

        # Create accelerator entity
        accelerator = Accelerator(
            slug=slug,
            status=status,
            milestone=milestone,
            acceptance=acceptance,
            objective=objective,
            sources_from=[IntegrationReference(slug=s["slug"], description=s.get("description", "")) for s in sources_from],
            publishes_to=[IntegrationReference(slug=p["slug"], description=p.get("description", "")) for p in publishes_to],
            depends_on=depends_on,
            feeds_into=feeds_into,
            docname=docname,
        )

        # Add to repository
        self.hcd_context.accelerator_repo.add(accelerator)

        # Track documented accelerators
        if not hasattr(self.env, "documented_accelerators"):
            self.env.documented_accelerators = set()
        self.env.documented_accelerators.add(slug)

        # Return placeholder - rendering in doctree-resolved
        node = DefineAcceleratorPlaceholder()
        node["accelerator_slug"] = slug
        return [node]


class AcceleratorIndexDirective(HCDDirective):
    """Generate index table grouped by status.

    Usage::

        .. accelerator-index::
    """

    def run(self):
        return [AcceleratorIndexPlaceholder()]


class AcceleratorsForAppDirective(HCDDirective):
    """List accelerators an app exposes.

    Usage::

        .. accelerators-for-app:: vocabulary-tool
    """

    required_arguments = 1

    def run(self):
        node = AcceleratorsForAppPlaceholder()
        node["app_slug"] = self.arguments[0]
        return [node]


class DependentAcceleratorsDirective(HCDDirective):
    """List accelerators that depend on or publish to an integration.

    Usage::

        .. dependent-accelerators:: kafka
    """

    required_arguments = 1

    def run(self):
        node = DependentAcceleratorsPlaceholder()
        node["integration_slug"] = self.arguments[0]
        return [node]


class AcceleratorDependencyDiagramDirective(HCDDirective):
    """Generate PlantUML component diagram of accelerator dependencies.

    Usage::

        .. accelerator-dependency-diagram::
    """

    def run(self):
        return [AcceleratorDependencyDiagramPlaceholder()]


class AcceleratorStatusDirective(HCDDirective):
    """Show status, milestone, and acceptance info for an accelerator.

    Usage::

        .. accelerator-status:: vocabulary-catalog
    """

    required_arguments = 1

    def run(self):
        slug = self.arguments[0]
        accelerator = self.hcd_context.accelerator_repo.get(slug)

        if not accelerator:
            return self.empty_result(f"Accelerator '{slug}' not found")

        result_nodes = []

        # Status badge
        if accelerator.status:
            status_para = nodes.paragraph()
            status_para += nodes.strong(text="Status: ")
            status_para += nodes.Text(accelerator.status)
            result_nodes.append(status_para)

        # Milestone
        if accelerator.milestone:
            milestone_para = nodes.paragraph()
            milestone_para += nodes.strong(text="Milestone: ")
            milestone_para += nodes.Text(accelerator.milestone)
            result_nodes.append(milestone_para)

        # Acceptance criteria
        if accelerator.acceptance:
            acceptance_para = nodes.paragraph()
            acceptance_para += nodes.strong(text="Acceptance: ")
            acceptance_para += nodes.Text(accelerator.acceptance)
            result_nodes.append(acceptance_para)

        return result_nodes


def build_accelerator_content(slug: str, docname: str, hcd_context):
    """Build content nodes for an accelerator page."""
    from sphinx.addnodes import seealso

    from ...config import get_config

    config = get_config()
    prefix = path_to_root(docname)

    accelerator = hcd_context.accelerator_repo.get(slug)
    if not accelerator:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"Accelerator '{slug}' not found")
        return [para]

    # Get all entities for cross-references
    all_accelerators = hcd_context.accelerator_repo.list()
    all_apps = hcd_context.app_repo.list()
    all_stories = hcd_context.story_repo.list()
    all_journeys = hcd_context.journey_repo.list()
    all_integrations = hcd_context.integration_repo.list()
    all_code_infos = hcd_context.code_info_repo.list()

    result_nodes = []

    # Objective/description
    if accelerator.objective:
        obj_para = nodes.paragraph()
        obj_para += nodes.Text(accelerator.objective)
        result_nodes.append(obj_para)

    # Code info from introspection
    code_info = get_code_info_for_accelerator(accelerator, all_code_infos)
    if code_info:
        if code_info.entities:
            entities_para = nodes.paragraph()
            entities_para += nodes.strong(text="Entities: ")
            entities_para += nodes.Text(", ".join(e.name for e in code_info.entities))
            result_nodes.append(entities_para)

        if code_info.use_cases:
            uc_para = nodes.paragraph()
            uc_para += nodes.strong(text="Use Cases: ")
            uc_para += nodes.Text(", ".join(uc.name for uc in code_info.use_cases))
            result_nodes.append(uc_para)

    # Seealso with metadata
    seealso_node = seealso()

    # Status
    if accelerator.status:
        status_para = nodes.paragraph()
        status_para += nodes.strong(text="Status: ")
        status_para += nodes.Text(accelerator.status)
        seealso_node += status_para

    # Milestone
    if accelerator.milestone:
        milestone_para = nodes.paragraph()
        milestone_para += nodes.strong(text="Milestone: ")
        milestone_para += nodes.Text(accelerator.milestone)
        seealso_node += milestone_para

    # Apps
    apps = get_apps_for_accelerator(accelerator, all_apps)
    if apps:
        apps_para = nodes.paragraph()
        apps_para += nodes.strong(text="Apps: ")
        for i, app in enumerate(apps):
            app_path = f"{prefix}{config.get_doc_path('applications')}/{app.slug}.html"
            ref = nodes.reference("", "", refuri=app_path)
            ref += nodes.Text(app.name)
            apps_para += ref
            if i < len(apps) - 1:
                apps_para += nodes.Text(", ")
        seealso_node += apps_para

    # Sources from (integrations)
    source_integrations = get_source_integrations(accelerator, all_integrations)
    if source_integrations:
        sources_para = nodes.paragraph()
        sources_para += nodes.strong(text="Sources From: ")
        for i, integration in enumerate(source_integrations):
            int_path = f"{prefix}{config.get_doc_path('integrations')}/{integration.slug}.html"
            ref = nodes.reference("", "", refuri=int_path)
            ref += nodes.Text(integration.name)
            sources_para += ref
            if i < len(source_integrations) - 1:
                sources_para += nodes.Text(", ")
        seealso_node += sources_para

    # Publishes to (integrations)
    publish_integrations = get_publish_integrations(accelerator, all_integrations)
    if publish_integrations:
        publish_para = nodes.paragraph()
        publish_para += nodes.strong(text="Publishes To: ")
        for i, integration in enumerate(publish_integrations):
            int_path = f"{prefix}{config.get_doc_path('integrations')}/{integration.slug}.html"
            ref = nodes.reference("", "", refuri=int_path)
            ref += nodes.Text(integration.name)
            publish_para += ref
            if i < len(publish_integrations) - 1:
                publish_para += nodes.Text(", ")
        seealso_node += publish_para

    # Depends on (other accelerators)
    if accelerator.depends_on:
        depends_para = nodes.paragraph()
        depends_para += nodes.strong(text="Depends On: ")
        for i, dep_slug in enumerate(accelerator.depends_on):
            accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{dep_slug}.html"
            ref = nodes.reference("", "", refuri=accel_path)
            ref += nodes.Text(dep_slug.replace("-", " ").title())
            depends_para += ref
            if i < len(accelerator.depends_on) - 1:
                depends_para += nodes.Text(", ")
        seealso_node += depends_para

    # Fed by (accelerators that feed into this one)
    fed_by = get_fed_by_accelerators(accelerator, all_accelerators)
    if fed_by:
        fed_para = nodes.paragraph()
        fed_para += nodes.strong(text="Fed By: ")
        for i, feeder in enumerate(fed_by):
            accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{feeder.slug}.html"
            ref = nodes.reference("", "", refuri=accel_path)
            ref += nodes.Text(feeder.slug.replace("-", " ").title())
            fed_para += ref
            if i < len(fed_by) - 1:
                fed_para += nodes.Text(", ")
        seealso_node += fed_para

    result_nodes.append(seealso_node)
    return result_nodes


def build_accelerator_index(docname: str, hcd_context):
    """Build accelerator index grouped by status."""
    all_accelerators = hcd_context.accelerator_repo.list()

    if not all_accelerators:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No accelerators defined")
        return [para]

    # Group by status
    by_status: dict[str, list[Accelerator]] = {}
    for accel in all_accelerators:
        status = accel.status or "unknown"
        by_status.setdefault(status, []).append(accel)

    result_nodes = []

    for status in sorted(by_status.keys()):
        accelerators = by_status[status]

        # Status heading
        heading = nodes.paragraph()
        heading += nodes.strong(text=status.title())
        result_nodes.append(heading)

        # Accelerator list
        accel_list = nodes.bullet_list()

        for accel in sorted(accelerators, key=lambda a: a.slug):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Link to accelerator
            accel_path = f"{accel.slug}.html"
            ref = nodes.reference("", "", refuri=accel_path)
            ref += nodes.Text(accel.slug.replace("-", " ").title())
            para += ref

            if accel.milestone:
                para += nodes.Text(f" ({accel.milestone})")

            item += para
            accel_list += item

        result_nodes.append(accel_list)

    return result_nodes


def build_accelerators_for_app(app_slug: str, docname: str, hcd_context):
    """Build list of accelerators for an app."""
    from ...config import get_config

    config = get_config()
    prefix = path_to_root(docname)

    app = hcd_context.app_repo.get(app_slug)
    if not app:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"App '{app_slug}' not found")
        return [para]

    all_accelerators = hcd_context.accelerator_repo.list()

    # Filter to accelerators this app exposes
    matching = [a for a in all_accelerators if a.slug in (app.accelerators or [])]

    if not matching:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No accelerators for app '{app_slug}'")
        return [para]

    bullet_list = nodes.bullet_list()

    for accel in sorted(matching, key=lambda a: a.slug):
        item = nodes.list_item()
        para = nodes.paragraph()

        accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{accel.slug}.html"
        ref = nodes.reference("", "", refuri=accel_path)
        ref += nodes.Text(accel.slug.replace("-", " ").title())
        para += ref

        item += para
        bullet_list += item

    return [bullet_list]


def build_dependency_diagram(docname: str, hcd_context):
    """Build PlantUML diagram of accelerator dependencies."""
    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        para = nodes.paragraph()
        para += nodes.emphasis(text="PlantUML extension not available")
        return [para]

    all_accelerators = hcd_context.accelerator_repo.list()

    if not all_accelerators:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No accelerators defined")
        return [para]

    lines = [
        "@startuml",
        "skinparam componentStyle rectangle",
        "skinparam defaultTextAlignment center",
        "",
    ]

    accel_slugs = {a.slug for a in all_accelerators}

    # Declare components
    for accel in sorted(all_accelerators, key=lambda a: a.slug):
        accel_id = accel.slug.replace("-", "_")
        lines.append(f'component "{accel.slug.replace("-", " ").title()}" as {accel_id}')

    lines.append("")

    # Add dependency arrows
    for accel in sorted(all_accelerators, key=lambda a: a.slug):
        accel_id = accel.slug.replace("-", "_")

        for dep_slug in accel.depends_on:
            if dep_slug in accel_slugs:
                dep_id = dep_slug.replace("-", "_")
                lines.append(f"{accel_id} --> {dep_id}")

        for feed_slug in accel.feeds_into:
            if feed_slug in accel_slugs:
                feed_id = feed_slug.replace("-", "_")
                lines.append(f"{accel_id} --> {feed_id} : feeds")

    lines.append("")
    lines.append("@enduml")

    puml_source = "\n".join(lines)
    node = plantuml(puml_source)
    node["uml"] = puml_source
    node["incdir"] = os.path.dirname(docname)
    node["filename"] = os.path.basename(docname)

    return [node]


def clear_accelerator_state(app, env, docname):
    """Clear accelerator state when a document is re-read."""
    from ..context import get_hcd_context

    # Clear documented accelerators tracker
    if hasattr(env, "documented_accelerators") and docname in env.documented_accelerators:
        env.documented_accelerators.discard(docname)

    # Clear accelerators from this document via repository
    hcd_context = get_hcd_context(app)
    hcd_context.accelerator_repo.clear_by_docname(docname)


def process_accelerator_placeholders(app, doctree, docname):
    """Replace accelerator placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    # Process define-accelerator placeholders
    for node in doctree.traverse(DefineAcceleratorPlaceholder):
        slug = node["accelerator_slug"]
        content = build_accelerator_content(slug, docname, hcd_context)
        node.replace_self(content)

    # Process accelerator-index placeholders
    for node in doctree.traverse(AcceleratorIndexPlaceholder):
        content = build_accelerator_index(docname, hcd_context)
        node.replace_self(content)

    # Process accelerators-for-app placeholders
    for node in doctree.traverse(AcceleratorsForAppPlaceholder):
        app_slug = node["app_slug"]
        content = build_accelerators_for_app(app_slug, docname, hcd_context)
        node.replace_self(content)

    # Process accelerator-dependency-diagram placeholders
    for node in doctree.traverse(AcceleratorDependencyDiagramPlaceholder):
        content = build_dependency_diagram(docname, hcd_context)
        node.replace_self(content)

"""Accelerator directives for sphinx_supply_chain.

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

from apps.sphinx.hcd.directives.base import HCDDirective
from apps.sphinx.hcd.node_builders import (
    empty_result_paragraph,
    entity_bullet_list,
    link_list_paragraph,
    metadata_paragraph,
    problematic_paragraph,
)
from apps.sphinx.shared import path_to_root
from apps.sphinx.hcd.context import get_hcd_context
from julee.hcd.use_cases.crud import (
    GetAppRequest,
    ListAppsRequest,
    ListIntegrationsRequest,
)
from julee.supply_chain.use_cases.resolve_accelerator_references import (
    get_apps_for_accelerator,
    get_fed_by_accelerators,
    get_publish_integrations,
    get_source_integrations,
)
from julee.hcd.utils import (
    parse_integration_options,
    parse_list_option,
)
from julee.supply_chain.entities.accelerator import Accelerator
from julee.supply_chain.use_cases.crud import (
    CreateAcceleratorRequest,
    CreateAcceleratorUseCase,
    GetAcceleratorRequest,
    ListAcceleratorsRequest,
)

from ..context import get_supply_chain_context
from ..dependencies import get_create_accelerator_use_case


class DefineAcceleratorPlaceholder(nodes.General, nodes.Element):
    """Placeholder for define-accelerator, replaced at doctree-resolved."""

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
           :name: Vocabulary Catalog
           :status: active
           :milestone: MVP
           :acceptance: All vocab terms published to CDC
           :concepts: Term, Definition, Category
           :path: src/julee/vocab/
           :technology: Python
           :sources-from: kafka
           :publishes-to: elasticsearch
           :depends-on: document-processor
           :feeds-into: compliance-mapper

           Business objective description goes here.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "name": directives.unchanged,
        "status": directives.unchanged,
        "milestone": directives.unchanged,
        "acceptance": directives.unchanged,
        "concepts": directives.unchanged,
        "path": directives.unchanged,
        "technology": directives.unchanged,
        "sources-from": directives.unchanged,
        "publishes-to": directives.unchanged,
        "depends-on": directives.unchanged,
        "feeds-into": directives.unchanged,
    }

    def run(self):
        slug = self.arguments[0]
        docname = self.env.docname

        # Parse options
        name = self.options.get("name", "").strip()
        status = self.options.get("status", "").strip()
        milestone = self.options.get("milestone", "").strip() or None
        acceptance = self.options.get("acceptance", "").strip() or None
        concepts = parse_list_option(self.options.get("concepts", ""))
        bounded_context_path = self.options.get("path", "").strip()
        technology = self.options.get("technology", "").strip() or "Python"
        sources_from = parse_integration_options(self.options.get("sources-from", ""))
        publishes_to = parse_integration_options(self.options.get("publishes-to", ""))
        depends_on = parse_list_option(self.options.get("depends-on", ""))
        feeds_into = parse_list_option(self.options.get("feeds-into", ""))
        objective = "\n".join(self.content).strip()

        # Create accelerator via use case
        request = CreateAcceleratorRequest(
            slug=slug,
            name=name,
            status=status,
            milestone=milestone,
            acceptance=acceptance,
            objective=objective,
            domain_concepts=concepts,
            bounded_context_path=bounded_context_path,
            technology=technology,
            sources_from=[
                {"slug": s["slug"], "description": s.get("description") or ""}
                for s in sources_from
            ],
            publishes_to=[
                {"slug": p["slug"], "description": p.get("description") or ""}
                for p in publishes_to
            ],
            depends_on=depends_on,
            feeds_into=feeds_into,
            docname=docname,
            solution_slug=self.solution_slug,
        )
        supply_chain_ctx = get_supply_chain_context(self.env.app)
        use_case = get_create_accelerator_use_case(supply_chain_ctx)
        response = use_case.execute_sync(request)
        accelerator = response.accelerator

        # Track documented accelerators
        if not hasattr(self.env, "documented_accelerators"):
            self.env.documented_accelerators = set()
        self.env.documented_accelerators.add(slug)

        # Return placeholder - rendering in doctree-resolved
        node = DefineAcceleratorPlaceholder()
        node["accelerator_slug"] = slug
        return [node]


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
        response = self.hcd_context.get_accelerator.execute_sync(
            GetAcceleratorRequest(slug=slug)
        )
        accelerator = response.accelerator

        if not accelerator:
            return self.empty_result(f"Accelerator '{slug}' not found")

        result_nodes = []

        if accelerator.status:
            result_nodes.append(metadata_paragraph("Status", accelerator.status))

        if accelerator.milestone:
            result_nodes.append(metadata_paragraph("Milestone", accelerator.milestone))

        if accelerator.acceptance:
            result_nodes.append(metadata_paragraph("Acceptance", accelerator.acceptance))

        return result_nodes


def build_accelerator_content(slug: str, docname: str, hcd_context):
    """Build content nodes for an accelerator page."""
    from sphinx.addnodes import seealso

    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)

    accel_response = hcd_context.get_accelerator.execute_sync(
        GetAcceleratorRequest(slug=slug)
    )
    accelerator = accel_response.accelerator
    if not accelerator:
        return [problematic_paragraph(f"Accelerator '{slug}' not found")]

    # Get all entities for cross-references
    all_accelerators = hcd_context.list_accelerators.execute_sync(
        ListAcceleratorsRequest(solution_slug=solution)
    ).accelerators
    all_apps = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    ).apps
    all_integrations = hcd_context.list_integrations.execute_sync(
        ListIntegrationsRequest(solution_slug=solution)
    ).integrations

    result_nodes = []

    # Objective/description - parse as RST for formatting support
    if accelerator.objective:
        from .base import parse_rst_content

        obj_nodes = parse_rst_content(accelerator.objective, f"<{slug}>")
        result_nodes.extend(obj_nodes)

    # Seealso with metadata
    seealso_node = seealso()

    if accelerator.status:
        seealso_node += metadata_paragraph("Status", accelerator.status)

    if accelerator.milestone:
        seealso_node += metadata_paragraph("Milestone", accelerator.milestone)

    # Apps
    apps = get_apps_for_accelerator(accelerator, all_apps)
    if apps:
        seealso_node += link_list_paragraph(
            "Apps",
            apps,
            lambda app: (
                f"{prefix}{config.get_doc_path('applications')}/{app.slug}.html",
                app.name,
            ),
        )

    # Sources from (integrations)
    source_integrations = get_source_integrations(accelerator, all_integrations)
    if source_integrations:
        seealso_node += link_list_paragraph(
            "Sources From",
            source_integrations,
            lambda i: (
                f"{prefix}{config.get_doc_path('integrations')}/{i.slug}.html",
                i.name,
            ),
        )

    # Publishes to (integrations)
    publish_integrations = get_publish_integrations(accelerator, all_integrations)
    if publish_integrations:
        seealso_node += link_list_paragraph(
            "Publishes To",
            publish_integrations,
            lambda i: (
                f"{prefix}{config.get_doc_path('integrations')}/{i.slug}.html",
                i.name,
            ),
        )

    # Depends on (other accelerators)
    if accelerator.depends_on:
        seealso_node += link_list_paragraph(
            "Depends On",
            accelerator.depends_on,
            lambda dep_slug: (
                f"{prefix}{config.get_doc_path('accelerators')}/{dep_slug}.html",
                dep_slug.replace("-", " ").title(),
            ),
        )

    # Fed by (accelerators that feed into this one)
    fed_by = get_fed_by_accelerators(accelerator, all_accelerators)
    if fed_by:
        seealso_node += link_list_paragraph(
            "Fed By",
            fed_by,
            lambda feeder: (
                f"{prefix}{config.get_doc_path('accelerators')}/{feeder.slug}.html",
                feeder.slug.replace("-", " ").title(),
            ),
        )

    result_nodes.append(seealso_node)
    return result_nodes


def build_accelerator_index(docname: str, hcd_context):
    """Build accelerator index grouped by status."""
    from ..config import get_config
    from ..node_builders import grouped_bullet_lists

    config = get_config()
    solution = config.solution_slug
    all_accelerators = hcd_context.list_accelerators.execute_sync(
        ListAcceleratorsRequest(solution_slug=solution)
    ).accelerators

    if not all_accelerators:
        return [empty_result_paragraph("No accelerators defined")]

    # Group by status
    by_status: dict[str, list[Accelerator]] = {}
    for accel in all_accelerators:
        status = accel.status or "unknown"
        by_status.setdefault(status, []).append(accel)

    # Sort entities within each group
    for status in by_status:
        by_status[status] = sorted(by_status[status], key=lambda a: a.slug)

    # Build group order from actual statuses
    group_order = [(s, s.title()) for s in sorted(by_status.keys())]

    return grouped_bullet_lists(
        by_status,
        group_order,
        link_fn=lambda a: (f"{a.slug}.html", a.slug.replace("-", " ").title()),
        suffix_fn=lambda a: f" ({a.milestone})" if a.milestone else None,
    )


def build_accelerators_for_app(app_slug: str, docname: str, hcd_context):
    """Build list of accelerators for an app."""
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)

    app_response = hcd_context.get_app.execute_sync(GetAppRequest(slug=app_slug))
    app = app_response.app
    if not app:
        return [empty_result_paragraph(f"App '{app_slug}' not found")]

    all_accelerators = hcd_context.list_accelerators.execute_sync(
        ListAcceleratorsRequest(solution_slug=solution)
    ).accelerators

    # Filter to accelerators this app exposes
    matching = [a for a in all_accelerators if a.slug in (app.accelerators or [])]

    if not matching:
        return [empty_result_paragraph(f"No accelerators for app '{app_slug}'")]

    return [
        entity_bullet_list(
            sorted(matching, key=lambda a: a.slug),
            link_fn=lambda a: (
                f"{prefix}{config.get_doc_path('accelerators')}/{a.slug}.html",
                a.slug.replace("-", " ").title(),
            ),
        )
    ]


def build_dependency_diagram(docname: str, hcd_context):
    """Build PlantUML diagram of accelerator dependencies."""
    from ..config import get_config

    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        return [empty_result_paragraph("PlantUML extension not available")]

    config = get_config()
    solution = config.solution_slug
    all_accelerators = hcd_context.list_accelerators.execute_sync(
        ListAcceleratorsRequest(solution_slug=solution)
    ).accelerators

    if not all_accelerators:
        return [empty_result_paragraph("No accelerators defined")]

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
        lines.append(
            f'component "{accel.slug.replace("-", " ").title()}" as {accel_id}'
        )

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
    if (
        hasattr(env, "documented_accelerators")
        and docname in env.documented_accelerators
    ):
        env.documented_accelerators.discard(docname)

    # Clear accelerators from this document via repository
    hcd_context = get_hcd_context(app)
    hcd_context.accelerator_repo.run_async(
        hcd_context.accelerator_repo.async_repo.clear_by_docname(docname)
    )


# NOTE: process_accelerator_placeholders removed - now handled by
# infrastructure/handlers/placeholder_resolution.py via AcceleratorPlaceholderHandler

"""Sphinx extension for accelerators with code introspection.

Provides directives that introspect src/{slug}/ for ADR 001-compliant code
structure and cross-reference with apps, stories, and journeys.

Stage 1: Introspects src/{slug}/ for entities, use cases, protocols.
Stage 2 (future): Will inspect apps/worker/pipelines/ for pipeline treatment.

Provides directives:
- define-accelerator: Define accelerator with metadata + introspected code
- accelerator-index: Generate index table grouped by status
- accelerators-for-app: List accelerators an app exposes
- dependent-accelerators: List accelerators that depend on/publish to an integration
- accelerator-dependency-diagram: Generate PlantUML component diagram
- accelerator-status: Show status, milestone, and acceptance info
- src-accelerator-backlinks: Generate seealso links from autodoc back to docs
- src-app-backlinks: Generate seealso links from app autodoc pages back to docs
"""

import ast
import os
import re
from pathlib import Path
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

from .config import get_config
from .utils import (
    normalize_name, slugify, kebab_to_snake, path_to_root,
    parse_list_option, parse_integration_options
)

logger = logging.getLogger(__name__)

# Global registry for code introspection (populated at builder-inited, doesn't change)
_code_registry: dict = {}


def get_accelerator_registry(env):
    """Get the accelerator registry from env, creating if needed."""
    if not hasattr(env, 'accelerator_registry'):
        env.accelerator_registry = {}
    return env.accelerator_registry


def get_documented_accelerators(env):
    """Get the set of documented accelerators from env, creating if needed."""
    if not hasattr(env, 'documented_accelerators'):
        env.documented_accelerators = set()
    return env.documented_accelerators


def scan_python_classes(directory: Path) -> list[dict]:
    """Extract class names from Python files in a directory using AST."""
    if not directory.exists():
        return []

    classes = []
    for py_file in directory.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        try:
            with open(py_file) as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    first_line = docstring.split('\n')[0].strip() if docstring else ""
                    classes.append({
                        'name': node.name,
                        'docstring': first_line,
                        'file': py_file.name,
                    })
        except Exception as e:
            logger.warning(f"Could not parse {py_file}: {e}")

    return sorted(classes, key=lambda c: c['name'])


def get_module_docstring(module_path: Path) -> tuple[str | None, str | None]:
    """Extract module docstring from a Python file using AST."""
    if not module_path.exists():
        return None, None

    try:
        with open(module_path) as f:
            tree = ast.parse(f.read(), filename=str(module_path))
        docstring = ast.get_docstring(tree)
        if docstring:
            first_line = docstring.split('\n')[0].strip()
            return first_line, docstring
    except Exception as e:
        logger.warning(f"Could not parse {module_path}: {e}")

    return None, None


def scan_bounded_context(slug: str, project_root: Path) -> dict | None:
    """Introspect src/{slug}/ for ADR 001-compliant code structure."""
    snake_slug = kebab_to_snake(slug)
    config = get_config()
    src_dir = config.get_path('bounded_contexts')
    context_dir = src_dir / snake_slug

    if not context_dir.exists() and snake_slug != slug:
        context_dir = src_dir / slug
        if not context_dir.exists():
            return None
    elif not context_dir.exists():
        return None

    init_file = context_dir / "__init__.py"
    objective, full_docstring = get_module_docstring(init_file)

    return {
        'entities': scan_python_classes(context_dir / "domain" / "models"),
        'use_cases': scan_python_classes(context_dir / "use_cases"),
        'repository_protocols': scan_python_classes(context_dir / "domain" / "repositories"),
        'service_protocols': scan_python_classes(context_dir / "domain" / "services"),
        'has_infrastructure': (context_dir / "infrastructure").exists(),
        'code_dir': context_dir.name,
        'objective': objective,
        'docstring': full_docstring,
    }


def scan_code_structure(app):
    """Scan src/ for all bounded contexts at build init."""
    global _code_registry
    _code_registry = {}

    config = get_config()
    src_dir = config.get_path('bounded_contexts')

    if not src_dir.exists():
        logger.info("src/ directory not found - no code to introspect yet")
        return

    for context_dir in src_dir.iterdir():
        if not context_dir.is_dir():
            continue
        if context_dir.name.startswith((".", "_")):
            continue

        slug = context_dir.name
        code_info = scan_bounded_context(slug, config.project_root)
        if code_info:
            _code_registry[slug] = code_info
            logger.info(f"Introspected bounded context '{slug}': "
                       f"{len(code_info['entities'])} entities, "
                       f"{len(code_info['use_cases'])} use cases")


def get_apps_for_accelerator(accelerator_slug: str) -> list[str]:
    """Get apps that expose this accelerator (from app manifests)."""
    from . import apps
    _app_registry = apps.get_app_registry()

    result = []
    for app_slug, app_data in _app_registry.items():
        if accelerator_slug in app_data.get('accelerators', []):
            result.append(app_slug)
    return sorted(result)


def get_stories_for_accelerator(accelerator_slug: str) -> list[dict]:
    """Get stories for apps that use this accelerator."""
    from . import stories
    _story_registry = stories.get_story_registry()

    app_slugs = get_apps_for_accelerator(accelerator_slug)
    result = []

    for story in _story_registry:
        if story['app'] in app_slugs:
            result.append(story)

    return result


def get_journeys_for_accelerator(accelerator_slug: str, env) -> list[str]:
    """Get journeys that include stories from this accelerator's apps."""
    from . import journeys
    journey_registry = journeys.get_journey_registry(env)

    story_list = get_stories_for_accelerator(accelerator_slug)
    story_titles = {normalize_name(s['feature']) for s in story_list}

    result = []
    for slug, journey in journey_registry.items():
        for step in journey.get('steps', []):
            if step.get('type') == 'story':
                if normalize_name(step['ref']) in story_titles:
                    result.append(slug)
                    break

    return sorted(set(result))


class DefineAcceleratorDirective(SphinxDirective):
    """Define an accelerator with metadata and introspected code.

    Usage::

        .. define-accelerator:: vocabulary
           :status: alpha
           :milestone: 2 (Nov 2025)
           :acceptance: Reference environment deployed and accepted.
           :sources_from: pilot-data-collection (Scheme documentation, standards materials)
           :feeds_into: traceability, conformity
           :publishes_to: reference-implementation (SVC artefacts)

           Accelerate the creation of Sustainable Vocabulary Catalogs.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        'status': directives.unchanged,
        'milestone': directives.unchanged,
        'acceptance': directives.unchanged,
        'sources_from': directives.unchanged,
        'feeds_into': directives.unchanged,
        'publishes_to': directives.unchanged,
        'depends_on': directives.unchanged,
    }

    def run(self):
        slug = self.arguments[0]

        get_documented_accelerators(self.env).add(slug)

        status = self.options.get('status', '').strip()
        milestone = self.options.get('milestone', '').strip()
        acceptance = self.options.get('acceptance', '').strip()
        sources_from = parse_integration_options(self.options.get('sources_from', ''))
        feeds_into = parse_list_option(self.options.get('feeds_into', ''))
        publishes_to = parse_integration_options(self.options.get('publishes_to', ''))
        depends_on = parse_list_option(self.options.get('depends_on', ''))

        objective = '\n'.join(self.content).strip()

        get_accelerator_registry(self.env)[slug] = {
            'slug': slug,
            'status': status,
            'milestone': milestone,
            'acceptance': acceptance,
            'objective': objective,
            'sources_from': sources_from,
            'feeds_into': feeds_into,
            'publishes_to': publishes_to,
            'depends_on': depends_on,
            'docname': self.env.docname,
        }

        node = DefineAcceleratorPlaceholder()
        node['accelerator_slug'] = slug
        return [node]


class DefineAcceleratorPlaceholder(nodes.General, nodes.Element):
    pass


class AcceleratorIndexDirective(SphinxDirective):
    """Generate index table grouped by status."""

    def run(self):
        node = AcceleratorIndexPlaceholder()
        return [node]


class AcceleratorIndexPlaceholder(nodes.General, nodes.Element):
    pass


class AcceleratorStatusDirective(SphinxDirective):
    """Show status, milestone, and acceptance for an accelerator."""

    required_arguments = 1

    def run(self):
        node = AcceleratorStatusPlaceholder()
        node['accelerator_slug'] = self.arguments[0]
        return [node]


class AcceleratorStatusPlaceholder(nodes.General, nodes.Element):
    pass


class AcceleratorsForAppDirective(SphinxDirective):
    """List accelerators an app exposes."""

    required_arguments = 1

    def run(self):
        node = AcceleratorsForAppPlaceholder()
        node['app_slug'] = self.arguments[0]
        return [node]


class AcceleratorsForAppPlaceholder(nodes.General, nodes.Element):
    pass


class DependentAcceleratorsDirective(SphinxDirective):
    """List accelerators that depend on or publish to an integration."""

    option_spec = {
        'relationship': directives.unchanged_required,
    }

    def run(self):
        relationship = self.options.get('relationship', '').strip()
        if relationship not in ('sources_from', 'publishes_to'):
            error = self.state_machine.reporter.error(
                f"Invalid relationship '{relationship}'. "
                f"Must be 'sources_from' or 'publishes_to'.",
                line=self.lineno,
            )
            return [error]

        docname = self.env.docname
        integration_slug = docname.split('/')[-1]

        node = DependentAcceleratorsPlaceholder()
        node['integration_slug'] = integration_slug
        node['relationship'] = relationship
        return [node]


class DependentAcceleratorsPlaceholder(nodes.General, nodes.Element):
    pass


class AcceleratorDependencyDiagramDirective(SphinxDirective):
    """Generate a PlantUML component diagram showing accelerator dependencies."""

    required_arguments = 1

    def run(self):
        node = AcceleratorDependencyDiagramPlaceholder()
        node['accelerator_slug'] = self.arguments[0]
        return [node]


class AcceleratorDependencyDiagramPlaceholder(nodes.General, nodes.Element):
    pass


class SrcAcceleratorBacklinksDirective(SphinxDirective):
    """Generate seealso links from autodoc pages back to documentation."""

    required_arguments = 1

    def run(self):
        node = SrcAcceleratorBacklinksPlaceholder()
        node['accelerator_slug'] = self.arguments[0]
        return [node]


class SrcAcceleratorBacklinksPlaceholder(nodes.General, nodes.Element):
    pass


class SrcAppBacklinksDirective(SphinxDirective):
    """Generate seealso links from app autodoc pages back to documentation."""

    required_arguments = 1

    def run(self):
        node = SrcAppBacklinksPlaceholder()
        node['app_slug'] = self.arguments[0]
        return [node]


class SrcAppBacklinksPlaceholder(nodes.General, nodes.Element):
    pass


def build_accelerator_status(slug: str, env) -> list:
    """Build status/milestone/acceptance block for an accelerator."""
    accelerator_registry = get_accelerator_registry(env)

    if slug not in accelerator_registry:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"Accelerator '{slug}' not defined")
        return [para]

    accel = accelerator_registry[slug]
    result_nodes = []

    if accel['status'] or accel['milestone']:
        status_para = nodes.paragraph()
        if accel['status']:
            status_para += nodes.strong(text="Status: ")
            status_para += nodes.Text(accel['status'].title())
        if accel['status'] and accel['milestone']:
            status_para += nodes.Text(" | ")
        if accel['milestone']:
            status_para += nodes.strong(text="Milestone: ")
            status_para += nodes.Text(accel['milestone'])
        result_nodes.append(status_para)

    if accel['acceptance']:
        accept_para = nodes.paragraph()
        accept_para += nodes.strong(text="Acceptance: ")
        accept_para += nodes.Text(accel['acceptance'])
        result_nodes.append(accept_para)

    return result_nodes


def build_accelerator_content(slug: str, docname: str, env) -> list:
    """Build the content nodes for an accelerator page."""
    from sphinx.addnodes import seealso

    config = get_config()
    accelerator_registry = get_accelerator_registry(env)

    if slug not in accelerator_registry:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"Accelerator '{slug}' not defined")
        return [para]

    accel = accelerator_registry[slug]
    result_nodes = []

    prefix = path_to_root(docname)

    snake_slug = kebab_to_snake(slug)
    code_info = _code_registry.get(slug) or _code_registry.get(snake_slug)

    objective = None
    if code_info and code_info.get('objective'):
        objective = code_info['objective']
    elif accel['objective']:
        objective = accel['objective']

    if objective:
        obj_para = nodes.paragraph()
        obj_para += nodes.Text(objective)
        result_nodes.append(obj_para)

    seealso_items = []

    if code_info:
        code_dir = code_info.get('code_dir', snake_slug)
        autodoc_path = f"{prefix}source/_autosummary/rba.{code_dir}.html"
        seealso_items.append(('Source', [(autodoc_path, f"rba.{code_dir}", True)]))
    else:
        seealso_items.append(('Source', [(None, f"No implementation yet — expecting code at src/{snake_slug}/", False)]))

    apps = get_apps_for_accelerator(slug)
    if apps:
        app_links = []
        for app_slug in apps:
            app_path = f"{prefix}{config.get_doc_path('applications')}/{app_slug}.html"
            app_links.append((app_path, app_slug.replace("-", " ").title(), False))
        seealso_items.append(('Exposed By', app_links))

    journeys = get_journeys_for_accelerator(slug, env)
    if journeys:
        journey_links = []
        for journey_slug in journeys:
            journey_path = f"{prefix}{config.get_doc_path('journeys')}/{journey_slug}.html"
            journey_links.append((journey_path, journey_slug.replace("-", " ").title(), False))
        seealso_items.append(('Journeys', journey_links))

    if accel['depends_on']:
        accel_links = []
        for dep_slug in accel['depends_on']:
            if dep_slug in accelerator_registry:
                accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{dep_slug}.html"
                accel_links.append((accel_path, dep_slug.replace("-", " ").title(), False))
            else:
                accel_links.append((None, f"{dep_slug.replace('-', ' ').title()} [not found]", False))
        seealso_items.append(('Depends On', accel_links))

    if accel['feeds_into']:
        accel_links = []
        for feed_slug in accel['feeds_into']:
            if feed_slug in accelerator_registry:
                accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{feed_slug}.html"
                accel_links.append((accel_path, feed_slug.replace("-", " ").title(), False))
            else:
                accel_links.append((None, f"{feed_slug.replace('-', ' ').title()} [not found]", False))
        seealso_items.append(('Feeds Into', accel_links))

    if accel['sources_from']:
        int_links = []
        for source in accel['sources_from']:
            int_path = f"{prefix}{config.get_doc_path('integrations')}/{source['slug']}.html"
            label = source['slug'].replace("-", " ").title()
            int_links.append((int_path, label, False))
        seealso_items.append(('Sources From', int_links))

    if accel['publishes_to']:
        int_links = []
        for target in accel['publishes_to']:
            int_path = f"{prefix}{config.get_doc_path('integrations')}/{target['slug']}.html"
            label = target['slug'].replace("-", " ").title()
            int_links.append((int_path, label, False))
        seealso_items.append(('Publishes To', int_links))

    if seealso_items:
        seealso_node = seealso()

        for label, links in seealso_items:
            para = nodes.paragraph()
            para += nodes.strong(text=f"{label}: ")

            for i, (path, text, is_code) in enumerate(links):
                if path:
                    ref = nodes.reference("", "", refuri=path)
                    if is_code:
                        ref += nodes.literal(text=text)
                    else:
                        ref += nodes.Text(text)
                    para += ref
                else:
                    if is_code:
                        para += nodes.literal(text=text)
                    else:
                        para += nodes.emphasis(text=text)

                if i < len(links) - 1:
                    para += nodes.Text(", ")

            seealso_node += para

        result_nodes.append(seealso_node)

    return result_nodes


def build_accelerator_index(docname: str, env) -> list:
    """Build the accelerator index grouped by status."""
    accelerator_registry = get_accelerator_registry(env)

    if not accelerator_registry:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No accelerators defined")
        return [para]

    by_status = {'alpha': [], 'future': [], 'production': [], 'other': []}
    for slug, accel in accelerator_registry.items():
        status = accel.get('status', '').lower()
        if status in by_status:
            by_status[status].append((slug, accel))
        else:
            by_status['other'].append((slug, accel))

    result_nodes = []

    status_sections = [
        ('alpha', 'Alpha Phase'),
        ('production', 'Production'),
        ('future', 'Future'),
        ('other', 'Other'),
    ]

    for status_key, status_label in status_sections:
        accels = by_status.get(status_key, [])
        if not accels:
            continue

        heading = nodes.paragraph()
        heading += nodes.strong(text=status_label)
        result_nodes.append(heading)

        accel_list = nodes.bullet_list()

        for slug, accel in sorted(accels, key=lambda x: x[0]):
            item = nodes.list_item()
            para = nodes.paragraph()

            accel_path = f"{slug}.html"
            ref = nodes.reference("", "", refuri=accel_path)
            ref += nodes.Text(slug.replace("-", " ").title())
            para += ref

            if accel.get('milestone'):
                para += nodes.Text(f" — {accel['milestone']}")

            if slug in _code_registry:
                para += nodes.Text(" [code]")

            item += para

            if accel.get('objective'):
                obj_para = nodes.paragraph()
                obj_text = accel['objective']
                if len(obj_text) > 100:
                    obj_text = obj_text[:100] + "..."
                obj_para += nodes.Text(obj_text)
                item += obj_para

            accel_list += item

        result_nodes.append(accel_list)

    return result_nodes


def build_accelerators_for_app(app_slug: str, docname: str, env) -> list:
    """Build list of accelerators for an app."""
    from . import apps

    config = get_config()
    accelerator_registry = get_accelerator_registry(env)
    _app_registry = apps.get_app_registry()

    prefix = path_to_root(docname)

    app_data = _app_registry.get(app_slug)

    if not app_data:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"App '{app_slug}' not found")
        return [para]

    accel_slugs = app_data.get('accelerators', [])
    if not accel_slugs:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No accelerators")
        return [para]

    bullet_list = nodes.bullet_list()

    for slug in sorted(accel_slugs):
        item = nodes.list_item()
        para = nodes.paragraph()

        accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{slug}.html"
        ref = nodes.reference("", "", refuri=accel_path)
        ref += nodes.Text(slug.replace("-", " ").title())
        para += ref

        if slug in accelerator_registry:
            objective = accelerator_registry[slug].get('objective', '')
            if objective:
                para += nodes.Text(f" — {objective[:60]}...")

        item += para
        bullet_list += item

    return [bullet_list]


def build_dependent_accelerators(integration_slug: str, relationship: str, docname: str, env) -> list:
    """Build table of accelerators that depend on or publish to an integration."""
    config = get_config()
    accelerator_registry = get_accelerator_registry(env)

    prefix = path_to_root(docname)

    matches = []
    for accel_slug, accel in accelerator_registry.items():
        rel_list = accel.get(relationship, [])
        for rel in rel_list:
            if rel['slug'] == integration_slug:
                matches.append({
                    'slug': accel_slug,
                    'description': rel.get('description'),
                })
                break

    if not matches:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No accelerators found")
        return [para]

    table = nodes.table()
    tgroup = nodes.tgroup(cols=2)
    table += tgroup

    tgroup += nodes.colspec(colwidth=30)
    tgroup += nodes.colspec(colwidth=70)

    thead = nodes.thead()
    tgroup += thead
    header_row = nodes.row()
    thead += header_row

    accel_header = nodes.entry()
    accel_header += nodes.paragraph(text="Accelerator")
    header_row += accel_header

    data_header = nodes.entry()
    if relationship == 'sources_from':
        data_header += nodes.paragraph(text="What it sources")
    else:
        data_header += nodes.paragraph(text="What it publishes")
    header_row += data_header

    tbody = nodes.tbody()
    tgroup += tbody

    for match in sorted(matches, key=lambda m: m['slug']):
        row = nodes.row()
        tbody += row

        accel_cell = nodes.entry()
        accel_para = nodes.paragraph()
        accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{match['slug']}.html"
        ref = nodes.reference("", "", refuri=accel_path)
        ref += nodes.strong(text=match['slug'].replace("-", " ").title())
        accel_para += ref
        accel_cell += accel_para
        row += accel_cell

        desc_cell = nodes.entry()
        desc_para = nodes.paragraph()
        if match['description']:
            desc_para += nodes.Text(match['description'])
        else:
            desc_para += nodes.emphasis(text="(not specified)")
        desc_cell += desc_para
        row += desc_cell

    return [table]


def build_accelerator_dependency_diagram(slug: str, docname: str, env) -> list:
    """Build PlantUML component diagram for an accelerator."""
    from sphinxcontrib.plantuml import plantuml

    accelerator_registry = get_accelerator_registry(env)

    if slug not in accelerator_registry:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"Accelerator '{slug}' not defined")
        return [para]

    accel = accelerator_registry[slug]
    apps = get_apps_for_accelerator(slug)
    sources_from = accel.get('sources_from', [])
    publishes_to = accel.get('publishes_to', [])

    lines = [
        "@startuml",
        "skinparam componentStyle rectangle",
        "skinparam defaultTextAlignment center",
        "skinparam component {",
        "  BackgroundColor<<accelerator>> LightBlue",
        "  BackgroundColor<<app>> LightGreen",
        "  BackgroundColor<<integration>> LightYellow",
        "}",
        "",
    ]

    accel_title = slug.replace("-", " ").title()
    lines.append(f'title "{accel_title}" Dependencies')
    lines.append("")

    def safe_id(name):
        return name.replace("-", "_").replace(" ", "_")

    if apps:
        lines.append("' Applications that expose this accelerator")
        for app_slug in apps:
            app_id = safe_id(app_slug)
            app_name = app_slug.replace("-", " ").title()
            lines.append(f'component "{app_name}" as {app_id} <<app>>')
        lines.append("")

    lines.append("' The accelerator (bounded context)")
    accel_id = safe_id(slug)
    lines.append(f'component "{accel_title}" as {accel_id} <<accelerator>>')
    lines.append("")

    if sources_from or publishes_to:
        lines.append("' Integration dependencies")

        for source in sources_from:
            source_slug = source['slug']
            source_id = safe_id(source_slug)
            source_name = source_slug.replace("-", " ").title()
            lines.append(f'component "{source_name}" as {source_id} <<integration>>')

        for target in publishes_to:
            target_slug = target['slug']
            target_id = safe_id(target_slug)
            if not any(s['slug'] == target_slug for s in sources_from):
                target_name = target_slug.replace("-", " ").title()
                lines.append(f'component "{target_name}" as {target_id} <<integration>>')

        lines.append("")

    lines.append("' Dependencies")

    for app_slug in apps:
        app_id = safe_id(app_slug)
        lines.append(f"{app_id} --> {accel_id} : exposes")

    for source in sources_from:
        source_id = safe_id(source['slug'])
        label = "sources from"
        if source.get('description'):
            desc = source['description']
            if len(desc) > 30:
                desc = desc[:27] + "..."
            label = desc
        lines.append(f'{accel_id} --> {source_id} : "{label}"')

    for target in publishes_to:
        target_id = safe_id(target['slug'])
        label = "publishes to"
        if target.get('description'):
            desc = target['description']
            if len(desc) > 30:
                desc = desc[:27] + "..."
            label = desc
        lines.append(f'{accel_id} --> {target_id} : "{label}"')

    lines.append("")
    lines.append("@enduml")

    puml_source = "\n".join(lines)

    node = plantuml(puml_source)
    node['uml'] = puml_source
    node['incdir'] = os.path.dirname(docname)
    node['filename'] = os.path.basename(docname) + ".rst"

    return [node]


def build_accelerator_backlinks(slug: str, docname: str, env) -> nodes.Element:
    """Build seealso node with backlinks for an accelerator."""
    from sphinx.addnodes import seealso
    from . import apps

    config = get_config()
    accelerator_registry = get_accelerator_registry(env)
    _app_registry = apps.get_app_registry()

    prefix = path_to_root(docname)

    seealso_node = seealso()

    items = []

    accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{slug}.html"
    accel_data = accelerator_registry.get(slug, {})
    accel_desc = accel_data.get('objective', '').strip()
    if not accel_desc:
        accel_desc = f"Business accelerator for {slug.replace('-', ' ')} capabilities"
    if len(accel_desc) > 120:
        accel_desc = accel_desc[:117] + "..."
    items.append((accel_path, f"{slug.replace('-', ' ').title()} Accelerator", accel_desc))

    app_list = get_apps_for_accelerator(slug)
    for app_slug in app_list:
        app_path = f"{prefix}{config.get_doc_path('applications')}/{app_slug}.html"
        app_data = _app_registry.get(app_slug, {})
        app_desc = app_data.get('description', 'Application documentation')
        if len(app_desc) > 120:
            app_desc = app_desc[:117] + "..."
        items.append((app_path, app_data.get('name', app_slug.replace("-", " ").title()), app_desc))

    if app_list:
        for app_slug in app_list[:2]:
            story_path = f"{prefix}{config.get_doc_path('stories')}/{app_slug}.html"
            items.append((story_path, f"{app_slug.replace('-', ' ').title()} Stories", "User stories"))

    def_list = nodes.definition_list()
    for path, title, description in items:
        item = nodes.definition_list_item()

        term = nodes.term()
        ref = nodes.reference("", "", refuri=path)
        ref += nodes.Text(title)
        term += ref
        item += term

        definition = nodes.definition()
        para = nodes.paragraph()
        para += nodes.Text(description)
        definition += para
        item += definition

        def_list += item

    seealso_node += def_list
    return seealso_node


def build_app_backlinks(app_slug: str, docname: str, env) -> nodes.Element:
    """Build seealso node with backlinks for an app."""
    from sphinx.addnodes import seealso
    from . import apps, stories, journeys

    config = get_config()
    accelerator_registry = get_accelerator_registry(env)
    _app_registry = apps.get_app_registry()
    _apps_with_stories = stories.get_apps_with_stories()

    prefix = path_to_root(docname)

    seealso_node = seealso()

    items = []

    app_data = _app_registry.get(app_slug)

    if app_data:
        app_path = f"{prefix}{config.get_doc_path('applications')}/{app_slug}.html"
        app_desc = app_data.get('description', 'Application documentation')
        if len(app_desc) > 120:
            app_desc = app_desc[:117] + "..."
        items.append((app_path, app_data.get('name', app_slug.replace("-", " ").title()), app_desc))

        accelerators = app_data.get('accelerators', [])
        for accel_slug in accelerators[:4]:
            accel_path = f"{prefix}{config.get_doc_path('accelerators')}/{accel_slug}.html"
            accel_data = accelerator_registry.get(accel_slug, {})
            accel_desc = accel_data.get('objective', '').strip()
            if not accel_desc:
                accel_desc = f"Business accelerator for {accel_slug.replace('-', ' ')} capabilities"
            if len(accel_desc) > 120:
                accel_desc = accel_desc[:117] + "..."
            items.append((accel_path, f"{accel_slug.replace('-', ' ').title()} Accelerator", accel_desc))

    app_normalized = normalize_name(app_slug)
    if app_normalized in {normalize_name(a) for a in _apps_with_stories}:
        story_path = f"{prefix}{config.get_doc_path('stories')}/{app_slug}.html"
        items.append((story_path, f"{app_slug.replace('-', ' ').title()} Stories", "User stories"))

    def get_journeys_for_app_slug(slug):
        journey_registry = journeys.get_journey_registry(env)
        _story_registry = stories.get_story_registry()
        story_list = [s for s in _story_registry if normalize_name(s['app']) == normalize_name(slug)]
        story_titles = {normalize_name(s['feature']) for s in story_list}

        result = []
        for j_slug, journey in journey_registry.items():
            for step in journey.get('steps', []):
                if step.get('type') == 'story':
                    if normalize_name(step['ref']) in story_titles:
                        result.append(j_slug)
                        break
        return sorted(set(result))

    journey_list = get_journeys_for_app_slug(app_slug)
    for journey_slug in journey_list[:3]:
        journey_path = f"{prefix}{config.get_doc_path('journeys')}/{journey_slug}.html"
        items.append((journey_path, f"{journey_slug.replace('-', ' ').title()}", "User journey"))

    def_list = nodes.definition_list()
    for path, title, description in items:
        item = nodes.definition_list_item()

        term = nodes.term()
        ref = nodes.reference("", "", refuri=path)
        ref += nodes.Text(title)
        term += ref
        item += term

        definition = nodes.definition()
        para = nodes.paragraph()
        para += nodes.Text(description)
        definition += para
        item += definition

        def_list += item

    seealso_node += def_list
    return seealso_node


def validate_accelerators(app, env):
    """Validate accelerator coverage after all documents are read."""
    from . import apps

    _app_registry = apps.get_app_registry()
    documented_accelerators = get_documented_accelerators(env)

    referenced_accelerators = set()
    for app_data in _app_registry.values():
        for accel in app_data.get('accelerators', []):
            referenced_accelerators.add(accel)

    for accel in referenced_accelerators:
        if accel not in documented_accelerators:
            logger.warning(
                f"Accelerator '{accel}' in app manifest has no docs page. "
                f"Create domain/accelerators/{accel}.rst with '.. define-accelerator:: {accel}' "
                f"(or run 'make clean html' if the file exists)"
            )

    for slug in documented_accelerators:
        snake_slug = kebab_to_snake(slug)
        if slug not in _code_registry and snake_slug not in _code_registry:
            logger.info(
                f"Accelerator '{slug}' has no code yet (expected at src/{snake_slug}/)"
            )


def process_accelerator_placeholders(app, doctree, docname):
    """Replace all accelerator placeholders after all documents are read."""
    env = app.env

    for node in doctree.traverse(DefineAcceleratorPlaceholder):
        slug = node['accelerator_slug']
        content = build_accelerator_content(slug, docname, env)
        node.replace_self(content)

    for node in doctree.traverse(AcceleratorStatusPlaceholder):
        slug = node['accelerator_slug']
        content = build_accelerator_status(slug, env)
        node.replace_self(content)

    for node in doctree.traverse(AcceleratorIndexPlaceholder):
        content = build_accelerator_index(docname, env)
        node.replace_self(content)

    for node in doctree.traverse(AcceleratorsForAppPlaceholder):
        app_slug = node['app_slug']
        content = build_accelerators_for_app(app_slug, docname, env)
        node.replace_self(content)

    for node in doctree.traverse(DependentAcceleratorsPlaceholder):
        integration_slug = node['integration_slug']
        relationship = node['relationship']
        content = build_dependent_accelerators(integration_slug, relationship, docname, env)
        node.replace_self(content)

    for node in doctree.traverse(AcceleratorDependencyDiagramPlaceholder):
        slug = node['accelerator_slug']
        content = build_accelerator_dependency_diagram(slug, docname, env)
        node.replace_self(content)

    for node in doctree.traverse(SrcAcceleratorBacklinksPlaceholder):
        slug = node['accelerator_slug']
        content = build_accelerator_backlinks(slug, docname, env)
        node.replace_self([content])

    for node in doctree.traverse(SrcAppBacklinksPlaceholder):
        app_slug = node['app_slug']
        content = build_app_backlinks(app_slug, docname, env)
        node.replace_self([content])


def setup(app):
    app.connect("builder-inited", scan_code_structure)
    app.connect("env-check-consistency", validate_accelerators)
    app.connect("doctree-resolved", process_accelerator_placeholders)

    app.add_directive("define-accelerator", DefineAcceleratorDirective)
    app.add_directive("accelerator-index", AcceleratorIndexDirective)
    app.add_directive("accelerator-status", AcceleratorStatusDirective)
    app.add_directive("accelerators-for-app", AcceleratorsForAppDirective)
    app.add_directive("dependent-accelerators", DependentAcceleratorsDirective)
    app.add_directive("accelerator-dependency-diagram", AcceleratorDependencyDiagramDirective)
    app.add_directive("src-accelerator-backlinks", SrcAcceleratorBacklinksDirective)
    app.add_directive("src-app-backlinks", SrcAppBacklinksDirective)

    app.add_node(DefineAcceleratorPlaceholder)
    app.add_node(AcceleratorIndexPlaceholder)
    app.add_node(AcceleratorStatusPlaceholder)
    app.add_node(AcceleratorsForAppPlaceholder)
    app.add_node(DependentAcceleratorsPlaceholder)
    app.add_node(AcceleratorDependencyDiagramPlaceholder)
    app.add_node(SrcAcceleratorBacklinksPlaceholder)
    app.add_node(SrcAppBacklinksPlaceholder)

    return {
        "version": "1.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }

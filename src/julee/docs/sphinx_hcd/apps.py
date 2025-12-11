"""Sphinx extension for applications.

Scans apps/*/app.yaml for canonical app definitions and provides directives
to render app information with derived data (personas, journeys, epics, stories).

Provides directives:
- define-app: Render app info from YAML + derived data
- app-index: Generate index tables grouped by type
- apps-for-persona: List apps for a persona
"""

import yaml
from pathlib import Path
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

from .config import get_config
from .utils import normalize_name, slugify, path_to_root

logger = logging.getLogger(__name__)

# Global registry populated at build init
_app_registry: dict = {}


def get_app_registry() -> dict:
    """Get the app registry."""
    return _app_registry


def get_documented_apps(env) -> set:
    """Get documented apps set from env, creating if needed."""
    if not hasattr(env, 'documented_apps'):
        env.documented_apps = set()
    return env.documented_apps


def scan_app_manifests(app):
    """Scan apps/*/app.yaml and build the app registry."""
    global _app_registry
    _app_registry = {}

    config = get_config()
    project_root = config.project_root
    apps_dir = config.get_path('app_manifests')

    if not apps_dir.exists():
        logger.info(f"apps/ directory not found at {apps_dir} - no app manifests to index")
        return

    # Scan for app.yaml files
    for app_dir in apps_dir.iterdir():
        if not app_dir.is_dir():
            continue

        manifest_path = app_dir / "app.yaml"
        if not manifest_path.exists():
            continue

        app_slug = app_dir.name

        try:
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not read {manifest_path}: {e}")
            continue

        _app_registry[app_slug] = {
            'slug': app_slug,
            'name': manifest.get('name', app_slug.replace('-', ' ').title()),
            'type': manifest.get('type', 'unknown'),
            'status': manifest.get('status'),
            'description': manifest.get('description', '').strip(),
            'accelerators': manifest.get('accelerators', []),
            'manifest_path': str(manifest_path),
        }

    logger.info(f"Indexed {len(_app_registry)} apps from manifests")


def validate_apps(app, env):
    """Validate app coverage after all documents are read."""
    from . import stories

    documented_apps = get_documented_apps(env)
    _apps_with_stories = stories.get_apps_with_stories()

    # Check for apps without documentation
    for app_slug in _app_registry:
        if app_slug not in documented_apps:
            logger.warning(
                f"App '{app_slug}' from apps/{app_slug}/app.yaml has no docs page. "
                f"Create applications/{app_slug}.rst with '.. define-app:: {app_slug}' "
                f"(or run 'make clean html' if the file exists)"
            )

    # Check for apps without stories
    for app_slug in _app_registry:
        if app_slug not in _apps_with_stories:
            logger.info(
                f"App '{app_slug}' has no stories yet "
                f"(add .feature files to tests/e2e/{app_slug}/features/)"
            )

    # Check for documented apps without manifests
    for app_slug in documented_apps:
        if app_slug not in _app_registry:
            logger.warning(
                f"App '{app_slug}' documented but has no manifest. "
                f"Create apps/{app_slug}/app.yaml"
            )


def get_personas_for_app(app_slug: str, story_registry: list) -> list[str]:
    """Get personas that have stories for this app."""
    personas = set()
    app_normalized = normalize_name(app_slug)
    for story in story_registry:
        if story['app_normalized'] == app_normalized:
            personas.add(story['persona'])
    return sorted(personas)


def get_journeys_for_app(app_slug: str, story_registry: list, journey_registry: dict) -> list[str]:
    """Get journeys that include stories from this app."""
    # Get story titles for this app
    app_normalized = normalize_name(app_slug)
    app_story_titles = {
        normalize_name(s['feature'])
        for s in story_registry
        if s['app_normalized'] == app_normalized
    }

    # Find journeys that reference these stories
    journeys = []
    for slug, journey in journey_registry.items():
        for step in journey.get('steps', []):
            if step.get('type') == 'story':
                if normalize_name(step['ref']) in app_story_titles:
                    journeys.append(slug)
                    break

    return sorted(set(journeys))


def get_epics_for_app(app_slug: str, story_registry: list, epic_registry: dict) -> list[str]:
    """Get epics that include stories from this app."""
    # Get story titles for this app
    app_normalized = normalize_name(app_slug)
    app_story_titles = {
        normalize_name(s['feature'])
        for s in story_registry
        if s['app_normalized'] == app_normalized
    }

    # Find epics that reference these stories
    epics = []
    for slug, epic in epic_registry.items():
        for story_title in epic.get('stories', []):
            if normalize_name(story_title) in app_story_titles:
                epics.append(slug)
                break

    return sorted(set(epics))


class DefineAppDirective(SphinxDirective):
    """Render app info from YAML manifest plus derived data.

    Usage::

        .. define-app:: credential-tool
    """

    required_arguments = 1

    def run(self):
        app_slug = self.arguments[0]

        # Register that this app is documented (env-based for incremental builds)
        get_documented_apps(self.env).add(app_slug)

        # Return placeholder - actual rendering in doctree-resolved
        node = DefineAppPlaceholder()
        node['app_slug'] = app_slug
        return [node]


class DefineAppPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for define-app, replaced at doctree-resolved."""
    pass


class AppIndexDirective(SphinxDirective):
    """Generate index tables grouped by app type.

    Usage::

        .. app-index::
    """

    def run(self):
        node = AppIndexPlaceholder()
        return [node]


class AppIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for app-index, replaced at doctree-resolved."""
    pass


class AppsForPersonaDirective(SphinxDirective):
    """List apps for a specific persona.

    Usage::

        .. apps-for-persona:: Member Implementer
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        node = AppsForPersonaPlaceholder()
        node['persona'] = self.arguments[0]
        return [node]


class AppsForPersonaPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for apps-for-persona, replaced at doctree-resolved."""
    pass


def build_app_content(app_slug: str, docname: str, story_registry: list,
                      journey_registry: dict, epic_registry: dict, known_personas: set):
    """Build the content nodes for an app."""
    from sphinx.addnodes import seealso

    config = get_config()

    if app_slug not in _app_registry:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"App '{app_slug}' not found in apps/")
        return [para]

    app_data = _app_registry[app_slug]
    result_nodes = []

    prefix = path_to_root(docname)

    # Description first
    if app_data['description']:
        desc_para = nodes.paragraph()
        desc_para += nodes.Text(app_data['description'])
        result_nodes.append(desc_para)

    # Stories count and link
    app_stories = [s for s in story_registry if s['app_normalized'] == normalize_name(app_slug)]

    if app_stories:
        story_count = len(app_stories)
        stories_para = nodes.paragraph()
        stories_para += nodes.Text(f"The {app_data['name']} has ")
        story_path = f"{prefix}{config.get_doc_path('stories')}/{app_slug}.html"
        ref = nodes.reference("", "", refuri=story_path)
        ref += nodes.Text(f"{story_count} stories")
        stories_para += ref
        stories_para += nodes.Text(".")
        result_nodes.append(stories_para)

    # Build seealso box with metadata
    seealso_node = seealso()

    # Type
    type_labels = {
        'staff': 'Staff Application',
        'external': 'External Application',
        'member-tool': 'Member Tool',
    }
    type_para = nodes.paragraph()
    type_para += nodes.strong(text="Type: ")
    type_para += nodes.Text(type_labels.get(app_data['type'], app_data['type']))
    seealso_node += type_para

    # Status (if present)
    if app_data['status']:
        status_para = nodes.paragraph()
        status_para += nodes.strong(text="Status: ")
        status_para += nodes.Text(app_data['status'])
        seealso_node += status_para

    # Personas (derived from stories)
    personas = get_personas_for_app(app_slug, story_registry)
    if personas:
        persona_para = nodes.paragraph()
        persona_para += nodes.strong(text="Personas: ")
        for i, persona in enumerate(personas):
            persona_slug = slugify(persona)
            persona_path = f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"
            persona_normalized = normalize_name(persona)

            if persona_normalized in known_personas:
                ref = nodes.reference("", "", refuri=persona_path)
                ref += nodes.Text(persona)
                persona_para += ref
            else:
                persona_para += nodes.Text(persona)

            if i < len(personas) - 1:
                persona_para += nodes.Text(", ")

        seealso_node += persona_para

    # Related Journeys
    journeys = get_journeys_for_app(app_slug, story_registry, journey_registry)
    if journeys:
        journey_para = nodes.paragraph()
        journey_para += nodes.strong(text="Journeys: ")
        for i, journey_slug in enumerate(journeys):
            journey_path = f"{prefix}{config.get_doc_path('journeys')}/{journey_slug}.html"
            ref = nodes.reference("", "", refuri=journey_path)
            ref += nodes.Text(journey_slug.replace("-", " ").title())
            journey_para += ref
            if i < len(journeys) - 1:
                journey_para += nodes.Text(", ")
        seealso_node += journey_para

    # Related Epics
    epics = get_epics_for_app(app_slug, story_registry, epic_registry)
    if epics:
        epic_para = nodes.paragraph()
        epic_para += nodes.strong(text="Epics: ")
        for i, epic_slug in enumerate(epics):
            epic_path = f"{prefix}{config.get_doc_path('epics')}/{epic_slug}.html"
            ref = nodes.reference("", "", refuri=epic_path)
            ref += nodes.Text(epic_slug.replace("-", " ").title())
            epic_para += ref
            if i < len(epics) - 1:
                epic_para += nodes.Text(", ")
        seealso_node += epic_para

    result_nodes.append(seealso_node)

    return result_nodes


def build_app_index(docname: str, story_registry: list):
    """Build the app index grouped by type."""
    config = get_config()

    if not _app_registry:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No apps defined")
        return [para]

    prefix = path_to_root(docname)

    # Group apps by type
    by_type = {'staff': [], 'external': [], 'member-tool': []}
    for slug, app_data in _app_registry.items():
        app_type = app_data['type']
        if app_type in by_type:
            by_type[app_type].append((slug, app_data))
        else:
            by_type.setdefault(app_type, []).append((slug, app_data))

    result_nodes = []

    type_sections = [
        ('staff', 'Staff Applications'),
        ('external', 'External Applications'),
        ('member-tool', 'Member Tools'),
    ]

    for type_key, type_label in type_sections:
        apps = by_type.get(type_key, [])
        if not apps:
            continue

        # Section heading
        heading = nodes.paragraph()
        heading += nodes.strong(text=type_label)
        result_nodes.append(heading)

        # App list
        app_list = nodes.bullet_list()

        for slug, app_data in sorted(apps, key=lambda x: x[1]['name']):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Link to app
            app_path = f"{slug}.html"
            ref = nodes.reference("", "", refuri=app_path)
            ref += nodes.Text(app_data['name'])
            para += ref

            # Personas
            personas = get_personas_for_app(slug, story_registry)
            if personas:
                para += nodes.Text(f" ({', '.join(personas)})")

            item += para
            app_list += item

        result_nodes.append(app_list)

    return result_nodes


def build_apps_for_persona(docname: str, persona_arg: str, story_registry: list):
    """Build list of apps for a persona."""
    config = get_config()
    persona_normalized = normalize_name(persona_arg)

    prefix = path_to_root(docname)

    # Find apps that have stories for this persona
    matching_apps = []
    for slug in _app_registry:
        personas = get_personas_for_app(slug, story_registry)
        persona_names_normalized = {normalize_name(p) for p in personas}
        if persona_normalized in persona_names_normalized:
            matching_apps.append((slug, _app_registry[slug]))

    if not matching_apps:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No apps found for persona '{persona_arg}'")
        return [para]

    bullet_list = nodes.bullet_list()

    for slug, app_data in sorted(matching_apps, key=lambda x: x[1]['name']):
        item = nodes.list_item()
        para = nodes.paragraph()

        app_path = f"{prefix}{config.get_doc_path('applications')}/{slug}.html"
        ref = nodes.reference("", "", refuri=app_path)
        ref += nodes.Text(app_data['name'])
        para += ref

        item += para
        bullet_list += item

    return [bullet_list]


def process_app_placeholders(app, doctree, docname):
    """Replace app placeholders with rendered content."""
    from . import stories, journeys, epics

    env = app.env

    _story_registry = stories.get_story_registry()
    _known_personas = stories.get_known_personas()
    journey_registry = journeys.get_journey_registry(env)
    epic_registry = epics.get_epic_registry(env)

    # Process define-app placeholders
    for node in doctree.traverse(DefineAppPlaceholder):
        app_slug = node['app_slug']
        content = build_app_content(
            app_slug, docname, _story_registry,
            journey_registry, epic_registry, _known_personas
        )
        node.replace_self(content)

    # Process app-index placeholders
    for node in doctree.traverse(AppIndexPlaceholder):
        content = build_app_index(docname, _story_registry)
        node.replace_self(content)

    # Process apps-for-persona placeholders
    for node in doctree.traverse(AppsForPersonaPlaceholder):
        persona = node['persona']
        content = build_apps_for_persona(docname, persona, _story_registry)
        node.replace_self(content)


def setup(app):
    app.connect("builder-inited", scan_app_manifests)
    app.connect("env-check-consistency", validate_apps)
    app.connect("doctree-resolved", process_app_placeholders)

    app.add_directive("define-app", DefineAppDirective)
    app.add_directive("app-index", AppIndexDirective)
    app.add_directive("apps-for-persona", AppsForPersonaDirective)

    app.add_node(DefineAppPlaceholder)
    app.add_node(AppIndexPlaceholder)
    app.add_node(AppsForPersonaPlaceholder)

    return {
        "version": "1.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }

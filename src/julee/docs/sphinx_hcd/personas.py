"""Sphinx extension for persona diagrams.

Generates PlantUML use case diagrams dynamically from epic and story data.

Provides directives:
- persona-diagram: Generate UML diagram for a single persona showing their epics
- persona-index-diagram: Generate UML diagram for staff or external persona groups
"""

from collections import defaultdict
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

from .config import get_config
from .utils import normalize_name, slugify

logger = logging.getLogger(__name__)


def get_epics_for_persona(persona_name: str, epic_registry: dict, story_registry: list) -> list[tuple[str, dict]]:
    """Get epics that contain stories for a given persona.

    Args:
        persona_name: The persona name to match
        epic_registry: Dict of epic_slug -> epic_data
        story_registry: List of story dicts

    Returns:
        List of (epic_slug, epic_data) tuples for matching epics
    """
    persona_normalized = normalize_name(persona_name)

    # Build lookup of story title -> persona
    story_personas = {}
    for story in story_registry:
        story_personas[normalize_name(story['feature'])] = story['persona_normalized']

    matching_epics = []
    for slug, epic in epic_registry.items():
        # Check if any story in this epic belongs to the persona
        for story_title in epic.get('stories', []):
            story_normalized = normalize_name(story_title)
            if story_personas.get(story_normalized) == persona_normalized:
                matching_epics.append((slug, epic))
                break

    return sorted(matching_epics, key=lambda x: x[0])


def get_apps_for_epic(epic: dict, story_registry: list) -> set[str]:
    """Get the set of app slugs used by stories in an epic.

    Args:
        epic: Epic data dict with 'stories' list
        story_registry: List of story dicts

    Returns:
        Set of app slug strings
    """
    apps = set()

    # Build lookup of story title -> app
    story_apps = {}
    for story in story_registry:
        story_apps[normalize_name(story['feature'])] = story['app']

    for story_title in epic.get('stories', []):
        story_normalized = normalize_name(story_title)
        if story_normalized in story_apps:
            apps.add(story_apps[story_normalized])

    return apps


def get_apps_for_persona(persona_name: str, story_registry: list) -> set[str]:
    """Get the set of app slugs used by a persona.

    Args:
        persona_name: The persona name to match
        story_registry: List of story dicts

    Returns:
        Set of app slug strings
    """
    persona_normalized = normalize_name(persona_name)
    apps = set()

    for story in story_registry:
        if story['persona_normalized'] == persona_normalized:
            apps.add(story['app'])

    return apps


def generate_persona_plantuml(persona_name: str, epics: list[tuple[str, dict]],
                               story_registry: list, app_registry: dict) -> str:
    """Generate PlantUML for a single persona's use case diagram.

    Args:
        persona_name: Display name of the persona
        epics: List of (epic_slug, epic_data) tuples
        story_registry: List of story dicts
        app_registry: Dict of app_slug -> app_data

    Returns:
        PlantUML source string
    """
    persona_id = slugify(persona_name).replace('-', '_')

    lines = [
        f"@startuml persona-{slugify(persona_name)}",
        "left to right direction",
        "skinparam actorStyle awesome",
        "",
        f'actor "{persona_name}" as {persona_id}',
        "",
    ]

    # Collect all apps used by this persona's epics
    all_apps = set()
    epic_apps = {}  # epic_slug -> set of apps

    for epic_slug, epic in epics:
        apps = get_apps_for_epic(epic, story_registry)
        epic_apps[epic_slug] = apps
        all_apps.update(apps)

    # Generate component declarations for apps
    for app_slug in sorted(all_apps):
        app_id = app_slug.replace('-', '_')
        app_name = app_registry.get(app_slug, {}).get('name', app_slug.replace('-', ' ').title())
        lines.append(f'component "{app_name}" as {app_id}')

    lines.append("")

    # Generate usecase declarations for epics
    for epic_slug, epic in epics:
        epic_id = epic_slug.replace('-', '_')
        epic_name = epic_slug.replace('-', ' ').title()
        lines.append(f'usecase "{epic_name}" as {epic_id}')

    lines.append("")

    # Generate persona -> epic connections
    for epic_slug, epic in epics:
        epic_id = epic_slug.replace('-', '_')
        lines.append(f"{persona_id} --> {epic_id}")

    lines.append("")

    # Generate epic -> app connections
    for epic_slug, epic in epics:
        epic_id = epic_slug.replace('-', '_')
        for app_slug in sorted(epic_apps.get(epic_slug, [])):
            app_id = app_slug.replace('-', '_')
            lines.append(f"{epic_id} --> {app_id}")

    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)


def generate_persona_index_plantuml(persona_type: str, personas: list[str],
                                     epic_registry: dict, story_registry: list,
                                     app_registry: dict) -> str:
    """Generate PlantUML for a group of personas (staff or external).

    Args:
        persona_type: 'staff' or 'external'
        personas: List of persona names in this group
        epic_registry: Dict of epic_slug -> epic_data
        story_registry: List of story dicts
        app_registry: Dict of app_slug -> app_data

    Returns:
        PlantUML source string
    """
    lines = [
        f"@startuml persona-{persona_type}",
        "left to right direction",
        "skinparam actorStyle awesome",
        "",
    ]

    # Collect data for all personas
    persona_epics = {}  # persona -> list of epic slugs
    all_apps = set()
    epic_app_map = {}  # epic_slug -> set of apps

    for persona_name in personas:
        epics = get_epics_for_persona(persona_name, epic_registry, story_registry)
        persona_epics[persona_name] = [slug for slug, _ in epics]

        for epic_slug, epic in epics:
            if epic_slug not in epic_app_map:
                apps = get_apps_for_epic(epic, story_registry)
                epic_app_map[epic_slug] = apps
                all_apps.update(apps)

    # Generate actor declarations
    for persona_name in sorted(personas):
        persona_id = slugify(persona_name).replace('-', '_')
        lines.append(f'actor "{persona_name}" as {persona_id}')

    lines.append("")

    # Generate component declarations for apps
    for app_slug in sorted(all_apps):
        app_id = app_slug.replace('-', '_')
        app_name = app_registry.get(app_slug, {}).get('name', app_slug.replace('-', ' ').title())
        lines.append(f'component "{app_name}" as {app_id}')

    lines.append("")

    # Collect unique epics across all personas in this group
    all_epics = set()
    for epic_slugs in persona_epics.values():
        all_epics.update(epic_slugs)

    # Generate usecase declarations for epics
    for epic_slug in sorted(all_epics):
        epic_id = epic_slug.replace('-', '_')
        epic_name = epic_slug.replace('-', ' ').title()
        lines.append(f'usecase "{epic_name}" as {epic_id}')

    lines.append("")

    # Generate persona -> epic connections
    for persona_name in sorted(personas):
        persona_id = slugify(persona_name).replace('-', '_')
        for epic_slug in sorted(persona_epics.get(persona_name, [])):
            epic_id = epic_slug.replace('-', '_')
            lines.append(f"{persona_id} --> {epic_id}")

    lines.append("")

    # Generate epic -> app connections
    for epic_slug in sorted(all_epics):
        epic_id = epic_slug.replace('-', '_')
        for app_slug in sorted(epic_app_map.get(epic_slug, [])):
            app_id = app_slug.replace('-', '_')
            lines.append(f"{epic_id} --> {app_id}")

    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)


class PersonaDiagramDirective(SphinxDirective):
    """Generate PlantUML use case diagram for a single persona.

    Usage::

        .. persona-diagram:: Pilot Manager

    Generates a diagram showing:
    - The persona as an actor
    - Epics they participate in as use cases
    - Apps they interact with as components
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        persona_name = self.arguments[0]

        # Return placeholder - actual rendering in doctree-resolved
        node = PersonaDiagramPlaceholder()
        node['persona'] = persona_name
        return [node]


class PersonaDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for persona-diagram, replaced at doctree-resolved."""
    pass


class PersonaIndexDiagramDirective(SphinxDirective):
    """Generate PlantUML diagram for a group of personas.

    Usage::

        .. persona-index-diagram:: staff
        .. persona-index-diagram:: external

    Groups are determined by app type from app.yaml manifests:
    - staff: Personas using apps with type 'staff'
    - external: Personas using apps with type 'external' or 'member-tool'
    """

    required_arguments = 1
    option_spec = {}

    def run(self):
        group_type = self.arguments[0].lower()

        if group_type not in ('staff', 'external'):
            logger.warning(
                f"persona-index-diagram type must be 'staff' or 'external', "
                f"got '{group_type}' in {self.env.docname}"
            )

        # Return placeholder - actual rendering in doctree-resolved
        node = PersonaIndexDiagramPlaceholder()
        node['group_type'] = group_type
        return [node]


class PersonaIndexDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for persona-index-diagram, replaced at doctree-resolved."""
    pass


def get_personas_by_app_type(story_registry: list, app_registry: dict) -> dict[str, set[str]]:
    """Group personas by the type of apps they use.

    Args:
        story_registry: List of story dicts
        app_registry: Dict of app_slug -> app_data

    Returns:
        Dict with 'staff' and 'external' keys mapping to sets of persona names
    """
    personas_by_type = {'staff': set(), 'external': set()}

    for story in story_registry:
        app_slug = story['app']
        persona = story['persona']

        if persona == 'unknown':
            continue

        app_data = app_registry.get(app_slug, {})
        app_type = app_data.get('type', 'unknown')

        if app_type == 'staff':
            personas_by_type['staff'].add(persona)
        elif app_type in ('external', 'member-tool'):
            personas_by_type['external'].add(persona)

    return personas_by_type


def build_persona_diagram(persona_name: str, env, docname: str):
    """Build the PlantUML diagram for a single persona."""
    from . import stories, epics, apps
    from sphinxcontrib.plantuml import plantuml
    import os

    story_registry = stories.get_story_registry()
    epic_registry = epics.get_epic_registry(env)
    app_registry = apps.get_app_registry()

    # Get epics for this persona
    persona_epics = get_epics_for_persona(persona_name, epic_registry, story_registry)

    if not persona_epics:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No epics found for persona '{persona_name}'")
        return [para]

    # Generate PlantUML
    puml_source = generate_persona_plantuml(
        persona_name, persona_epics, story_registry, app_registry
    )

    # Create plantuml node with required attributes
    node = plantuml(puml_source)
    node['uml'] = puml_source
    node['incdir'] = os.path.dirname(docname)
    node['filename'] = os.path.basename(docname)

    return [node]


def build_persona_index_diagram(group_type: str, env, docname: str):
    """Build the PlantUML diagram for a persona group."""
    from . import stories, epics, apps
    from sphinxcontrib.plantuml import plantuml
    import os

    story_registry = stories.get_story_registry()
    epic_registry = epics.get_epic_registry(env)
    app_registry = apps.get_app_registry()

    # Get personas for this group type
    personas_by_type = get_personas_by_app_type(story_registry, app_registry)
    personas = sorted(personas_by_type.get(group_type, set()))

    if not personas:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No {group_type} personas found")
        return [para]

    # Generate PlantUML
    puml_source = generate_persona_index_plantuml(
        group_type, personas, epic_registry, story_registry, app_registry
    )

    # Create plantuml node with required attributes
    node = plantuml(puml_source)
    node['uml'] = puml_source
    node['incdir'] = os.path.dirname(docname)
    node['filename'] = os.path.basename(docname)

    return [node]


def process_persona_placeholders(app, doctree, docname):
    """Replace persona diagram placeholders with rendered content."""
    env = app.env

    # Process persona-diagram placeholders
    for node in doctree.traverse(PersonaDiagramPlaceholder):
        persona = node['persona']
        content = build_persona_diagram(persona, env, docname)
        node.replace_self(content)

    # Process persona-index-diagram placeholders
    for node in doctree.traverse(PersonaIndexDiagramPlaceholder):
        group_type = node['group_type']
        content = build_persona_index_diagram(group_type, env, docname)
        node.replace_self(content)


def setup(app):
    app.connect("doctree-resolved", process_persona_placeholders)

    app.add_directive("persona-diagram", PersonaDiagramDirective)
    app.add_directive("persona-index-diagram", PersonaIndexDiagramDirective)

    app.add_node(PersonaDiagramPlaceholder)
    app.add_node(PersonaIndexDiagramPlaceholder)

    return {
        "version": "1.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }

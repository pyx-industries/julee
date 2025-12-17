"""Persona directives for sphinx_hcd.

Generates PlantUML use case diagrams dynamically from epic and story data.

Provides directives:
- persona-diagram: Generate UML diagram for a single persona showing their epics
- persona-index-diagram: Generate UML diagram for staff or external persona groups
"""

import os

from docutils import nodes

from ...domain.use_cases import derive_personas, derive_personas_by_app_type, get_epics_for_persona
from ...utils import normalize_name, slugify
from .base import HCDDirective


class PersonaDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for persona-diagram, replaced at doctree-resolved."""

    pass


class PersonaIndexDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for persona-index-diagram, replaced at doctree-resolved."""

    pass


class PersonaDiagramDirective(HCDDirective):
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

        # Return placeholder - rendering in doctree-resolved
        node = PersonaDiagramPlaceholder()
        node["persona"] = persona_name
        return [node]


class PersonaIndexDiagramDirective(HCDDirective):
    """Generate PlantUML diagram for a group of personas.

    Usage::

        .. persona-index-diagram:: staff
        .. persona-index-diagram:: customers
        .. persona-index-diagram:: vendors

    Groups are determined by the type field from app.yaml manifests.
    """

    required_arguments = 1
    option_spec = {}

    def run(self):
        group_type = self.arguments[0].lower()

        # Return placeholder - rendering in doctree-resolved
        node = PersonaIndexDiagramPlaceholder()
        node["group_type"] = group_type
        return [node]


def get_apps_for_epic(epic, all_stories) -> set[str]:
    """Get the set of app slugs used by stories in an epic."""
    apps = set()

    # Build lookup of story title -> app
    story_apps = {}
    for story in all_stories:
        story_apps[normalize_name(story.feature_title)] = story.app_slug

    for story_title in epic.story_refs:
        story_normalized = normalize_name(story_title)
        if story_normalized in story_apps:
            apps.add(story_apps[story_normalized])

    return apps


def generate_persona_plantuml(persona, all_epics, all_stories, all_apps) -> str:
    """Generate PlantUML for a single persona's use case diagram."""
    persona_id = slugify(persona.name).replace("-", "_")
    app_lookup = {a.slug: a for a in all_apps}

    lines = [
        f"@startuml persona-{slugify(persona.name)}",
        "left to right direction",
        "skinparam actorStyle awesome",
        "",
        f'actor "{persona.name}" as {persona_id}',
        "",
    ]

    # Get epics for this persona
    epics = get_epics_for_persona(persona, all_epics, all_stories)

    # Collect all apps used by this persona's epics
    all_epic_apps = set()
    epic_apps_map = {}

    for epic in epics:
        apps = get_apps_for_epic(epic, all_stories)
        epic_apps_map[epic.slug] = apps
        all_epic_apps.update(apps)

    # Generate component declarations for apps
    for app_slug in sorted(all_epic_apps):
        app_id = app_slug.replace("-", "_")
        app = app_lookup.get(app_slug)
        app_name = app.name if app else app_slug.replace("-", " ").title()
        lines.append(f'component "{app_name}" as {app_id}')

    lines.append("")

    # Generate usecase declarations for epics
    for epic in epics:
        epic_id = epic.slug.replace("-", "_")
        epic_name = epic.slug.replace("-", " ").title()
        lines.append(f'usecase "{epic_name}" as {epic_id}')

    lines.append("")

    # Generate persona -> epic connections
    for epic in epics:
        epic_id = epic.slug.replace("-", "_")
        lines.append(f"{persona_id} --> {epic_id}")

    lines.append("")

    # Generate epic -> app connections
    for epic in epics:
        epic_id = epic.slug.replace("-", "_")
        for app_slug in sorted(epic_apps_map.get(epic.slug, [])):
            app_id = app_slug.replace("-", "_")
            lines.append(f"{epic_id} --> {app_id}")

    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)


def generate_persona_index_plantuml(
    group_type: str, personas, all_epics, all_stories, all_apps
) -> str:
    """Generate PlantUML for a group of personas."""
    app_lookup = {a.slug: a for a in all_apps}

    lines = [
        f"@startuml persona-{group_type}",
        "left to right direction",
        "skinparam actorStyle awesome",
        "",
    ]

    # Collect data for all personas
    persona_epics_map = {}
    all_epic_apps = set()
    epic_apps_map = {}

    for persona in personas:
        epics = get_epics_for_persona(persona, all_epics, all_stories)
        persona_epics_map[persona.name] = epics

        for epic in epics:
            if epic.slug not in epic_apps_map:
                apps = get_apps_for_epic(epic, all_stories)
                epic_apps_map[epic.slug] = apps
                all_epic_apps.update(apps)

    # Generate actor declarations
    for persona in sorted(personas, key=lambda p: p.name):
        persona_id = slugify(persona.name).replace("-", "_")
        lines.append(f'actor "{persona.name}" as {persona_id}')

    lines.append("")

    # Generate component declarations for apps
    for app_slug in sorted(all_epic_apps):
        app_id = app_slug.replace("-", "_")
        app = app_lookup.get(app_slug)
        app_name = app.name if app else app_slug.replace("-", " ").title()
        lines.append(f'component "{app_name}" as {app_id}')

    lines.append("")

    # Collect unique epics
    all_group_epics = set()
    for epics in persona_epics_map.values():
        all_group_epics.update(e.slug for e in epics)

    # Generate usecase declarations for epics
    for epic_slug in sorted(all_group_epics):
        epic_id = epic_slug.replace("-", "_")
        epic_name = epic_slug.replace("-", " ").title()
        lines.append(f'usecase "{epic_name}" as {epic_id}')

    lines.append("")

    # Generate persona -> epic connections
    for persona in sorted(personas, key=lambda p: p.name):
        persona_id = slugify(persona.name).replace("-", "_")
        for epic in sorted(persona_epics_map.get(persona.name, []), key=lambda e: e.slug):
            epic_id = epic.slug.replace("-", "_")
            lines.append(f"{persona_id} --> {epic_id}")

    lines.append("")

    # Generate epic -> app connections
    for epic_slug in sorted(all_group_epics):
        epic_id = epic_slug.replace("-", "_")
        for app_slug in sorted(epic_apps_map.get(epic_slug, [])):
            app_id = app_slug.replace("-", "_")
            lines.append(f"{epic_id} --> {app_id}")

    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)


def build_persona_diagram(persona_name: str, docname: str, hcd_context):
    """Build the PlantUML diagram for a single persona."""
    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        para = nodes.paragraph()
        para += nodes.emphasis(text="PlantUML extension not available")
        return [para]

    all_stories = hcd_context.story_repo.list_all()
    all_epics = hcd_context.epic_repo.list_all()
    all_apps = hcd_context.app_repo.list_all()

    # Derive personas
    personas = derive_personas(all_stories, all_epics)
    persona_normalized = normalize_name(persona_name)

    # Find the persona
    persona = None
    for p in personas:
        if p.normalized_name == persona_normalized:
            persona = p
            break

    if not persona:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No persona found: '{persona_name}'")
        return [para]

    # Check if persona has epics
    epics = get_epics_for_persona(persona, all_epics, all_stories)
    if not epics:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No epics found for persona '{persona_name}'")
        return [para]

    # Generate PlantUML
    puml_source = generate_persona_plantuml(persona, all_epics, all_stories, all_apps)

    # Create plantuml node
    node = plantuml(puml_source)
    node["uml"] = puml_source
    node["incdir"] = os.path.dirname(docname)
    node["filename"] = os.path.basename(docname)

    return [node]


def build_persona_index_diagram(group_type: str, docname: str, hcd_context):
    """Build the PlantUML diagram for a persona group."""
    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        para = nodes.paragraph()
        para += nodes.emphasis(text="PlantUML extension not available")
        return [para]

    all_stories = hcd_context.story_repo.list_all()
    all_epics = hcd_context.epic_repo.list_all()
    all_apps = hcd_context.app_repo.list_all()

    # Get personas grouped by app type
    personas_by_type = derive_personas_by_app_type(all_stories, all_epics, all_apps)
    personas = sorted(personas_by_type.get(group_type, []), key=lambda p: p.name)

    if not personas:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No {group_type} personas found")
        return [para]

    # Generate PlantUML
    puml_source = generate_persona_index_plantuml(
        group_type, personas, all_epics, all_stories, all_apps
    )

    # Create plantuml node
    node = plantuml(puml_source)
    node["uml"] = puml_source
    node["incdir"] = os.path.dirname(docname)
    node["filename"] = os.path.basename(docname)

    return [node]


def process_persona_placeholders(app, doctree, docname):
    """Replace persona diagram placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    # Process persona-diagram placeholders
    for node in doctree.traverse(PersonaDiagramPlaceholder):
        persona = node["persona"]
        content = build_persona_diagram(persona, docname, hcd_context)
        node.replace_self(content)

    # Process persona-index-diagram placeholders
    for node in doctree.traverse(PersonaIndexDiagramPlaceholder):
        group_type = node["group_type"]
        content = build_persona_index_diagram(group_type, docname, hcd_context)
        node.replace_self(content)

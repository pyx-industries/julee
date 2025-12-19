"""Persona directives for sphinx_hcd.

Provides directives:
- define-persona: Define a first-class persona with HCD metadata
- persona-diagram: Generate UML diagram for a single persona showing their epics
- persona-index-diagram: Generate UML diagram for staff or external persona groups
"""

import os

from docutils import nodes
from docutils.parsers.rst import directives

from ...domain.models.persona import Persona
from ...domain.use_cases import (
    derive_personas,
    derive_personas_by_app_type,
    get_epics_for_persona,
)
from ...utils import normalize_name, slugify
from .base import HCDDirective


class DefinePersonaPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for define-persona, replaced at doctree-resolved."""

    pass


class PersonaDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for persona-diagram, replaced at doctree-resolved."""

    pass


class PersonaIndexDiagramPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for persona-index-diagram, replaced at doctree-resolved."""

    pass


def parse_list_option(value: str) -> list[str]:
    """Parse a multi-line or comma-separated option into a list.

    Handles both:
    - Comma-separated: "item1, item2, item3"
    - Multi-line with bullets:
        - item1
        - item2
        - item3
    """
    if not value:
        return []

    items = []
    for line in value.strip().split("\n"):
        line = line.strip()
        # Remove bullet points
        if line.startswith("-"):
            line = line[1:].strip()
        if line:
            # Handle comma-separated on same line
            if "," in line and not line.startswith("-"):
                items.extend(item.strip() for item in line.split(",") if item.strip())
            else:
                items.append(line)
    return items


class DefinePersonaDirective(HCDDirective):
    """Define a first-class persona with HCD metadata.

    Usage::

        .. define-persona:: solutions-developer
           :name: Solutions Developer
           :goals:
              - Build reliable production systems
              - Minimize infrastructure boilerplate
           :frustrations:
              - Reinventing audit/retry patterns
              - Lack of visibility into workflow state
           :jobs-to-be-done:
              - Deploy new workflow to production
              - Debug failed workflow execution
           :context: Enterprise developer working with compliance requirements

    The slug (argument) is the URL-safe identifier. The :name: option is
    the human-readable name used in Gherkin stories ("As a {name}").
    """

    required_arguments = 1  # slug
    has_content = False
    option_spec = {
        "name": directives.unchanged_required,
        "goals": directives.unchanged,
        "frustrations": directives.unchanged,
        "jobs-to-be-done": directives.unchanged,
        "context": directives.unchanged,
    }

    def run(self):
        slug = self.arguments[0].strip()
        docname = self.env.docname

        # Parse options
        name = self.options.get("name", "").strip()
        goals = parse_list_option(self.options.get("goals", ""))
        frustrations = parse_list_option(self.options.get("frustrations", ""))
        jobs_to_be_done = parse_list_option(self.options.get("jobs-to-be-done", ""))
        context = self.options.get("context", "").strip()

        # Create and save persona
        persona = Persona.from_definition(
            slug=slug,
            name=name,
            goals=goals,
            frustrations=frustrations,
            jobs_to_be_done=jobs_to_be_done,
            context=context,
            docname=docname,
        )
        self.hcd_context.persona_repo.save(persona)

        # Return placeholder for rendering
        node = DefinePersonaPlaceholder()
        node["persona_slug"] = slug
        return [node]


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
        for epic in sorted(
            persona_epics_map.get(persona.name, []), key=lambda e: e.slug
        ):
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


def build_define_persona_content(persona_slug: str, docname: str, hcd_context):
    """Build the content for a defined persona.

    Renders the persona definition with its metadata.
    """
    persona = hcd_context.persona_repo.get(persona_slug)

    if not persona:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"Persona not found: '{persona_slug}'")
        return [para]

    # Build persona content
    result = []

    # Title
    title = nodes.rubric(text=persona.name)
    result.append(title)

    # Context (if provided)
    if persona.context:
        context_para = nodes.paragraph()
        context_para += nodes.Text(persona.context)
        result.append(context_para)

    # Goals (if provided)
    if persona.goals:
        goals_title = nodes.strong(text="Goals")
        goals_para = nodes.paragraph()
        goals_para += goals_title
        result.append(goals_para)

        goals_list = nodes.bullet_list()
        for goal in persona.goals:
            item = nodes.list_item()
            item_para = nodes.paragraph()
            item_para += nodes.Text(goal)
            item += item_para
            goals_list += item
        result.append(goals_list)

    # Frustrations (if provided)
    if persona.frustrations:
        frust_title = nodes.strong(text="Frustrations")
        frust_para = nodes.paragraph()
        frust_para += frust_title
        result.append(frust_para)

        frust_list = nodes.bullet_list()
        for frustration in persona.frustrations:
            item = nodes.list_item()
            item_para = nodes.paragraph()
            item_para += nodes.Text(frustration)
            item += item_para
            frust_list += item
        result.append(frust_list)

    # Jobs to be done (if provided)
    if persona.jobs_to_be_done:
        jtbd_title = nodes.strong(text="Jobs to be Done")
        jtbd_para = nodes.paragraph()
        jtbd_para += jtbd_title
        result.append(jtbd_para)

        jtbd_list = nodes.bullet_list()
        for job in persona.jobs_to_be_done:
            item = nodes.list_item()
            item_para = nodes.paragraph()
            item_para += nodes.Text(job)
            item += item_para
            jtbd_list += item
        result.append(jtbd_list)

    return result


def process_persona_placeholders(app, doctree, docname):
    """Replace persona placeholders with rendered content."""
    from ..context import get_hcd_context

    hcd_context = get_hcd_context(app)

    # Process define-persona placeholders
    for node in doctree.traverse(DefinePersonaPlaceholder):
        persona_slug = node["persona_slug"]
        content = build_define_persona_content(persona_slug, docname, hcd_context)
        node.replace_self(content)

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

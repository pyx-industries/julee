"""Sphinx extension for defining and cross-referencing epics.

Provides directives:
- define-epic: Define an epic with description
- epic-story: Reference a story as part of the epic
- epic-index: Render index of all epics
- epics-for-persona: List epics for a persona (derived from stories)
"""

from docutils import nodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from .config import get_config
from .utils import normalize_name, path_to_root

logger = logging.getLogger(__name__)


def get_epic_registry(env):
    """Get or create the epic registry on the environment."""
    if not hasattr(env, "epic_registry"):
        env.epic_registry = {}
    return env.epic_registry


def get_current_epic(env):
    """Get or create the current epic tracker on the environment."""
    if not hasattr(env, "epic_current"):
        env.epic_current = {}
    return env.epic_current


class DefineEpicDirective(SphinxDirective):
    """Define an epic with description.

    Usage::

        .. define-epic:: credential-creation

           Covers the creation, attachment, and verification of UNTP-compliant
           credentials including DPPs, DFRs, and DCCs.
    """

    required_arguments = 1  # epic slug
    has_content = True
    option_spec = {}

    def run(self):
        epic_slug = self.arguments[0]
        docname = self.env.docname

        # Description is the directive content
        description = "\n".join(self.content).strip()

        # Register the epic in environment
        epic_registry = get_epic_registry(self.env)
        current_epic = get_current_epic(self.env)

        epic_data = {
            "slug": epic_slug,
            "description": description,
            "stories": [],  # Will be populated by epic-story
            "docname": docname,
        }
        epic_registry[epic_slug] = epic_data
        current_epic[docname] = epic_slug

        # Build output nodes
        result_nodes = []

        # Description paragraph
        if description:
            desc_para = nodes.paragraph(text=description)
            result_nodes.append(desc_para)

        # Add a placeholder for stories (will be filled in doctree-resolved)
        stories_placeholder = nodes.container()
        stories_placeholder["classes"].append("epic-stories-placeholder")
        stories_placeholder["epic_slug"] = epic_slug
        result_nodes.append(stories_placeholder)

        return result_nodes


class EpicStoryDirective(SphinxDirective):
    """Reference a story as part of the epic.

    Usage::

        .. epic-story:: Create DPP from Product Sheet
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        story_title = self.arguments[0]
        docname = self.env.docname

        # Add to current epic's stories
        epic_registry = get_epic_registry(self.env)
        current_epic = get_current_epic(self.env)

        epic_slug = current_epic.get(docname)
        if epic_slug and epic_slug in epic_registry:
            epic_registry[epic_slug]["stories"].append(story_title)

        # Return empty - rendering happens in doctree-resolved
        return []


class EpicIndexDirective(SphinxDirective):
    """Render index of all epics.

    Usage::

        .. epic-index::
    """

    def run(self):
        # Return placeholder - actual rendering in doctree-resolved
        node = EpicIndexPlaceholder()
        return [node]


class EpicIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for epic index, replaced at doctree-resolved."""

    pass


class EpicsForPersonaDirective(SphinxDirective):
    """List epics for a specific persona (derived from stories).

    Usage::

        .. epics-for-persona:: Member Implementer
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        # Return placeholder - actual rendering in doctree-resolved
        node = EpicsForPersonaPlaceholder()
        node["persona"] = self.arguments[0]
        return [node]


class EpicsForPersonaPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for epics-for-persona, replaced at doctree-resolved."""

    pass


def clear_epic_state(app, env, docname):
    """Clear epic state when a document is re-read."""
    current_epic = get_current_epic(env)
    epic_registry = get_epic_registry(env)

    if docname in current_epic:
        del current_epic[docname]

    # Remove epics defined in this document
    to_remove = [slug for slug, e in epic_registry.items() if e["docname"] == docname]
    for slug in to_remove:
        del epic_registry[slug]


def validate_epics(app, env):
    """Validate epic references after all documents are read."""
    from . import stories

    epic_registry = get_epic_registry(env)
    _story_registry = stories.get_story_registry()
    story_titles = {normalize_name(s["feature"]) for s in _story_registry}

    for slug, epic in epic_registry.items():
        # Validate story references
        for story_title in epic["stories"]:
            if normalize_name(story_title) not in story_titles:
                logger.warning(
                    f"Epic '{slug}' references unknown story: '{story_title}'"
                )


def get_personas_for_epic(epic: dict, story_registry: list) -> set[str]:
    """Get the set of personas for an epic based on its stories."""
    personas = set()
    for story_title in epic["stories"]:
        story_normalized = normalize_name(story_title)
        for story in story_registry:
            if normalize_name(story["feature"]) == story_normalized:
                personas.add(story["persona"])
                break
    return personas


def render_epic_stories(
    epic: dict, docname: str, story_registry: list, known_personas: set
):
    """Render epic stories as a simple bullet list."""
    from . import stories

    config = get_config()
    _known_apps = stories.get_known_apps()

    stories_data = []
    for story_title in epic["stories"]:
        story_normalized = normalize_name(story_title)
        for story in story_registry:
            if normalize_name(story["feature"]) == story_normalized:
                stories_data.append(story)
                break

    if not stories_data:
        return None

    # Calculate paths
    prefix = path_to_root(docname)

    result_nodes = []

    # Stories heading
    stories_heading = nodes.paragraph()
    stories_heading += nodes.strong(text="Stories")
    result_nodes.append(stories_heading)

    # Simple bullet list: "story name (App Name)"
    story_list = nodes.bullet_list()

    for story in sorted(stories_data, key=lambda s: s["feature"].lower()):
        story_item = nodes.list_item()
        story_para = nodes.paragraph()

        # Story link
        story_para += stories.make_story_reference(story, docname)

        # App in parentheses
        story_para += nodes.Text(" (")
        app_path = f"{prefix}{config.get_doc_path('applications')}/{story['app']}.html"
        app_valid = story["app_normalized"] in _known_apps

        if app_valid:
            app_ref = nodes.reference("", "", refuri=app_path)
            app_ref += nodes.Text(story["app"].replace("-", " ").title())
            story_para += app_ref
        else:
            story_para += nodes.Text(story["app"].replace("-", " ").title())

        story_para += nodes.Text(")")

        story_item += story_para
        story_list += story_item

    result_nodes.append(story_list)

    return result_nodes


def process_epic_placeholders(app, doctree, docname):
    """Replace epic placeholders with rendered content."""
    from . import stories

    get_config()
    env = app.env
    epic_registry = get_epic_registry(env)
    current_epic = get_current_epic(env)
    _story_registry = stories.get_story_registry()
    _known_personas = stories.get_known_personas()

    # Process epic stories placeholder
    epic_slug = current_epic.get(docname)
    if epic_slug and epic_slug in epic_registry:
        epic = epic_registry[epic_slug]

        for node in doctree.traverse(nodes.container):
            if "epic-stories-placeholder" in node.get("classes", []):
                stories_nodes = render_epic_stories(
                    epic, docname, _story_registry, _known_personas
                )
                if stories_nodes:
                    node.replace_self(stories_nodes)
                else:
                    node.replace_self([])
                break

    # Process epic index placeholder
    for node in doctree.traverse(EpicIndexPlaceholder):
        index_node = build_epic_index(env, docname, _story_registry)
        node.replace_self(index_node)

    # Process epics-for-persona placeholder
    for node in doctree.traverse(EpicsForPersonaPlaceholder):
        persona = node["persona"]
        epics_node = build_epics_for_persona(env, docname, persona, _story_registry)
        node.replace_self(epics_node)


def build_epic_index(env, docname: str, story_registry: list):
    """Build the epic index listing all epics, plus unassigned stories."""
    from . import stories

    config = get_config()
    epic_registry = get_epic_registry(env)
    _known_apps = stories.get_known_apps()

    if not epic_registry:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No epics defined")
        return [para]

    result_nodes = []
    bullet_list = nodes.bullet_list()

    # Collect all stories assigned to epics
    assigned_stories = set()
    for epic in epic_registry.values():
        for story_title in epic["stories"]:
            assigned_stories.add(normalize_name(story_title))

    for slug in sorted(epic_registry.keys()):
        epic = epic_registry[slug]

        item = nodes.list_item()
        para = nodes.paragraph()

        # Link to epic
        epic_path = f"{slug}.html"
        epic_ref = nodes.reference("", "", refuri=epic_path)
        epic_ref += nodes.Text(slug.replace("-", " ").title())
        para += epic_ref

        # Story count
        story_count = len(epic["stories"])
        para += nodes.Text(f" ({story_count} stories)")

        item += para
        bullet_list += item

    result_nodes.append(bullet_list)

    # Find unassigned stories
    unassigned_stories = []
    for story in story_registry:
        if normalize_name(story["feature"]) not in assigned_stories:
            unassigned_stories.append(story)

    if unassigned_stories:
        # Calculate paths
        prefix = path_to_root(docname)

        # Add section heading
        heading = nodes.paragraph()
        heading += nodes.strong(text="Unassigned Stories")
        result_nodes.append(heading)

        intro = nodes.paragraph()
        intro += nodes.Text(
            f"{len(unassigned_stories)} stories not yet assigned to an epic:"
        )
        result_nodes.append(intro)

        # List unassigned stories
        unassigned_list = nodes.bullet_list()
        for story in sorted(unassigned_stories, key=lambda s: s["feature"].lower()):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Story link
            para += stories.make_story_reference(story, docname)

            # App in parentheses
            para += nodes.Text(" (")
            app_path = (
                f"{prefix}{config.get_doc_path('applications')}/{story['app']}.html"
            )
            app_valid = story["app_normalized"] in _known_apps

            if app_valid:
                app_ref = nodes.reference("", "", refuri=app_path)
                app_ref += nodes.Text(story["app"].replace("-", " ").title())
                para += app_ref
            else:
                para += nodes.Text(story["app"].replace("-", " ").title())

            para += nodes.Text(")")

            item += para
            unassigned_list += item

        result_nodes.append(unassigned_list)

    return result_nodes


def build_epics_for_persona(env, docname: str, persona_arg: str, story_registry: list):
    """Build list of epics for a persona."""
    config = get_config()
    epic_registry = get_epic_registry(env)
    persona_normalized = normalize_name(persona_arg)

    prefix = path_to_root(docname)

    # Find epics that contain stories for this persona
    matching_epics = []
    for slug, epic in epic_registry.items():
        personas = get_personas_for_epic(epic, story_registry)
        persona_names_normalized = {normalize_name(p) for p in personas}
        if persona_normalized in persona_names_normalized:
            matching_epics.append((slug, epic))

    if not matching_epics:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No epics found for persona '{persona_arg}'")
        return [para]

    bullet_list = nodes.bullet_list()

    for slug, _epic in sorted(matching_epics, key=lambda x: x[0]):
        item = nodes.list_item()
        para = nodes.paragraph()

        epic_path = f"{prefix}{config.get_doc_path('epics')}/{slug}.html"
        epic_ref = nodes.reference("", "", refuri=epic_path)
        epic_ref += nodes.Text(slug.replace("-", " ").title())
        para += epic_ref

        item += para
        bullet_list += item

    return [bullet_list]


def setup(app):
    app.connect("env-purge-doc", clear_epic_state)
    app.connect("env-check-consistency", validate_epics)
    app.connect("doctree-resolved", process_epic_placeholders)

    app.add_directive("define-epic", DefineEpicDirective)
    app.add_directive("epic-story", EpicStoryDirective)
    app.add_directive("epic-index", EpicIndexDirective)
    app.add_directive("epics-for-persona", EpicsForPersonaDirective)

    app.add_node(EpicIndexPlaceholder)
    app.add_node(EpicsForPersonaPlaceholder)

    return {
        "version": "1.0",
        "parallel_read_safe": False,  # Uses global state
        "parallel_write_safe": True,
    }

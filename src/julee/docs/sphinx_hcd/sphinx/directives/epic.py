"""Epic directives for sphinx_hcd.

Provides directives for defining and cross-referencing epics:
- define-epic: Define an epic with description
- epic-story: Reference a story as part of the epic
- epic-index: Render index of all epics
- epics-for-persona: List epics for a persona (derived from stories)
"""

from docutils import nodes

from ...domain.models.epic import Epic
from ...domain.use_cases import get_epics_for_persona, derive_personas
from ...utils import normalize_name, path_to_root
from .base import HCDDirective


class EpicIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for epic index, replaced at doctree-resolved."""

    pass


class EpicsForPersonaPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for epics-for-persona, replaced at doctree-resolved."""

    pass


class DefineEpicDirective(HCDDirective):
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
        description = "\n".join(self.content).strip()

        # Create and register the epic entity
        epic = Epic(
            slug=epic_slug,
            description=description,
            story_refs=[],  # Will be populated by epic-story
            docname=docname,
        )

        # Add to repository
        self.hcd_context.epic_repo.add(epic)

        # Track current epic in environment for epic-story
        if not hasattr(self.env, "epic_current"):
            self.env.epic_current = {}
        self.env.epic_current[docname] = epic_slug

        # Build output nodes
        result_nodes = []

        if description:
            desc_para = nodes.paragraph(text=description)
            result_nodes.append(desc_para)

        # Add a placeholder for stories (filled in doctree-resolved)
        stories_placeholder = nodes.container()
        stories_placeholder["classes"].append("epic-stories-placeholder")
        stories_placeholder["epic_slug"] = epic_slug
        result_nodes.append(stories_placeholder)

        return result_nodes


class EpicStoryDirective(HCDDirective):
    """Reference a story as part of the epic.

    Usage::

        .. epic-story:: Create DPP from Product Sheet
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        story_title = self.arguments[0]
        docname = self.env.docname

        # Get current epic
        epic_current = getattr(self.env, "epic_current", {})
        epic_slug = epic_current.get(docname)

        if epic_slug:
            # Get the epic from repository and update story_refs
            epic = self.hcd_context.epic_repo.get(epic_slug)
            if epic:
                # Add story to epic's story_refs
                if story_title not in epic.story_refs:
                    epic.story_refs.append(story_title)

        # Return empty - rendering happens in doctree-resolved
        return []


class EpicIndexDirective(HCDDirective):
    """Render index of all epics.

    Usage::

        .. epic-index::
    """

    def run(self):
        # Return placeholder - actual rendering in doctree-resolved
        node = EpicIndexPlaceholder()
        return [node]


class EpicsForPersonaDirective(HCDDirective):
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


def render_epic_stories(epic: Epic, docname: str, hcd_context):
    """Render epic stories as a simple bullet list."""
    from ...config import get_config
    from .story import StoryListForPersonaDirective

    config = get_config()
    prefix = path_to_root(docname)

    # Get all stories
    all_stories = hcd_context.story_repo.list()
    all_apps = hcd_context.app_repo.list()
    known_apps = {normalize_name(a.name) for a in all_apps}

    # Find stories referenced by this epic
    stories_data = []
    for story_title in epic.story_refs:
        story_normalized = normalize_name(story_title)
        for story in all_stories:
            if normalize_name(story.feature_title) == story_normalized:
                stories_data.append(story)
                break

    if not stories_data:
        return None

    result_nodes = []

    # Stories heading
    stories_heading = nodes.paragraph()
    stories_heading += nodes.strong(text="Stories")
    result_nodes.append(stories_heading)

    # Simple bullet list
    story_list = nodes.bullet_list()

    for story in sorted(stories_data, key=lambda s: s.feature_title.lower()):
        story_item = nodes.list_item()
        story_para = nodes.paragraph()

        # Build story link manually
        story_doc = f"{config.get_doc_path('stories')}/{story.app_slug}"
        story_ref_uri = _build_relative_uri(docname, story_doc, story.slug)
        story_ref = nodes.reference("", "", refuri=story_ref_uri)
        story_ref += nodes.Text(story.i_want)
        story_para += story_ref

        # App in parentheses
        story_para += nodes.Text(" (")
        app_path = f"{prefix}{config.get_doc_path('applications')}/{story.app_slug}.html"
        app_valid = story.app_normalized in known_apps

        if app_valid:
            app_ref = nodes.reference("", "", refuri=app_path)
            app_ref += nodes.Text(story.app_slug.replace("-", " ").title())
            story_para += app_ref
        else:
            story_para += nodes.Text(story.app_slug.replace("-", " ").title())

        story_para += nodes.Text(")")

        story_item += story_para
        story_list += story_item

    result_nodes.append(story_list)

    return result_nodes


def _build_relative_uri(from_docname: str, target_doc: str, anchor: str = None) -> str:
    """Build a relative URI from one doc to another."""
    from_parts = from_docname.split("/")
    target_parts = target_doc.split("/")

    common = 0
    for i in range(min(len(from_parts), len(target_parts))):
        if from_parts[i] == target_parts[i]:
            common += 1
        else:
            break

    up_levels = len(from_parts) - common - 1
    down_path = "/".join(target_parts[common:])

    if up_levels > 0:
        rel_path = "../" * up_levels + down_path + ".html"
    else:
        rel_path = down_path + ".html"

    if anchor:
        return f"{rel_path}#{anchor}"
    return rel_path


def build_epic_index(env, docname: str, hcd_context):
    """Build the epic index listing all epics, plus unassigned stories."""
    from ...config import get_config

    config = get_config()
    prefix = path_to_root(docname)

    all_epics = hcd_context.epic_repo.list()
    all_stories = hcd_context.story_repo.list()
    all_apps = hcd_context.app_repo.list()
    known_apps = {normalize_name(a.name) for a in all_apps}

    if not all_epics:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No epics defined")
        return [para]

    result_nodes = []
    bullet_list = nodes.bullet_list()

    # Collect all stories assigned to epics
    assigned_stories = set()
    for epic in all_epics:
        for story_title in epic.story_refs:
            assigned_stories.add(normalize_name(story_title))

    for epic in sorted(all_epics, key=lambda e: e.slug):
        item = nodes.list_item()
        para = nodes.paragraph()

        # Link to epic
        epic_path = f"{epic.slug}.html"
        epic_ref = nodes.reference("", "", refuri=epic_path)
        epic_ref += nodes.Text(epic.slug.replace("-", " ").title())
        para += epic_ref

        # Story count
        story_count = len(epic.story_refs)
        para += nodes.Text(f" ({story_count} stories)")

        item += para
        bullet_list += item

    result_nodes.append(bullet_list)

    # Find unassigned stories
    unassigned_stories = []
    for story in all_stories:
        if normalize_name(story.feature_title) not in assigned_stories:
            unassigned_stories.append(story)

    if unassigned_stories:
        heading = nodes.paragraph()
        heading += nodes.strong(text="Unassigned Stories")
        result_nodes.append(heading)

        intro = nodes.paragraph()
        intro += nodes.Text(
            f"{len(unassigned_stories)} stories not yet assigned to an epic:"
        )
        result_nodes.append(intro)

        unassigned_list = nodes.bullet_list()
        for story in sorted(unassigned_stories, key=lambda s: s.feature_title.lower()):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Story link
            story_doc = f"{config.get_doc_path('stories')}/{story.app_slug}"
            story_ref_uri = _build_relative_uri(docname, story_doc, story.slug)
            story_ref = nodes.reference("", "", refuri=story_ref_uri)
            story_ref += nodes.Text(story.i_want)
            para += story_ref

            # App in parentheses
            para += nodes.Text(" (")
            app_path = (
                f"{prefix}{config.get_doc_path('applications')}/{story.app_slug}.html"
            )
            app_valid = story.app_normalized in known_apps

            if app_valid:
                app_ref = nodes.reference("", "", refuri=app_path)
                app_ref += nodes.Text(story.app_slug.replace("-", " ").title())
                para += app_ref
            else:
                para += nodes.Text(story.app_slug.replace("-", " ").title())

            para += nodes.Text(")")

            item += para
            unassigned_list += item

        result_nodes.append(unassigned_list)

    return result_nodes


def build_epics_for_persona(env, docname: str, persona_arg: str, hcd_context):
    """Build list of epics for a persona."""
    from ...config import get_config

    config = get_config()
    prefix = path_to_root(docname)

    all_stories = hcd_context.story_repo.list()
    all_epics = hcd_context.epic_repo.list()

    # Derive personas to get their epic associations
    personas = derive_personas(all_stories, all_epics)
    persona_normalized = normalize_name(persona_arg)

    # Find the persona
    persona = None
    for p in personas:
        if p.normalized_name == persona_normalized:
            persona = p
            break

    if not persona:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No epics found for persona '{persona_arg}'")
        return [para]

    # Get epics for this persona
    matching_epics = get_epics_for_persona(persona, all_epics)

    if not matching_epics:
        para = nodes.paragraph()
        para += nodes.emphasis(text=f"No epics found for persona '{persona_arg}'")
        return [para]

    bullet_list = nodes.bullet_list()

    for epic in sorted(matching_epics, key=lambda e: e.slug):
        item = nodes.list_item()
        para = nodes.paragraph()

        epic_path = f"{prefix}{config.get_doc_path('epics')}/{epic.slug}.html"
        epic_ref = nodes.reference("", "", refuri=epic_path)
        epic_ref += nodes.Text(epic.slug.replace("-", " ").title())
        para += epic_ref

        item += para
        bullet_list += item

    return [bullet_list]


def clear_epic_state(app, env, docname):
    """Clear epic state when a document is re-read."""
    from ..context import get_hcd_context

    # Clear current epic tracker
    if hasattr(env, "epic_current") and docname in env.epic_current:
        del env.epic_current[docname]

    # Clear epics from this document via repository
    hcd_context = get_hcd_context(app)
    hcd_context.epic_repo.clear_by_docname(docname)


def process_epic_placeholders(app, doctree, docname):
    """Replace epic placeholders with rendered content."""
    from ..context import get_hcd_context

    env = app.env
    hcd_context = get_hcd_context(app)
    epic_current = getattr(env, "epic_current", {})

    # Process epic stories placeholder
    epic_slug = epic_current.get(docname)
    if epic_slug:
        epic = hcd_context.epic_repo.get(epic_slug)
        if epic:
            for node in doctree.traverse(nodes.container):
                if "epic-stories-placeholder" in node.get("classes", []):
                    stories_nodes = render_epic_stories(epic, docname, hcd_context)
                    if stories_nodes:
                        node.replace_self(stories_nodes)
                    else:
                        node.replace_self([])
                    break

    # Process epic index placeholder
    for node in doctree.traverse(EpicIndexPlaceholder):
        index_node = build_epic_index(env, docname, hcd_context)
        node.replace_self(index_node)

    # Process epics-for-persona placeholder
    for node in doctree.traverse(EpicsForPersonaPlaceholder):
        persona = node["persona"]
        epics_node = build_epics_for_persona(env, docname, persona, hcd_context)
        node.replace_self(epics_node)

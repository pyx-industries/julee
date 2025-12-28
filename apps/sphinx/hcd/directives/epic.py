"""Epic directives for sphinx_hcd.

Provides directives for defining and cross-referencing epics:
- define-epic: Define an epic with description
- epic-story: Reference a story as part of the epic
- epic-index: Render index of all epics
- epics-for-persona: List epics for a persona (derived from stories)
"""

from docutils import nodes

from apps.sphinx.shared import path_to_root
from julee.hcd.entities.epic import Epic
from julee.hcd.use_cases.crud import (
    CreateEpicRequest,
    GetEpicRequest,
    ListAppsRequest,
    ListEpicsRequest,
    ListStoriesRequest,
)
from julee.hcd.use_cases.derive_personas import derive_personas, get_epics_for_persona
from julee.hcd.utils import normalize_name

from ..dependencies import get_create_epic_use_case
from ..node_builders import (
    empty_result_paragraph,
    entity_bullet_list,
    make_link,
)
from .base import HCDDirective


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
        solution = self.solution_slug

        # Create epic via use case
        request = CreateEpicRequest(
            slug=epic_slug,
            description=description,
            story_refs=[],  # Will be populated by epic-story
            docname=docname,
            solution_slug=solution,
        )
        use_case = get_create_epic_use_case(self.hcd_context)
        response = use_case.execute_sync(request)
        epic = response.epic

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
            epic_response = self.hcd_context.get_epic.execute_sync(
                GetEpicRequest(slug=epic_slug)
            )
            epic = epic_response.epic
            if epic:
                # Add story to epic's story_refs
                if story_title not in epic.story_refs:
                    epic.story_refs.append(story_title)

        # Return empty - rendering happens in doctree-resolved
        return []


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
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)

    # Get all stories and apps via use cases
    stories_response = hcd_context.list_stories.execute_sync(
        ListStoriesRequest(solution_slug=solution)
    )
    apps_response = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    )
    all_stories = stories_response.stories
    known_apps = {normalize_name(a.name) for a in apps_response.apps}

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

        # Story link
        story_doc = f"{config.get_doc_path('stories')}/{story.app_slug}"
        story_ref_uri = _build_relative_uri(docname, story_doc, story.slug)
        story_para += make_link(story_ref_uri, story.i_want)

        # App in parentheses
        story_para += nodes.Text(" (")
        app_path = (
            f"{prefix}{config.get_doc_path('applications')}/{story.app_slug}.html"
        )
        app_valid = story.app_normalized in known_apps

        if app_valid:
            story_para += make_link(app_path, story.app_slug.replace("-", " ").title())
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
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)

    # Get all entities via use cases
    epics_response = hcd_context.list_epics.execute_sync(
        ListEpicsRequest(solution_slug=solution)
    )
    stories_response = hcd_context.list_stories.execute_sync(
        ListStoriesRequest(solution_slug=solution)
    )
    apps_response = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    )
    all_epics = epics_response.epics
    all_stories = stories_response.stories
    known_apps = {normalize_name(a.name) for a in apps_response.apps}

    if not all_epics:
        return [empty_result_paragraph("No epics defined")]

    result_nodes = []

    # Collect all stories assigned to epics
    assigned_stories = set()
    for epic in all_epics:
        for story_title in epic.story_refs:
            assigned_stories.add(normalize_name(story_title))

    # Epic list
    result_nodes.append(
        entity_bullet_list(
            sorted(all_epics, key=lambda e: e.slug),
            link_fn=lambda e: (f"{e.slug}.html", e.slug.replace("-", " ").title()),
            suffix_fn=lambda e: f" ({len(e.story_refs)} stories)",
        )
    )

    # Find unassigned stories
    unassigned_stories = []
    for story in all_stories:
        if normalize_name(story.feature_title) not in assigned_stories:
            unassigned_stories.append(story)

    if unassigned_stories:
        # Section heading
        heading = nodes.paragraph()
        heading += nodes.strong(text="Unassigned Stories")
        result_nodes.append(heading)

        intro = nodes.paragraph()
        intro += nodes.Text(
            f"{len(unassigned_stories)} stories not yet assigned to an epic:"
        )
        result_nodes.append(intro)

        # Build unassigned stories list with app links
        unassigned_list = nodes.bullet_list()
        for story in sorted(unassigned_stories, key=lambda s: s.feature_title.lower()):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Story link
            story_doc = f"{config.get_doc_path('stories')}/{story.app_slug}"
            story_ref_uri = _build_relative_uri(docname, story_doc, story.slug)
            para += make_link(story_ref_uri, story.i_want)

            # App in parentheses
            para += nodes.Text(" (")
            app_path = (
                f"{prefix}{config.get_doc_path('applications')}/{story.app_slug}.html"
            )
            app_valid = story.app_normalized in known_apps

            if app_valid:
                para += make_link(app_path, story.app_slug.replace("-", " ").title())
            else:
                para += nodes.Text(story.app_slug.replace("-", " ").title())

            para += nodes.Text(")")

            item += para
            unassigned_list += item

        result_nodes.append(unassigned_list)

    return result_nodes


def build_epics_for_persona(env, docname: str, persona_arg: str, hcd_context):
    """Build list of epics for a persona."""
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)

    # Get entities via use cases
    stories_response = hcd_context.list_stories.execute_sync(
        ListStoriesRequest(solution_slug=solution)
    )
    epics_response = hcd_context.list_epics.execute_sync(
        ListEpicsRequest(solution_slug=solution)
    )
    all_stories = stories_response.stories
    all_epics = epics_response.epics

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
        return [empty_result_paragraph(f"No epics found for persona '{persona_arg}'")]

    # Get epics for this persona
    matching_epics = get_epics_for_persona(persona, all_epics, all_stories)

    if not matching_epics:
        return [empty_result_paragraph(f"No epics found for persona '{persona_arg}'")]

    return [
        entity_bullet_list(
            sorted(matching_epics, key=lambda e: e.slug),
            link_fn=lambda e: (
                f"{prefix}{config.get_doc_path('epics')}/{e.slug}.html",
                e.slug.replace("-", " ").title(),
            ),
        )
    ]


def clear_epic_state(app, env, docname):
    """Clear epic state when a document is re-read."""
    from ..context import get_hcd_context

    # Clear current epic tracker
    if hasattr(env, "epic_current") and docname in env.epic_current:
        del env.epic_current[docname]

    # Clear epics from this document via repository
    hcd_context = get_hcd_context(app)
    hcd_context.epic_repo.run_async(
        hcd_context.epic_repo.async_repo.clear_by_docname(docname)
    )


# NOTE: process_epic_placeholders removed - now handled by
# infrastructure/handlers/placeholder_resolution.py via EpicPlaceholderHandler

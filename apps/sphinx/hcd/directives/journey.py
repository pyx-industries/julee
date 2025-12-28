"""Journey directives for sphinx_hcd.

A journey represents a persona's path through the system to achieve a goal.
Each journey captures the user's motivation, the value they receive, and
the sequence of steps (stories/epics) they follow.

Provides directives:
- define-journey: Define a journey with persona, intent, outcome, and steps
- step-story: Reference a story as a journey step
- step-epic: Reference an epic as a journey step
- step-phase: Optional grouping label for steps
- journey-index: Render index of all journeys
- journey-dependency-graph: Generate PlantUML graph of journey dependencies
- journeys-for-persona: List journeys for a specific persona

Template-driven pattern:
- journey-index and journeys-for-persona use Jinja templates
- Templates are in julee/hcd/infrastructure/templates/
"""

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from jinja2 import Environment, FileSystemLoader

from apps.sphinx.directive_factory import parse_rst_to_nodes
from apps.sphinx.shared import path_to_root
from julee.hcd.entities.journey import Journey, JourneyStep
from julee.hcd.use_cases.crud import (
    CreateJourneyRequest,
    GetJourneyRequest,
    ListAppsRequest,
    ListJourneysRequest,
    ListStoriesRequest,
)
from julee.hcd.utils import (
    normalize_name,
    parse_csv_option,
    parse_list_option,
)

from ..node_builders import (
    empty_result_paragraph,
    entity_bullet_list,
    make_link,
)
from .base import HCDDirective

# Template directory for HCD entity templates
_HCD_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent.parent / "src/julee/hcd/infrastructure/templates"

# Jinja environment for journey templates
_jinja_env: Environment | None = None


def _get_jinja_env() -> Environment:
    """Get or create Jinja environment for HCD templates."""
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(_HCD_TEMPLATE_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Add custom filters
        _jinja_env.filters["first_sentence"] = _first_sentence
    return _jinja_env


def _first_sentence(text: str) -> str:
    """Extract first sentence from text."""
    if not text:
        return ""
    for i, char in enumerate(text):
        if char in ".!?" and (i + 1 >= len(text) or text[i + 1] in " \n"):
            return text[: i + 1]
    return text


class JourneyDependencyGraphPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for journey dependency graph, replaced at doctree-resolved."""

    pass


class DefineJourneyDirective(HCDDirective):
    """Define a journey with persona, intent, outcome, and metadata.

    Options:
        :persona: (required) The persona undertaking this journey.
        :intent: The user's underlying motivation.
        :outcome: The business value delivered when the journey succeeds.
        :depends-on: Comma-separated list of journey slugs.
        :preconditions: Bullet list of conditions that must be true before starting.
        :postconditions: Bullet list of conditions that will be true after completing.

    Example::

        .. define-journey:: build-vocabulary
           :persona: Knowledge Curator
           :intent: Ensure consistent terminology across RBA programs
           :outcome: Semantic interoperability enabling automated compliance mapping
           :depends-on: operate-pipelines
    """

    required_arguments = 1  # journey slug
    has_content = True
    option_spec = {
        "persona": directives.unchanged_required,
        "intent": directives.unchanged,
        "outcome": directives.unchanged,
        "depends-on": directives.unchanged,
        "preconditions": directives.unchanged,
        "postconditions": directives.unchanged,
    }

    def run(self):
        journey_slug = self.arguments[0]
        docname = self.env.docname

        # Parse options
        persona = self.options.get("persona", "").strip()
        intent = self.options.get("intent", "").strip()
        outcome = self.options.get("outcome", "").strip()
        depends_on = parse_csv_option(self.options.get("depends-on", ""))
        preconditions = parse_list_option(self.options.get("preconditions", ""))
        postconditions = parse_list_option(self.options.get("postconditions", ""))
        goal = "\n".join(self.content).strip()

        # Create and register journey via use case
        request = CreateJourneyRequest(
            slug=journey_slug,
            persona=persona,
            intent=intent,
            outcome=outcome,
            goal=goal,
            depends_on=depends_on,
            preconditions=preconditions,
            postconditions=postconditions,
            steps=[],  # Will be populated by step directives
            docname=docname,
            solution_slug=self.solution_slug,
        )
        self.hcd_context.create_journey.execute_sync(request)

        # Track current journey in environment for step directives
        if not hasattr(self.env, "journey_current"):
            self.env.journey_current = {}
        self.env.journey_current[docname] = journey_slug

        # Build output nodes
        result_nodes = []

        # Intent and outcome paragraph
        if persona and intent:
            intro_para = nodes.paragraph()
            intro_para += nodes.Text("The ")
            intro_para += self.make_persona_link(persona)
            intro_para += nodes.Text(" wants to ")
            intent_text = intent[0].lower() + intent[1:] if intent else ""
            intro_para += nodes.Text(intent_text + ".")

            if outcome:
                intro_para += nodes.Text(" Success means ")
                outcome_text = outcome[0].lower() + outcome[1:] if outcome else ""
                intro_para += nodes.Text(outcome_text + ".")

            result_nodes.append(intro_para)

        # Goal paragraph (backward compat for when intent not provided)
        if goal and not intent:
            intro_para = nodes.paragraph()
            intro_para += nodes.Text("The goal of the ")
            intro_para += self.make_persona_link(persona)
            intro_para += nodes.Text(" is to ")
            goal_text = goal[0].lower() + goal[1:] if goal else ""
            intro_para += nodes.Text(goal_text)
            result_nodes.append(intro_para)
        elif goal and intent:
            goal_para = nodes.paragraph()
            goal_para += nodes.Text(goal)
            result_nodes.append(goal_para)

        # Placeholder for steps (filled in doctree-read)
        steps_placeholder = nodes.container()
        steps_placeholder["classes"].append("journey-steps-placeholder")
        steps_placeholder["journey_slug"] = journey_slug
        result_nodes.append(steps_placeholder)

        return result_nodes


class StepStoryDirective(HCDDirective):
    """Reference a story as a journey step.

    Usage::

        .. step-story:: Upload Scheme Documentation
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        story_title = self.arguments[0]
        docname = self.env.docname

        # Get current journey and add step
        journey_current = getattr(self.env, "journey_current", {})
        journey_slug = journey_current.get(docname)

        if journey_slug:
            journey_response = self.hcd_context.get_journey.execute_sync(
                GetJourneyRequest(slug=journey_slug)
            )
            journey = journey_response.journey
            if journey:
                step = JourneyStep.story(story_title)
                journey.steps.append(step)

        return []


class StepEpicDirective(HCDDirective):
    """Reference an epic as a journey step.

    Usage::

        .. step-epic:: vocabulary-management
    """

    required_arguments = 1

    def run(self):
        epic_slug = self.arguments[0]
        docname = self.env.docname

        journey_current = getattr(self.env, "journey_current", {})
        journey_slug = journey_current.get(docname)

        if journey_slug:
            journey_response = self.hcd_context.get_journey.execute_sync(
                GetJourneyRequest(slug=journey_slug)
            )
            journey = journey_response.journey
            if journey:
                step = JourneyStep.epic(epic_slug)
                journey.steps.append(step)

        return []


class StepPhaseDirective(HCDDirective):
    """Optional grouping label for journey steps.

    Usage::

        .. step-phase:: Upload Sources

           Add reference materials to the knowledge base.
    """

    required_arguments = 1
    final_argument_whitespace = True
    has_content = True

    def run(self):
        phase_title = self.arguments[0]
        docname = self.env.docname
        description = "\n".join(self.content).strip()

        journey_current = getattr(self.env, "journey_current", {})
        journey_slug = journey_current.get(docname)

        if journey_slug:
            journey_response = self.hcd_context.get_journey.execute_sync(
                GetJourneyRequest(slug=journey_slug)
            )
            journey = journey_response.journey
            if journey:
                step = JourneyStep.phase(phase_title, description)
                journey.steps.append(step)

        return []


class JourneyIndexDirective(HCDDirective):
    """Render index of all journeys.

    Usage::

        .. journey-index::
    """

    def run(self):
        solution = self.solution_slug
        docname = self.env.docname
        journeys_response = self.hcd_context.list_journeys.execute_sync(
            ListJourneysRequest(solution_slug=solution)
        )
        all_journeys = journeys_response.journeys

        return build_journey_index(
            journeys=all_journeys,
            docname=docname,
            empty_message="No journeys defined",
        )


def build_journey_index(
    journeys: list[Journey],
    docname: str,
    empty_message: str = "No journeys found",
    show_persona: bool = True,
    show_description: bool = True,
    max_desc_length: int = 100,
) -> list[nodes.Node]:
    """Build journey index using template.

    Args:
        journeys: List of Journey entities to render
        docname: Current document name (for RST parsing)
        empty_message: Message when no journeys
        show_persona: Whether to show persona in parentheses
        show_description: Whether to show intent/goal
        max_desc_length: Max description length

    Returns:
        List of docutils nodes
    """
    env = _get_jinja_env()
    template = env.get_template("journey_index.rst.j2")
    rst_content = template.render(
        journeys=sorted(journeys, key=lambda j: j.slug),
        empty_message=empty_message,
        show_persona=show_persona,
        show_description=show_description,
        max_desc_length=max_desc_length,
    )
    return parse_rst_to_nodes(rst_content, docname)


class JourneyDependencyGraphDirective(HCDDirective):
    """Generate a PlantUML dependency graph from journey dependencies.

    Usage::

        .. journey-dependency-graph::
    """

    def run(self):
        # Return placeholder - rendered in doctree-resolved
        node = JourneyDependencyGraphPlaceholder()
        return [node]


class JourneysForPersonaDirective(HCDDirective):
    """List journeys for a specific persona.

    Usage::

        .. journeys-for-persona:: Analyst
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        persona_arg = self.arguments[0]
        solution = self.solution_slug
        docname = self.env.docname

        # Get journeys using filtered use case
        response = self.hcd_context.list_journeys.execute_sync(
            ListJourneysRequest(persona=persona_arg, solution_slug=solution)
        )
        journeys = response.journeys

        return build_journey_index(
            journeys=journeys,
            docname=docname,
            empty_message=f"No journeys found for persona '{persona_arg}'",
            show_persona=False,
            show_description=False,
        )


def build_story_node(story_title: str, docname: str, hcd_context):
    """Build a paragraph node for a story reference."""
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    stories_response = hcd_context.list_stories.execute_sync(
        ListStoriesRequest(solution_slug=solution)
    )
    apps_response = hcd_context.list_apps.execute_sync(
        ListAppsRequest(solution_slug=solution)
    )
    all_stories = stories_response.stories
    known_apps = {normalize_name(a.name) for a in apps_response.apps}
    prefix = path_to_root(docname)

    # Find the story
    story_normalized = normalize_name(story_title)
    story = None
    for s in all_stories:
        if normalize_name(s.feature_title) == story_normalized:
            story = s
            break

    para = nodes.paragraph()

    if story:
        # Story link
        story_doc = f"{config.get_doc_path('stories')}/{story.app_slug}"
        story_ref_uri = _build_relative_uri(docname, story_doc, story.slug)
        para += make_link(story_ref_uri, story.feature_title)

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
    else:
        para += nodes.problematic(text=f"{story_title} [not found]")

    return para


def build_epic_node(epic_slug: str, docname: str):
    """Build a paragraph node for an epic reference."""
    from ..config import get_config

    config = get_config()
    prefix = path_to_root(docname)
    epic_path = f"{prefix}{config.get_doc_path('epics')}/{epic_slug}.html"

    para = nodes.paragraph()
    para += make_link(epic_path, epic_slug.replace("-", " ").title())
    para += nodes.Text(" (epic)")

    return para


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


def render_journey_steps(journey: Journey, docname: str, hcd_context):
    """Render journey steps as a numbered list with phases grouping stories."""
    steps = journey.steps
    if not steps:
        return None

    # Group steps by phase
    phases = []
    current_phase = None

    for step in steps:
        if step.step_type.value == "phase":
            current_phase = {
                "title": step.ref,
                "description": step.description,
                "items": [],
            }
            phases.append(current_phase)
        elif step.step_type.value in ("story", "epic"):
            if current_phase is None:
                current_phase = {"title": None, "description": "", "items": []}
                phases.append(current_phase)
            current_phase["items"].append(step)

    # Build enumerated list
    enum_list = nodes.enumerated_list()
    enum_list["enumtype"] = "arabic"

    for phase in phases:
        list_item = nodes.list_item()

        if phase["title"]:
            header_para = nodes.paragraph()
            header_para += nodes.strong(text=phase["title"])
            if phase["description"]:
                header_para += nodes.Text(" — ")
                header_para += nodes.Text(phase["description"])
            list_item += header_para

        if phase["items"]:
            bullet_list = nodes.bullet_list()
            for item in phase["items"]:
                bullet_item = nodes.list_item()
                if item.step_type.value == "story":
                    bullet_item += build_story_node(item.ref, docname, hcd_context)
                elif item.step_type.value == "epic":
                    bullet_item += build_epic_node(item.ref, docname)
                bullet_list += bullet_item
            list_item += bullet_list

        enum_list += list_item

    return enum_list


def make_labelled_list(
    term: str, items: list, hcd_context, docname: str = None, item_type: str = "text"
):
    """Create a labelled bullet list with term as heading."""
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug

    container = nodes.container()

    term_para = nodes.paragraph()
    term_para += nodes.strong(text=term)
    container += term_para

    bullet_list = nodes.bullet_list()
    journeys_response = hcd_context.list_journeys.execute_sync(
        ListJourneysRequest(solution_slug=solution)
    )
    journey_slugs = {j.slug for j in journeys_response.journeys}

    for item in items:
        list_item = nodes.list_item()
        inline = nodes.inline()

        if item_type == "journey":
            related_slug = item
            related_path = f"{related_slug}.html"
            if related_slug in journey_slugs:
                inline += make_link(related_path, related_slug.replace("-", " ").title())
            else:
                inline += nodes.Text(related_slug.replace("-", " ").title())
                inline += nodes.emphasis(text=" [not found]")
        else:
            inline += nodes.Text(item)

        list_item += inline
        bullet_list += list_item

    container += bullet_list
    return container


def clear_journey_state(app, env, docname):
    """Clear journey state when a document is re-read."""
    from ..context import get_hcd_context

    # Clear current journey tracker
    if hasattr(env, "journey_current") and docname in env.journey_current:
        del env.journey_current[docname]

    # Clear journeys from this document via repository
    hcd_context = get_hcd_context(app)
    hcd_context.journey_repo.run_async(
        hcd_context.journey_repo.async_repo.clear_by_docname(docname)
    )


def process_journey_steps(app, doctree):
    """Replace journey steps placeholder with rendered steps."""
    from ..config import get_config
    from ..context import get_hcd_context

    env = app.env
    docname = env.docname
    hcd_context = get_hcd_context(app)
    config = get_config()
    solution = config.solution_slug
    journey_current = getattr(env, "journey_current", {})

    journey_slug = journey_current.get(docname)
    if not journey_slug:
        return

    journey_response = hcd_context.get_journey.execute_sync(
        GetJourneyRequest(slug=journey_slug)
    )
    journey = journey_response.journey
    if not journey:
        return

    # Replace steps placeholder
    for node in doctree.traverse(nodes.container):
        if "journey-steps-placeholder" in node.get("classes", []):
            steps_node = render_journey_steps(journey, docname, hcd_context)
            # Clear classes before replacing to avoid docutils warning
            node["classes"] = []
            if steps_node:
                node.replace_self([steps_node])
            else:
                node.replace_self([])
            break

    # Add preconditions
    if journey.preconditions:
        doctree += make_labelled_list(
            "Preconditions", journey.preconditions, hcd_context
        )

    # Add postconditions
    if journey.postconditions:
        doctree += make_labelled_list(
            "Postconditions", journey.postconditions, hcd_context
        )

    # Add depends-on
    if journey.depends_on:
        doctree += make_labelled_list(
            "Depends On", journey.depends_on, hcd_context, docname, item_type="journey"
        )

    # Add depended-on-by (inferred)
    journeys_response = hcd_context.list_journeys.execute_sync(
        ListJourneysRequest(solution_slug=solution)
    )
    depended_on_by = [j.slug for j in journeys_response.journeys if journey_slug in j.depends_on]
    if depended_on_by:
        doctree += make_labelled_list(
            "Depended On By",
            sorted(depended_on_by),
            hcd_context,
            docname,
            item_type="journey",
        )


def build_dependency_graph_node(env, hcd_context):
    """Build the PlantUML node for the journey dependency graph."""
    from ..config import get_config

    try:
        from sphinxcontrib.plantuml import plantuml
    except ImportError:
        return empty_result_paragraph("PlantUML extension not available")

    config = get_config()
    solution = config.solution_slug
    journeys_response = hcd_context.list_journeys.execute_sync(
        ListJourneysRequest(solution_slug=solution)
    )
    all_journeys = journeys_response.journeys

    if not all_journeys:
        return empty_result_paragraph("No journeys defined")

    # Build PlantUML content
    lines = [
        "@startuml",
        "skinparam componentStyle rectangle",
        "skinparam defaultTextAlignment center",
        "",
    ]

    journey_slugs = {j.slug for j in all_journeys}

    for journey in sorted(all_journeys, key=lambda j: j.slug):
        title = journey.slug.replace("-", " ").title()
        lines.append(f"[{title}] as {journey.slug.replace('-', '_')}")

    lines.append("")

    for journey in sorted(all_journeys, key=lambda j: j.slug):
        for dep in journey.depends_on:
            if dep in journey_slugs:
                from_id = journey.slug.replace("-", "_")
                to_id = dep.replace("-", "_")
                lines.append(f"{from_id} --> {to_id}")

    lines.append("")
    lines.append("@enduml")

    puml_content = "\n".join(lines)

    puml_node = plantuml(puml_content)
    puml_node["uml"] = puml_content
    puml_node["incdir"] = ""
    puml_node["filename"] = "journey-dependency-graph"

    return puml_node


# NOTE: process_dependency_graph_placeholder removed - now handled by
# infrastructure/handlers/placeholder_resolution.py via JourneyPlaceholderHandler

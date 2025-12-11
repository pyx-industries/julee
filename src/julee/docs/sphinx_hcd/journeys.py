"""Sphinx extension for defining and cross-referencing user journeys.

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
"""

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from .config import get_config
from .utils import (
    normalize_name,
    parse_csv_option,
    parse_list_option,
    path_to_root,
    slugify,
)

logger = logging.getLogger(__name__)


def get_journey_registry(env):
    """Get or create the journey registry on the environment."""
    if not hasattr(env, "journey_registry"):
        env.journey_registry = {}
    return env.journey_registry


def get_current_journey(env):
    """Get or create the current journey tracker on the environment."""
    if not hasattr(env, "journey_current"):
        env.journey_current = {}
    return env.journey_current


class DefineJourneyDirective(SphinxDirective):
    """Define a journey with persona, intent, outcome, and metadata.

    Options:
        :persona: (required) The persona undertaking this journey.

        :intent: The user's underlying motivation - why they care about this
            journey. Answers "what does the persona want?" Focus on their
            goal, not the system's features. Renders as:
            "The [Persona] wants to [intent]."

        :outcome: The business value delivered when the journey succeeds.
            Answers "what does success look like?" Focus on measurable or
            observable results, not activities. Renders as:
            "Success means [outcome]."

        :depends-on: Comma-separated list of journey slugs that must be
            completed before this journey makes sense.

        :preconditions: Bullet list of conditions that must be true before
            starting this journey.

        :postconditions: Bullet list of conditions that will be true after
            completing this journey.

    Content:
        The directive body describes *what* the persona does (activities).
        If :intent: is provided, this becomes supplementary description.
        If :intent: is omitted, this becomes the goal (backward compatibility).

    Example::

        .. define-journey:: build-vocabulary
           :persona: Knowledge Curator
           :intent: Ensure consistent terminology across RBA programs
           :outcome: Semantic interoperability enabling automated compliance mapping
           :depends-on: operate-pipelines
           :preconditions:
              - Source materials available
              - SME accessible
           :postconditions:
              - SVC published and versioned

           Create a Sustainable Vocabulary Catalog from source materials.
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
        from . import stories

        config = get_config()
        journey_slug = self.arguments[0]
        docname = self.env.docname

        # Parse options
        persona = self.options.get("persona", "").strip()
        intent = self.options.get("intent", "").strip()
        outcome = self.options.get("outcome", "").strip()
        depends_on = parse_csv_option(self.options.get("depends-on", ""))
        preconditions = parse_list_option(self.options.get("preconditions", ""))
        postconditions = parse_list_option(self.options.get("postconditions", ""))

        # Goal is the directive content (what they do)
        goal = "\n".join(self.content).strip()

        # Register the journey in environment
        journey_registry = get_journey_registry(self.env)
        current_journey = get_current_journey(self.env)

        journey_data = {
            "slug": journey_slug,
            "persona": persona,
            "persona_normalized": normalize_name(persona),
            "intent": intent,
            "outcome": outcome,
            "goal": goal,
            "depends_on": depends_on,
            "preconditions": preconditions,
            "postconditions": postconditions,
            "steps": [],  # Will be populated by step-story/step-epic/step-phase
            "docname": docname,
        }
        journey_registry[journey_slug] = journey_data
        current_journey[docname] = journey_slug

        # Build output nodes
        result_nodes = []

        # Import story extension to get known personas
        _known_personas = stories.get_known_personas()

        # Calculate paths
        prefix = path_to_root(docname)

        # Intent and outcome as single paragraph:
        # "The [Persona] wants to [intent]. Success means [outcome]."
        if persona and intent:
            intro_para = nodes.paragraph()
            intro_para += nodes.Text("The ")

            persona_slug = slugify(persona)
            persona_path = (
                f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"
            )
            persona_valid = normalize_name(persona) in _known_personas

            if persona_valid:
                persona_ref = nodes.reference("", "", refuri=persona_path)
                persona_ref += nodes.Text(persona)
                intro_para += persona_ref
            else:
                intro_para += nodes.Text(persona)

            intro_para += nodes.Text(" wants to ")
            # Lowercase first letter of intent to flow as sentence
            intent_text = intent[0].lower() + intent[1:] if intent else ""
            intro_para += nodes.Text(intent_text + ".")

            # Append outcome to same paragraph if present
            if outcome:
                intro_para += nodes.Text(" Success means ")
                outcome_text = outcome[0].lower() + outcome[1:] if outcome else ""
                intro_para += nodes.Text(outcome_text + ".")

            result_nodes.append(intro_para)

        # Goal paragraph (what they do) - only if intent not provided (backward compat)
        if goal and not intent:
            # Fall back to old format if no intent specified
            intro_para = nodes.paragraph()
            intro_para += nodes.Text("The goal of the ")

            persona_slug = slugify(persona)
            persona_path = (
                f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"
            )
            persona_valid = normalize_name(persona) in _known_personas

            if persona_valid:
                persona_ref = nodes.reference("", "", refuri=persona_path)
                persona_ref += nodes.Text(persona)
                intro_para += persona_ref
            else:
                intro_para += nodes.Text(persona)

            intro_para += nodes.Text(" is to ")
            goal_text = goal[0].lower() + goal[1:] if goal else ""
            intro_para += nodes.Text(goal_text)
            result_nodes.append(intro_para)
        elif goal and intent:
            # If intent provided, goal becomes activity description
            goal_para = nodes.paragraph()
            goal_para += nodes.Text(goal)
            result_nodes.append(goal_para)

        # Add a placeholder for steps (will be filled in doctree-resolved)
        steps_placeholder = nodes.container()
        steps_placeholder["classes"].append("journey-steps-placeholder")
        steps_placeholder["journey_slug"] = journey_slug
        result_nodes.append(steps_placeholder)

        return result_nodes


class StepStoryDirective(SphinxDirective):
    """Reference a story as a journey step.

    Usage::

        .. step-story:: Upload Scheme Documentation
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        story_title = self.arguments[0]
        docname = self.env.docname

        # Add to current journey's steps
        journey_registry = get_journey_registry(self.env)
        current_journey = get_current_journey(self.env)

        journey_slug = current_journey.get(docname)
        if journey_slug and journey_slug in journey_registry:
            journey_registry[journey_slug]["steps"].append(
                {
                    "type": "story",
                    "ref": story_title,
                }
            )

        # Return empty - rendering happens in doctree-resolved
        return []


class StepEpicDirective(SphinxDirective):
    """Reference an epic as a journey step.

    Usage::

        .. step-epic:: vocabulary-management
    """

    required_arguments = 1

    def run(self):
        epic_slug = self.arguments[0]
        docname = self.env.docname

        # Add to current journey's steps
        journey_registry = get_journey_registry(self.env)
        current_journey = get_current_journey(self.env)

        journey_slug = current_journey.get(docname)
        if journey_slug and journey_slug in journey_registry:
            journey_registry[journey_slug]["steps"].append(
                {
                    "type": "epic",
                    "ref": epic_slug,
                }
            )

        # Return empty - rendering happens in doctree-resolved
        return []


class StepPhaseDirective(SphinxDirective):
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

        # Add to current journey's steps
        journey_registry = get_journey_registry(self.env)
        current_journey = get_current_journey(self.env)

        journey_slug = current_journey.get(docname)
        if journey_slug and journey_slug in journey_registry:
            journey_registry[journey_slug]["steps"].append(
                {
                    "type": "phase",
                    "ref": phase_title,
                    "description": description,
                }
            )

        # Return empty - rendering happens in doctree-resolved
        return []


class JourneyIndexDirective(SphinxDirective):
    """Render index of all journeys.

    Usage::

        .. journey-index::
    """

    def run(self):
        journey_registry = get_journey_registry(self.env)

        if not journey_registry:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No journeys defined")
            return [para]

        result_nodes = []
        bullet_list = nodes.bullet_list()

        for slug in sorted(journey_registry.keys()):
            journey = journey_registry[slug]

            item = nodes.list_item()
            para = nodes.paragraph()

            # Link to journey
            journey_path = f"{slug}.html"
            journey_ref = nodes.reference("", "", refuri=journey_path)
            journey_ref += nodes.strong(text=slug.replace("-", " ").title())
            para += journey_ref

            # Persona in parentheses
            if journey["persona"]:
                para += nodes.Text(f" ({journey['persona']})")

            item += para

            # Intent as sub-paragraph (preferred), fall back to goal
            display_text = journey.get("intent") or journey.get("goal", "")
            if display_text:
                desc_para = nodes.paragraph()
                # Truncate if too long
                if len(display_text) > 100:
                    display_text = display_text[:100] + "..."
                desc_para += nodes.Text(display_text)
                item += desc_para

            bullet_list += item

        result_nodes.append(bullet_list)
        return result_nodes


class JourneyDependencyGraphPlaceholder(nodes.General, nodes.Element):
    """Placeholder node for journey dependency graph, replaced at doctree-resolved."""

    pass


class JourneyDependencyGraphDirective(SphinxDirective):
    """Generate a PlantUML dependency graph from journey dependencies.

    Usage::

        .. journey-dependency-graph::
    """

    def run(self):
        # Return a placeholder that will be replaced in doctree-resolved
        # when all journeys have been registered
        node = JourneyDependencyGraphPlaceholder()
        return [node]


def build_dependency_graph_node(env):
    """Build the PlantUML node for the journey dependency graph."""
    from sphinxcontrib.plantuml import plantuml

    journey_registry = get_journey_registry(env)

    if not journey_registry:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No journeys defined")
        return para

    # Build PlantUML content
    lines = [
        "@startuml",
        "skinparam componentStyle rectangle",
        "skinparam defaultTextAlignment center",
        "",
    ]

    # Add all journeys as components
    for slug in sorted(journey_registry.keys()):
        title = slug.replace("-", " ").title()
        lines.append(f"[{title}] as {slug.replace('-', '_')}")

    lines.append("")

    # Add dependency arrows (A depends on B => A --> B)
    for slug, journey in sorted(journey_registry.items()):
        for dep in journey["depends_on"]:
            if dep in journey_registry:
                from_id = slug.replace("-", "_")
                to_id = dep.replace("-", "_")
                lines.append(f"{from_id} --> {to_id}")

    lines.append("")
    lines.append("@enduml")

    puml_content = "\n".join(lines)

    # Use the sphinxcontrib.plantuml extension's node type
    puml_node = plantuml(puml_content)
    puml_node["uml"] = puml_content
    puml_node["incdir"] = ""
    puml_node["filename"] = "journey-dependency-graph"

    return puml_node


def process_dependency_graph_placeholder(app, doctree, docname):
    """Replace dependency graph placeholder with actual PlantUML node.

    Uses doctree-resolved event (fires after ALL documents read) to ensure
    the journey registry is complete when building the graph.
    """
    env = app.env

    for node in doctree.traverse(JourneyDependencyGraphPlaceholder):
        puml_node = build_dependency_graph_node(env)
        node.replace_self(puml_node)


class JourneysForPersonaDirective(SphinxDirective):
    """List journeys for a specific persona.

    Usage::

        .. journeys-for-persona:: Analyst
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        config = get_config()
        persona_arg = self.arguments[0]
        persona_normalized = normalize_name(persona_arg)
        docname = self.env.docname

        journey_registry = get_journey_registry(self.env)

        # Find journeys for this persona
        journeys = [
            j
            for j in journey_registry.values()
            if j["persona_normalized"] == persona_normalized
        ]

        if not journeys:
            para = nodes.paragraph()
            para += nodes.emphasis(
                text=f"No journeys found for persona '{persona_arg}'"
            )
            return [para]

        prefix = path_to_root(docname)

        bullet_list = nodes.bullet_list()

        for journey in sorted(journeys, key=lambda j: j["slug"]):
            item = nodes.list_item()
            para = nodes.paragraph()

            journey_path = (
                f"{prefix}{config.get_doc_path('journeys')}/{journey['slug']}.html"
            )
            journey_ref = nodes.reference("", "", refuri=journey_path)
            journey_ref += nodes.Text(journey["slug"].replace("-", " ").title())
            para += journey_ref

            item += para
            bullet_list += item

        return [bullet_list]


def clear_journey_state(app, env, docname):
    """Clear journey state when a document is re-read."""
    current_journey = get_current_journey(env)
    journey_registry = get_journey_registry(env)

    if docname in current_journey:
        del current_journey[docname]

    # Remove journeys defined in this document
    to_remove = [
        slug for slug, j in journey_registry.items() if j["docname"] == docname
    ]
    for slug in to_remove:
        del journey_registry[slug]


def validate_journeys(app, env):
    """Validate journey references after all documents are read."""
    from . import stories

    journey_registry = get_journey_registry(env)
    _story_registry = stories.get_story_registry()
    _known_personas = stories.get_known_personas()

    story_titles = {normalize_name(s["feature"]) for s in _story_registry}

    for slug, journey in journey_registry.items():
        # Validate persona
        if journey["persona"] and journey["persona_normalized"] not in _known_personas:
            logger.warning(
                f"Journey '{slug}' references unknown persona: '{journey['persona']}'"
            )

        # Validate depends-on journeys
        for dep in journey["depends_on"]:
            if dep not in journey_registry:
                logger.warning(
                    f"Journey '{slug}' references unknown dependency: '{dep}'"
                )

        # Validate story steps
        for step in journey["steps"]:
            if step["type"] == "story":
                if normalize_name(step["ref"]) not in story_titles:
                    logger.warning(
                        f"Journey '{slug}' references unknown story: '{step['ref']}'"
                    )


def build_story_node(story_title: str, docname: str):
    """Build a paragraph node for a story reference."""
    from . import stories

    config = get_config()
    _story_registry = stories.get_story_registry()
    _known_apps = stories.get_known_apps()

    # Find the story
    story_normalized = normalize_name(story_title)
    story = None
    for s in _story_registry:
        if normalize_name(s["feature"]) == story_normalized:
            story = s
            break

    para = nodes.paragraph()

    if story:
        # Create link to story
        para += stories.make_story_reference(story, docname, story["feature"])

        # Add app in parentheses
        prefix = path_to_root(docname)
        app_path = f"{prefix}{config.get_doc_path('applications')}/{story['app']}.html"
        app_valid = story["app_normalized"] in _known_apps

        para += nodes.Text(" (")
        if app_valid:
            app_ref = nodes.reference("", "", refuri=app_path)
            app_ref += nodes.Text(story["app"].replace("-", " ").title())
            para += app_ref
        else:
            para += nodes.Text(story["app"].replace("-", " ").title())
        para += nodes.Text(")")
    else:
        # Story not found - show warning style
        para += nodes.problematic(text=f"{story_title} [not found]")

    return para


def build_epic_node(epic_slug: str, docname: str):
    """Build a paragraph node for an epic reference."""
    config = get_config()
    prefix = path_to_root(docname)
    epic_path = f"{prefix}{config.get_doc_path('epics')}/{epic_slug}.html"

    para = nodes.paragraph()
    epic_ref = nodes.reference("", "", refuri=epic_path)
    epic_ref += nodes.Text(epic_slug.replace("-", " ").title())
    para += epic_ref
    para += nodes.Text(" (epic)")

    return para


def render_journey_steps(journey: dict, docname: str):
    """Render journey steps as a numbered list with phases grouping stories."""
    steps = journey["steps"]
    if not steps:
        return None

    # Group steps: phases contain subsequent stories/epics until next phase
    phases = []
    current_phase = None

    for step in steps:
        if step["type"] == "phase":
            # Start a new phase
            current_phase = {
                "title": step["ref"],
                "description": step.get("description", ""),
                "items": [],
            }
            phases.append(current_phase)
        elif step["type"] in ("story", "epic"):
            if current_phase is None:
                # Stories before any phase - create implicit phase
                current_phase = {"title": None, "description": "", "items": []}
                phases.append(current_phase)
            current_phase["items"].append(step)

    # Build enumerated list
    enum_list = nodes.enumerated_list()
    enum_list["enumtype"] = "arabic"

    for phase in phases:
        list_item = nodes.list_item()

        # Phase header paragraph: "Title — Description" or just items if no title
        if phase["title"]:
            header_para = nodes.paragraph()
            header_para += nodes.strong(text=phase["title"])
            if phase["description"]:
                header_para += nodes.Text(" — ")
                header_para += nodes.Text(phase["description"])
            list_item += header_para

        # Nested bullet list for stories/epics
        if phase["items"]:
            bullet_list = nodes.bullet_list()
            for item in phase["items"]:
                bullet_item = nodes.list_item()
                if item["type"] == "story":
                    bullet_item += build_story_node(item["ref"], docname)
                elif item["type"] == "epic":
                    bullet_item += build_epic_node(item["ref"], docname)
                bullet_list += bullet_item
            list_item += bullet_list

        enum_list += list_item

    return enum_list


def make_labelled_list(
    term: str, items: list, env, docname: str = None, item_type: str = "text"
):
    """Create a labelled bullet list with term as heading.

    Uses 'simple' class on bullet list for compact vertical spacing.

    item_type can be 'text' (plain text) or 'journey' (journey links).
    """
    journey_registry = get_journey_registry(env)
    container = nodes.container()

    # Term as bold paragraph
    term_para = nodes.paragraph()
    term_para += nodes.strong(text=term)
    container += term_para

    # Bullet list
    bullet_list = nodes.bullet_list()

    for item in items:
        list_item = nodes.list_item()
        # Use inline container for content to avoid paragraph gaps
        inline = nodes.inline()

        if item_type == "journey":
            related_slug = item
            related_path = f"{related_slug}.html"
            if related_slug in journey_registry:
                ref = nodes.reference("", "", refuri=related_path)
                ref += nodes.Text(related_slug.replace("-", " ").title())
                inline += ref
            else:
                inline += nodes.Text(related_slug.replace("-", " ").title())
                inline += nodes.emphasis(text=" [not found]")
        else:
            inline += nodes.Text(item)

        list_item += inline
        bullet_list += list_item

    container += bullet_list

    return container


def process_journey_steps(app, doctree):
    """Replace journey steps placeholder with rendered steps.

    Uses doctree-read event (fires after all directives parsed, before pickle)
    to ensure modifications are preserved in both HTML and LaTeX builds.
    """
    env = app.env
    docname = env.docname  # Available during doctree-read
    current_journey = get_current_journey(env)
    journey_registry = get_journey_registry(env)

    journey_slug = current_journey.get(docname)
    if not journey_slug or journey_slug not in journey_registry:
        return

    journey = journey_registry[journey_slug]

    # Find and replace the steps placeholder
    for node in doctree.traverse(nodes.container):
        if "journey-steps-placeholder" in node.get("classes", []):
            steps_node = render_journey_steps(journey, docname)
            if steps_node:
                node.replace_self(steps_node)
            else:
                node.replace_self([])
            break

    # Add preconditions if present (after steps)
    if journey["preconditions"]:
        doctree += make_labelled_list("Preconditions", journey["preconditions"], env)

    # Add postconditions if present
    if journey["postconditions"]:
        doctree += make_labelled_list("Postconditions", journey["postconditions"], env)

    # Add depends-on journeys if present
    if journey["depends_on"]:
        doctree += make_labelled_list(
            "Depends On", journey["depends_on"], env, docname, item_type="journey"
        )

    # Add depended-on-by journeys (inferred from other journeys' depends_on)
    depended_on_by = [
        j["slug"] for j in journey_registry.values() if journey_slug in j["depends_on"]
    ]
    if depended_on_by:
        doctree += make_labelled_list(
            "Depended On By", sorted(depended_on_by), env, docname, item_type="journey"
        )


def setup(app):
    app.connect("env-purge-doc", clear_journey_state)
    app.connect("env-check-consistency", validate_journeys)
    # Use doctree-read (not doctree-resolved) so modifications persist in pickled
    # doctrees for both HTML and LaTeX builders
    app.connect("doctree-read", process_journey_steps)
    # Dependency graph uses doctree-resolved (fires after ALL docs read)
    # so journey_registry is complete when building the graph
    app.connect("doctree-resolved", process_dependency_graph_placeholder)

    app.add_directive("define-journey", DefineJourneyDirective)
    app.add_directive("step-story", StepStoryDirective)
    app.add_directive("step-epic", StepEpicDirective)
    app.add_directive("step-phase", StepPhaseDirective)
    app.add_directive("journey-index", JourneyIndexDirective)
    app.add_directive("journey-dependency-graph", JourneyDependencyGraphDirective)
    app.add_directive("journeys-for-persona", JourneysForPersonaDirective)

    app.add_node(JourneyDependencyGraphPlaceholder)

    return {
        "version": "1.0",
        "parallel_read_safe": False,  # Uses global state
        "parallel_write_safe": True,
    }

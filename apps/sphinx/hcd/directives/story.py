"""Story directives for sphinx_hcd.

Provides directives for rendering user stories from Gherkin feature files:
- story-app: Full rendering of stories for an app (with anchors)
- story-list-for-persona: List of stories for a persona
- story-list-for-app: List of stories for an app
- story-index: Toctree-style index of per-app story pages
- stories: Render specific stories by name
- story: Single story reference
"""

from collections import defaultdict

from docutils import nodes

from julee.hcd.entities.story import Story
from julee.hcd.use_cases.resolve_story_references import (
    get_epics_for_story,
    get_journeys_for_story,
)
from julee.hcd.utils import normalize_name, slugify

from .base import HCDDirective, make_deprecated_directive


class StorySeeAlsoPlaceholder(nodes.General, nodes.Element):
    """Placeholder for story seealso block, replaced at doctree-read."""

    pass


class StoryAppDirective(HCDDirective):
    """Render all stories for an application with full details and anchors.

    Usage::

        .. story-app:: staff-portal

    Renders stories grouped by persona, each with:
    - Heading with anchor
    - Gherkin snippet
    - Feature file path
    """

    required_arguments = 1

    def run(self):
        app_arg = self.arguments[0]
        app_normalized = normalize_name(app_arg)

        # Get stories from repository
        all_stories = self.hcd_context.story_repo.list_all()
        stories = [s for s in all_stories if s.app_normalized == app_normalized]

        if not stories:
            return self.empty_result(f"No stories found for application '{app_arg}'")

        # Get known apps and personas for validation
        all_apps = self.hcd_context.app_repo.list_all()
        known_apps = {normalize_name(a.name) for a in all_apps}

        # Group stories by persona
        by_persona: dict[str, list[Story]] = defaultdict(list)
        for story in stories:
            by_persona[story.persona].append(story)

        result_nodes = []

        # Build intro paragraph
        persona_count = len(by_persona)
        total_stories = len(stories)
        app_display = app_arg.replace("-", " ").title()
        app_valid = app_normalized in known_apps

        intro_para = nodes.paragraph()
        intro_para += nodes.Text("The ")

        if app_valid:
            intro_para += self.make_app_link(app_arg)
        else:
            intro_para += nodes.Text(app_display)

        if total_stories == 1:
            intro_para += nodes.Text(" has one story for ")
        else:
            intro_para += nodes.Text(f" has {total_stories} stories ")

        if persona_count == 1:
            persona = list(by_persona.keys())[0]
            if total_stories != 1:
                intro_para += nodes.Text("for ")
            intro_para += self.make_persona_link(persona)
            intro_para += nodes.Text(".")
        else:
            intro_para += nodes.Text(f"across {persona_count} personas: ")
            sorted_personas = sorted(by_persona.keys())
            for i, persona in enumerate(sorted_personas):
                count = len(by_persona[persona])
                intro_para += self.make_persona_link(persona)
                intro_para += nodes.Text(f" ({count})")
                if i < len(sorted_personas) - 1:
                    intro_para += nodes.Text(", ")
                else:
                    intro_para += nodes.Text(".")

        result_nodes.append(intro_para)

        # Render stories grouped by persona
        for persona in sorted(by_persona.keys()):
            persona_stories = by_persona[persona]
            persona_slug_id = slugify(persona)

            persona_section = nodes.section(ids=[persona_slug_id])
            persona_section += nodes.title(text=persona)

            for story in sorted(persona_stories, key=lambda s: s.feature_title):
                story_section = nodes.section(ids=[story.slug])
                story_section += nodes.title(text=story.feature_title)

                # Gherkin snippet
                if story.gherkin_snippet:
                    snippet = nodes.literal_block(text=story.gherkin_snippet)
                    snippet["language"] = "gherkin"
                    story_section += snippet

                # Feature file path
                path_para = nodes.paragraph()
                path_para += nodes.strong(text="Feature file: ")
                path_para += nodes.literal(text=story.file_path)
                story_section += path_para

                # Placeholder for seealso (filled in doctree-read)
                seealso_placeholder = StorySeeAlsoPlaceholder()
                seealso_placeholder["story_feature"] = story.feature_title
                seealso_placeholder["story_persona"] = story.persona
                seealso_placeholder["story_app"] = story.app_slug
                story_section += seealso_placeholder

                persona_section += story_section

            result_nodes.append(persona_section)

        return result_nodes


class StoryListForPersonaDirective(HCDDirective):
    """Render stories for a specific persona as a simple bullet list.

    Usage::

        .. story-list-for-persona:: Pilot Manager
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        persona_arg = self.arguments[0]
        persona_normalized = normalize_name(persona_arg)

        # Get stories from repository
        all_stories = self.hcd_context.story_repo.list_all()
        stories = [s for s in all_stories if s.persona_normalized == persona_normalized]

        if not stories:
            return self.empty_result(f"No stories found for persona '{persona_arg}'")

        # Get known apps for validation
        all_apps = self.hcd_context.app_repo.list_all()
        known_apps = {normalize_name(a.name) for a in all_apps}

        story_list = nodes.bullet_list()

        for story in sorted(stories, key=lambda s: s.feature_title.lower()):
            story_item = nodes.list_item()
            story_para = nodes.paragraph()

            # Story link
            story_para += self.make_story_link(story)

            # App in parentheses
            story_para += nodes.Text(" (")
            app_valid = normalize_name(story.app_slug) in known_apps
            if app_valid:
                story_para += self.make_app_link(story.app_slug)
            else:
                story_para += nodes.Text(story.app_slug.replace("-", " ").title())
            story_para += nodes.Text(")")

            story_item += story_para
            story_list += story_item

        return [story_list]


class StoryListForAppDirective(HCDDirective):
    """Render stories for a specific application, grouped by persona then benefit.

    Usage::

        .. story-list-for-app:: staff-portal
    """

    required_arguments = 1

    def run(self):
        app_arg = self.arguments[0]
        app_normalized = normalize_name(app_arg)

        # Get stories from repository
        all_stories = self.hcd_context.story_repo.list_all()
        stories = [s for s in all_stories if s.app_normalized == app_normalized]

        if not stories:
            return self.empty_result(f"No stories found for application '{app_arg}'")

        # Group by persona, then by benefit
        by_persona: dict[str, dict[str, list[Story]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for story in stories:
            by_persona[story.persona][story.so_that].append(story)

        result_nodes = []

        for persona in sorted(by_persona.keys()):
            benefits = by_persona[persona]

            # Persona heading
            persona_heading = nodes.paragraph()
            persona_ref = self.make_persona_link(persona)
            persona_ref.children = [nodes.strong(text=persona)]
            persona_heading += persona_ref
            result_nodes.append(persona_heading)

            # Outer bullet list for benefits
            benefit_list = nodes.bullet_list()

            for benefit in sorted(benefits.keys()):
                benefit_stories = benefits[benefit]
                benefit_item = nodes.list_item()

                benefit_para = nodes.paragraph()
                benefit_para += nodes.Text("So that ")
                benefit_para += nodes.Text(benefit)
                benefit_item += benefit_para

                # Inner bullet list for features
                feature_list = nodes.bullet_list()

                for story in sorted(benefit_stories, key=lambda s: s.i_want):
                    feature_item = nodes.list_item()
                    feature_para = nodes.paragraph()
                    feature_para += nodes.Text("I need to ")
                    feature_para += self.make_story_link(story)
                    feature_item += feature_para
                    feature_list += feature_item

                benefit_item += feature_list
                benefit_list += benefit_item

            result_nodes.append(benefit_list)

        return result_nodes


class StoryIndexDirective(HCDDirective):
    """Render index pointing to per-app story pages.

    Usage::

        .. story-index::

    Renders a list of links to per-app story pages with story counts.
    """

    def run(self):
        all_stories = self.hcd_context.story_repo.list_all()

        if not all_stories:
            return self.empty_result("No Gherkin stories found")

        # Count stories per app
        stories_per_app: dict[str, int] = defaultdict(int)
        for story in all_stories:
            stories_per_app[story.app_slug] += 1

        app_list = nodes.bullet_list()

        for app in sorted(stories_per_app.keys()):
            count = stories_per_app[app]
            app_item = nodes.list_item()
            app_para = nodes.paragraph()

            # Link to app's story page
            app_ref = nodes.reference("", "", refuri=f"{app}.html")
            app_ref += nodes.strong(
                text=app.replace("-", " ").replace("_", " ").title()
            )
            app_para += app_ref
            app_para += nodes.Text(f" ({count} stories)")

            app_item += app_para
            app_list += app_item

        return [app_list]


class StoriesDirective(HCDDirective):
    """Render multiple stories grouped by persona and benefit.

    Usage::

        .. stories::
           Upload Scheme Documentation
           Add External Standard to Knowledge Base
    """

    has_content = True

    def run(self):
        # Parse feature names from content
        feature_names = [line.strip() for line in self.content if line.strip()]

        if not feature_names:
            return self.empty_result("No stories specified")

        # Get all stories for lookup
        all_stories = self.hcd_context.story_repo.list_all()
        story_lookup = {normalize_name(s.feature_title): s for s in all_stories}

        # Get known apps for validation
        all_apps = self.hcd_context.app_repo.list_all()
        known_apps = {normalize_name(a.name) for a in all_apps}

        # Look up stories
        stories = []
        not_found = []
        for feature_name in feature_names:
            feature_normalized = normalize_name(feature_name)
            story = story_lookup.get(feature_normalized)
            if story:
                stories.append(story)
            else:
                not_found.append(feature_name)

        # Group by persona, then by benefit
        by_persona: dict[str, dict[str, list[Story]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for story in stories:
            by_persona[story.persona][story.so_that].append(story)

        result_nodes = []

        for persona in sorted(by_persona.keys()):
            benefits = by_persona[persona]

            # Persona heading
            persona_heading = nodes.paragraph()
            persona_ref = self.make_persona_link(persona)
            persona_ref.children = [nodes.strong(text=persona)]
            persona_heading += persona_ref
            result_nodes.append(persona_heading)

            # Outer bullet list for benefits
            benefit_list = nodes.bullet_list()

            for benefit in sorted(benefits.keys()):
                benefit_stories = benefits[benefit]
                benefit_item = nodes.list_item()

                benefit_para = nodes.paragraph()
                benefit_para += nodes.Text("So that ")
                benefit_para += nodes.Text(benefit)
                benefit_item += benefit_para

                # Inner bullet list for features
                feature_list = nodes.bullet_list()

                for story in sorted(benefit_stories, key=lambda s: s.i_want):
                    feature_item = nodes.list_item()
                    feature_para = nodes.paragraph()
                    feature_para += nodes.Text("I need to ")
                    feature_para += self.make_story_link(story)

                    # App in parentheses
                    feature_para += nodes.Text(" (")
                    app_valid = story.app_normalized in known_apps
                    if app_valid:
                        feature_para += self.make_app_link(story.app_slug)
                    else:
                        feature_para += nodes.Text(
                            story.app_slug.replace("-", " ").title()
                        )
                        feature_para += nodes.emphasis(text=" (?)")
                    feature_para += nodes.Text(")")

                    feature_item += feature_para
                    feature_list += feature_item

                benefit_item += feature_list
                benefit_list += benefit_item

            result_nodes.append(benefit_list)

        # Add warnings for not found stories
        if not_found:
            result_nodes.append(
                self.warning_node(f"Stories not found: {', '.join(not_found)}")
            )

        return result_nodes


class StoryRefDirective(HCDDirective):
    """Render a single story reference.

    Usage::

        .. story:: Upload CMA Documents for Analysis
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        # Delegate to StoriesDirective with single story
        directive = StoriesDirective(
            self.name,
            [],  # arguments
            {},  # options
            [self.arguments[0]],  # content - single feature name
            self.lineno,
            self.content_offset,
            self.block_text,
            self.state,
            self.state_machine,
        )
        return directive.run()


def build_story_seealso(story, env, docname: str, hcd_context):
    """Build seealso block with links to related persona, app, epics, and journeys.

    Args:
        story: Story entity or dict
        env: Sphinx environment
        docname: Current document name
        hcd_context: HCDContext for accessing repositories

    Returns:
        Seealso admonition node or None if no links
    """
    from apps.sphinx.shared import path_to_root
    from julee.hcd.utils import slugify

    from ..config import get_config

    config = get_config()
    prefix = path_to_root(docname)
    links = []

    # Handle both Story entities and legacy dicts
    if hasattr(story, "persona"):
        persona = story.persona
        app_slug = story.app_slug
        feature_title = story.feature_title
    else:
        persona = story.get("persona")
        app_slug = story.get("app")
        feature_title = story.get("feature")

    # Persona link
    if persona and persona != "unknown":
        persona_slug = slugify(persona)
        persona_path = f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"
        links.append(("Persona", persona, persona_path))

    # App link
    if app_slug:
        app_path = f"{prefix}{config.get_doc_path('applications')}/{app_slug}.html"
        links.append(("App", app_slug.replace("-", " ").title(), app_path))

    # Get story entity for use cases
    all_stories = hcd_context.story_repo.list_all()
    all_epics = hcd_context.epic_repo.list_all()
    all_journeys = hcd_context.journey_repo.list_all()

    story_entity = None
    for s in all_stories:
        if normalize_name(s.feature_title) == normalize_name(feature_title):
            story_entity = s
            break

    if story_entity:
        # Epic links via use case
        epics = get_epics_for_story(story_entity, all_epics)
        for epic in epics:
            epic_title = epic.slug.replace("-", " ").title()
            epic_path = f"{prefix}{config.get_doc_path('epics')}/{epic.slug}.html"
            links.append(("Epic", epic_title, epic_path))

        # Journey links via use case
        journeys = get_journeys_for_story(story_entity, all_journeys)
        for journey in journeys:
            journey_title = journey.slug.replace("-", " ").title()
            journey_path = (
                f"{prefix}{config.get_doc_path('journeys')}/{journey.slug}.html"
            )
            links.append(("Journey", journey_title, journey_path))

    if not links:
        return None

    # Build seealso block
    seealso = nodes.admonition(classes=["seealso"])
    seealso += nodes.title(text="See also")

    line_block = nodes.line_block()
    for link_type, link_text, link_path in links:
        line = nodes.line()
        line += nodes.strong(text=f"{link_type}: ")
        ref = nodes.reference("", "", refuri=link_path)
        ref += nodes.Text(link_text)
        line += ref
        line_block += line

    seealso += line_block
    return seealso


def process_story_seealso_placeholders(app, doctree):
    """Replace story seealso placeholders with actual content.

    Uses doctree-read event so epic/journey registries are populated.
    """
    from ..context import get_hcd_context

    env = app.env
    docname = env.docname
    hcd_context = get_hcd_context(app)

    for node in doctree.traverse(StorySeeAlsoPlaceholder):
        story = {
            "feature": node["story_feature"],
            "persona": node["story_persona"],
            "app": node.get("story_app"),
        }

        seealso = build_story_seealso(story, env, docname, hcd_context)
        if seealso:
            node.replace_self([seealso])
        else:
            node.replace_self([])


# Deprecated aliases
GherkinStoryDirective = make_deprecated_directive(
    StoryRefDirective, "gherkin-story", "story"
)
GherkinStoriesDirective = make_deprecated_directive(
    StoriesDirective, "gherkin-stories", "stories"
)
GherkinStoriesForPersonaDirective = make_deprecated_directive(
    StoryListForPersonaDirective,
    "gherkin-stories-for-persona",
    "story-list-for-persona",
)
GherkinStoriesForAppDirective = make_deprecated_directive(
    StoryListForAppDirective, "gherkin-stories-for-app", "story-list-for-app"
)
GherkinStoriesIndexDirective = make_deprecated_directive(
    StoryIndexDirective, "gherkin-stories-index", "story-index"
)
GherkinAppStoriesDirective = make_deprecated_directive(
    StoryAppDirective, "gherkin-app-stories", "story-app"
)

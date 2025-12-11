"""Sphinx extension to index and render Gherkin feature files as user stories.

Provides directives:
- story-app: Full rendering of stories for an app (with anchors)
- story-list-for-persona: List of stories for a persona
- story-list-for-app: List of stories for an app
- story-index: Toctree-style index of per-app story pages
- stories: Render specific stories by name
- story: Single story reference

Legacy aliases (deprecated, emit warnings):
- gherkin-app-stories -> story-app
- gherkin-stories-for-persona -> story-list-for-persona
- gherkin-stories-for-app -> story-list-for-app
- gherkin-stories-index -> story-index
- gherkin-stories -> stories
- gherkin-story -> story
"""

import re
import warnings
from pathlib import Path
from collections import defaultdict
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

from .config import get_config
from .utils import normalize_name, slugify, path_to_root

logger = logging.getLogger(__name__)

# Global registry populated at build init
_story_registry: list[dict] = []
_known_apps: set[str] = set()
_known_personas: set[str] = set()
_apps_with_stories: set[str] = set()


def get_story_registry() -> list[dict]:
    """Get the story registry."""
    return _story_registry


def get_known_apps() -> set[str]:
    """Get set of known app names (normalized)."""
    return _known_apps


def get_known_personas() -> set[str]:
    """Get set of known persona names (normalized)."""
    return _known_personas


def get_apps_with_stories() -> set[str]:
    """Get set of apps that have stories."""
    return _apps_with_stories


def get_epics_for_story(story_title: str, env) -> list[str]:
    """Find epics that reference this story."""
    from . import epics
    epic_registry = epics.get_epic_registry(env)
    story_normalized = normalize_name(story_title)

    matching_epics = []
    for slug, epic in epic_registry.items():
        for epic_story in epic.get('stories', []):
            if normalize_name(epic_story) == story_normalized:
                matching_epics.append(slug)
                break

    return sorted(matching_epics)


def get_journeys_for_story(story_title: str, env) -> list[str]:
    """Find journeys that reference this story (directly or via epic)."""
    from . import journeys
    journey_registry = journeys.get_journey_registry(env)
    story_normalized = normalize_name(story_title)

    matching_journeys = []
    for slug, journey in journey_registry.items():
        for step in journey.get('steps', []):
            if step.get('type') == 'story':
                if normalize_name(step['ref']) == story_normalized:
                    matching_journeys.append(slug)
                    break

    return sorted(matching_journeys)


def build_story_seealso(story: dict, env, docname: str):
    """Build seealso block with links to related persona, app, epics, and journeys."""
    config = get_config()
    prefix = path_to_root(docname)

    links = []

    # Persona link
    persona = story.get('persona')
    if persona and persona != 'unknown':
        persona_slug = slugify(persona)
        persona_path = f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"
        links.append(('Persona', persona, persona_path))

    # App link
    app = story.get('app')
    if app:
        app_path = f"{prefix}{config.get_doc_path('applications')}/{app}.html"
        links.append(('App', app.replace("-", " ").title(), app_path))

    # Epic links
    epics_list = get_epics_for_story(story['feature'], env)
    for epic_slug in epics_list:
        epic_title = epic_slug.replace("-", " ").title()
        epic_path = f"{prefix}{config.get_doc_path('epics')}/{epic_slug}.html"
        links.append(('Epic', epic_title, epic_path))

    # Journey links
    journeys_list = get_journeys_for_story(story['feature'], env)
    for journey_slug in journeys_list:
        journey_title = journey_slug.replace("-", " ").title()
        journey_path = f"{prefix}{config.get_doc_path('journeys')}/{journey_slug}.html"
        links.append(('Journey', journey_title, journey_path))

    if not links:
        return None

    # Build seealso block with line_block for tight spacing
    seealso = nodes.admonition(classes=['seealso'])
    seealso += nodes.title(text='See also')

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


class StorySeeAlsoPlaceholder(nodes.General, nodes.Element):
    """Placeholder for story seealso block, replaced at doctree-read."""
    pass


def scan_feature_files(app):
    """Scan tests/e2e/**/features/*.feature and build the story registry."""
    global _story_registry, _apps_with_stories
    _story_registry = []
    _apps_with_stories = set()

    config = get_config()
    project_root = config.project_root
    tests_dir = config.get_path('feature_files')

    if not tests_dir.exists():
        logger.info(f"Feature files directory not found at {tests_dir} - no stories to index")
        return

    # Scan for feature files
    for feature_file in tests_dir.rglob("*.feature"):
        rel_path = feature_file.relative_to(project_root)

        # Extract app name from path: tests/e2e/{app}/features/{name}.feature
        parts = rel_path.parts
        if len(parts) >= 4 and parts[2] != "features":
            app_name = parts[2]  # e.g., "staff-portal"
        else:
            app_name = "unknown"

        # Parse the feature file
        try:
            with open(feature_file) as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            logger.warning(f"Could not read {feature_file}: {e}")
            continue

        # Extract header components
        feature_match = re.search(r"^Feature:\s*(.+)$", content, re.MULTILINE)
        as_a_match = re.search(r"^\s*As an?\s+(.+)$", content, re.MULTILINE)
        i_want_match = re.search(r"^\s*I want to\s+(.+)$", content, re.MULTILINE)
        so_that_match = re.search(r"^\s*So that\s+(.+)$", content, re.MULTILINE)

        # Extract Gherkin snippet (user story header only, stop before Background/Scenario)
        snippet_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('Scenario', 'Background', '@', 'Given', 'When', 'Then', 'And', 'But')):
                break
            if stripped:
                snippet_lines.append(line)
        gherkin_snippet = '\n'.join(snippet_lines)

        feature_title = feature_match.group(1) if feature_match else "Unknown"
        story = {
            "app": app_name,
            "app_normalized": normalize_name(app_name),
            "feature": feature_title,
            "slug": slugify(feature_title),
            "persona": as_a_match.group(1) if as_a_match else "unknown",
            "persona_normalized": normalize_name(as_a_match.group(1)) if as_a_match else "unknown",
            "i_want": i_want_match.group(1) if i_want_match else "do something",
            "so_that": so_that_match.group(1) if so_that_match else "achieve a goal",
            "path": str(rel_path),
            "abs_path": str(feature_file),
            "gherkin_snippet": gherkin_snippet,
        }
        _story_registry.append(story)
        _apps_with_stories.add(app_name)

    logger.info(f"Indexed {len(_story_registry)} Gherkin stories")


def scan_known_entities(app):
    """Scan docs to find known applications and personas."""
    global _known_apps, _known_personas
    _known_apps = set()
    _known_personas = set()

    config = get_config()
    docs_dir = config.docs_dir

    # Scan applications
    apps_dir = docs_dir / config.get_doc_path('applications')
    if apps_dir.exists():
        for rst_file in apps_dir.glob("*.rst"):
            if rst_file.name != "index.rst":
                app_name = rst_file.stem
                _known_apps.add(normalize_name(app_name))

    # Scan personas
    personas_dir = docs_dir / config.get_doc_path('personas')
    if personas_dir.exists():
        for rst_file in personas_dir.glob("*.rst"):
            if rst_file.name != "index.rst":
                persona_name = rst_file.stem
                _known_personas.add(normalize_name(persona_name))

    logger.info(f"Found {len(_known_apps)} apps: {_known_apps}")
    logger.info(f"Found {len(_known_personas)} personas: {_known_personas}")


def builder_inited(app):
    """Called when builder is initialized - scan and index feature files."""
    scan_feature_files(app)
    scan_known_entities(app)

    # Collect apps and personas that have stories
    apps_with_stories = set()
    personas_with_stories = set()
    unknown_apps = set()
    unknown_personas = set()

    for story in _story_registry:
        apps_with_stories.add(story["app_normalized"])
        personas_with_stories.add(story["persona_normalized"])

        if story["app_normalized"] not in _known_apps:
            unknown_apps.add(story["app"])
        if story["persona_normalized"] not in _known_personas:
            unknown_personas.add(story["persona"])

    # Warn about stories referencing undocumented entities
    for app_name in sorted(unknown_apps):
        logger.warning(f"Gherkin story references undocumented application: '{app_name}'")
    for persona in sorted(unknown_personas):
        logger.warning(f"Gherkin story references undocumented persona: '{persona}'")

    # Warn about documented entities with no stories
    apps_without_stories = _known_apps - apps_with_stories
    personas_without_stories = _known_personas - personas_with_stories

    for app_name in sorted(apps_without_stories):
        logger.info(f"Application '{app_name}' has no Gherkin stories yet")
    for persona in sorted(personas_without_stories):
        logger.info(f"Persona '{persona}' has no Gherkin stories yet")


def get_story_ref_target(story: dict, from_docname: str) -> tuple[str, str]:
    """Get the reference target for a story from a given document.

    Returns (docname, anchor) tuple for the story's location on its app's story page.
    """
    config = get_config()
    app_slug = story["app"]
    story_slug = story["slug"]
    return f"{config.get_doc_path('stories')}/{app_slug}", story_slug


def make_story_reference(story: dict, from_docname: str, link_text: str | None = None) -> nodes.reference:
    """Create a reference node linking to a story's anchor on its app page."""
    target_doc, anchor = get_story_ref_target(story, from_docname)

    # Calculate relative path from current doc to target
    from_parts = from_docname.split('/')
    target_parts = target_doc.split('/')

    # Find common prefix
    common = 0
    for i in range(min(len(from_parts), len(target_parts))):
        if from_parts[i] == target_parts[i]:
            common += 1
        else:
            break

    # Build relative path
    up_levels = len(from_parts) - common - 1
    down_path = '/'.join(target_parts[common:])

    if up_levels > 0:
        rel_path = '../' * up_levels + down_path + '.html'
    else:
        rel_path = down_path + '.html'

    ref_uri = f"{rel_path}#{anchor}"

    ref = nodes.reference("", "", refuri=ref_uri)
    ref += nodes.Text(link_text or story["i_want"])
    return ref


class StoryAppDirective(SphinxDirective):
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
        config = get_config()
        app_arg = self.arguments[0]
        app_normalized = normalize_name(app_arg)

        # Filter stories for this app
        stories = [s for s in _story_registry
                   if s["app_normalized"] == app_normalized]

        if not stories:
            para = nodes.paragraph()
            para += nodes.emphasis(text=f"No stories found for application '{app_arg}'")
            return [para]

        # Calculate relative paths
        docname = self.env.docname
        prefix = path_to_root(docname)

        # Group stories by persona
        by_persona = defaultdict(list)
        for story in stories:
            by_persona[story["persona"]].append(story)

        result_nodes = []

        # Build intro paragraph with app link and persona breakdown
        persona_count = len(by_persona)
        total_stories = len(stories)
        app_display = app_arg.replace("-", " ").title()
        app_path = f"{prefix}{config.get_doc_path('applications')}/{app_arg}.html"
        app_valid = app_normalized in _known_apps

        intro_para = nodes.paragraph()
        intro_para += nodes.Text("The ")

        if app_valid:
            app_ref = nodes.reference("", "", refuri=app_path)
            app_ref += nodes.Text(app_display)
            intro_para += app_ref
        else:
            intro_para += nodes.Text(app_display)

        if total_stories == 1:
            intro_para += nodes.Text(" has one story for ")
        else:
            intro_para += nodes.Text(f" has {total_stories} stories ")

        if persona_count == 1:
            # Single persona
            persona = list(by_persona.keys())[0]
            persona_valid = normalize_name(persona) in _known_personas
            persona_slug = persona.lower().replace(" ", "-")
            persona_path = f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"

            if total_stories != 1:
                intro_para += nodes.Text("for ")

            if persona_valid:
                persona_ref = nodes.reference("", "", refuri=persona_path)
                persona_ref += nodes.Text(persona)
                intro_para += persona_ref
            else:
                intro_para += nodes.Text(persona)

            intro_para += nodes.Text(".")
        else:
            # Multiple personas - list them with counts
            intro_para += nodes.Text(f"across {persona_count} personas: ")

            sorted_personas = sorted(by_persona.keys())
            for i, persona in enumerate(sorted_personas):
                count = len(by_persona[persona])
                persona_valid = normalize_name(persona) in _known_personas
                persona_slug = persona.lower().replace(" ", "-")
                persona_path = f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"

                if persona_valid:
                    persona_ref = nodes.reference("", "", refuri=persona_path)
                    persona_ref += nodes.Text(persona)
                    intro_para += persona_ref
                else:
                    intro_para += nodes.Text(persona)

                intro_para += nodes.Text(f" ({count})")

                if i < len(sorted_personas) - 1:
                    intro_para += nodes.Text(", ")
                else:
                    intro_para += nodes.Text(".")

        result_nodes.append(intro_para)

        for persona in sorted(by_persona.keys()):
            persona_stories = by_persona[persona]
            persona_slug_id = slugify(persona)

            # Persona section
            persona_section = nodes.section(ids=[persona_slug_id])

            # Persona title (plain text, no count)
            persona_title = nodes.title(text=persona)
            persona_section += persona_title

            # Stories for this persona
            for story in sorted(persona_stories, key=lambda s: s["feature"]):
                # Story section with anchor
                story_section = nodes.section(ids=[story["slug"]])

                # Title
                title = nodes.title(text=story["feature"])
                story_section += title

                # Gherkin snippet as literal block
                snippet = nodes.literal_block(text=story["gherkin_snippet"])
                snippet['language'] = 'gherkin'
                story_section += snippet

                # Feature file path (for reference, not as broken link)
                path_para = nodes.paragraph()
                path_para += nodes.strong(text="Feature file: ")
                path_para += nodes.literal(text=story["path"])
                story_section += path_para

                # Placeholder for seealso (filled in doctree-read when registries are complete)
                seealso_placeholder = StorySeeAlsoPlaceholder()
                seealso_placeholder['story_feature'] = story["feature"]
                seealso_placeholder['story_persona'] = story["persona"]
                seealso_placeholder['story_app'] = story["app"]
                story_section += seealso_placeholder

                persona_section += story_section

            result_nodes.append(persona_section)

        return result_nodes


class StoryListForPersonaDirective(SphinxDirective):
    """Render stories for a specific persona as a simple bullet list.

    Usage::

        .. story-list-for-persona:: Pilot Manager
    """

    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        config = get_config()
        persona_arg = self.arguments[0]
        persona_normalized = normalize_name(persona_arg)

        # Filter stories for this persona
        stories = [s for s in _story_registry
                   if s["persona_normalized"] == persona_normalized]

        if not stories:
            para = nodes.paragraph()
            para += nodes.emphasis(text=f"No stories found for persona '{persona_arg}'")
            return [para]

        # Calculate relative paths
        docname = self.env.docname
        prefix = path_to_root(docname)

        result_nodes = []

        # Simple bullet list: "story name (App Name)"
        story_list = nodes.bullet_list()

        for story in sorted(stories, key=lambda s: s['feature'].lower()):
            story_item = nodes.list_item()
            story_para = nodes.paragraph()

            # Story link
            story_para += make_story_reference(story, docname)

            # App in parentheses
            story_para += nodes.Text(" (")
            app_path = f"{prefix}{config.get_doc_path('applications')}/{story['app']}.html"
            app_valid = normalize_name(story['app']) in _known_apps

            if app_valid:
                app_ref = nodes.reference("", "", refuri=app_path)
                app_ref += nodes.Text(story['app'].replace("-", " ").title())
                story_para += app_ref
            else:
                story_para += nodes.Text(story['app'].replace("-", " ").title())

            story_para += nodes.Text(")")

            story_item += story_para
            story_list += story_item

        result_nodes.append(story_list)

        return result_nodes


class StoryListForAppDirective(SphinxDirective):
    """Render stories for a specific application, grouped by persona then benefit.

    Usage::

        .. story-list-for-app:: staff-portal
    """

    required_arguments = 1

    def run(self):
        config = get_config()
        app_arg = self.arguments[0]
        app_normalized = normalize_name(app_arg)

        # Filter stories for this app
        stories = [s for s in _story_registry
                   if s["app_normalized"] == app_normalized]

        if not stories:
            para = nodes.paragraph()
            para += nodes.emphasis(text=f"No stories found for application '{app_arg}'")
            return [para]

        # Calculate relative paths
        docname = self.env.docname
        prefix = path_to_root(docname)

        # Group by persona, then by benefit
        by_persona = defaultdict(lambda: defaultdict(list))
        for story in stories:
            by_persona[story["persona"]][story["so_that"]].append(story)

        result_nodes = []

        for persona in sorted(by_persona.keys()):
            benefits = by_persona[persona]
            persona_valid = normalize_name(persona) in _known_personas

            # Persona heading (strong with link)
            persona_heading = nodes.paragraph()
            persona_slug = persona.lower().replace(" ", "-")
            persona_path = f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"

            if persona_valid:
                persona_ref = nodes.reference("", "", refuri=persona_path)
                persona_ref += nodes.strong(text=persona)
                persona_heading += persona_ref
            else:
                persona_heading += nodes.strong(text=persona)
                persona_heading += nodes.emphasis(text=" (?)")

            result_nodes.append(persona_heading)

            # Outer bullet list for benefits
            benefit_list = nodes.bullet_list()

            for benefit in sorted(benefits.keys()):
                benefit_stories = benefits[benefit]

                # Benefit list item
                benefit_item = nodes.list_item()

                # Benefit text with "So that" prefix
                benefit_para = nodes.paragraph()
                benefit_para += nodes.Text("So that ")
                benefit_para += nodes.Text(benefit)
                benefit_item += benefit_para

                # Inner bullet list for features
                feature_list = nodes.bullet_list()

                for story in sorted(benefit_stories, key=lambda s: s["i_want"]):
                    feature_item = nodes.list_item()
                    feature_para = nodes.paragraph()

                    # Feature link with "I need to" prefix - links to story anchor
                    feature_para += nodes.Text("I need to ")
                    feature_para += make_story_reference(story, docname)

                    feature_item += feature_para
                    feature_list += feature_item

                benefit_item += feature_list
                benefit_list += benefit_item

            result_nodes.append(benefit_list)

        return result_nodes


class StoryIndexDirective(SphinxDirective):
    """Render index pointing to per-app story pages.

    Usage::

        .. story-index::

    Renders a list of links to per-app story pages with story counts.
    """

    def run(self):
        if not _story_registry:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No Gherkin stories found")
            return [para]

        # Count stories per app
        stories_per_app = defaultdict(int)
        for story in _story_registry:
            stories_per_app[story["app"]] += 1

        result_nodes = []

        # Create bullet list of app links
        app_list = nodes.bullet_list()

        for app in sorted(stories_per_app.keys()):
            count = stories_per_app[app]
            app_item = nodes.list_item()
            app_para = nodes.paragraph()

            # Link to app's story page
            app_ref = nodes.reference("", "", refuri=f"{app}.html")
            app_ref += nodes.strong(text=app.replace("-", " ").replace("_", " ").title())
            app_para += app_ref
            app_para += nodes.Text(f" ({count} stories)")

            app_item += app_para
            app_list += app_item

        result_nodes.append(app_list)

        return result_nodes


class StoriesDirective(SphinxDirective):
    """Render multiple stories grouped by persona and benefit.

    Usage::

        .. stories::
           Upload Scheme Documentation
           Add External Standard to Knowledge Base
    """

    has_content = True

    def run(self):
        config = get_config()

        # Parse feature names from content (one per line)
        feature_names = [line.strip() for line in self.content if line.strip()]

        if not feature_names:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No stories specified")
            return [para]

        # Look up stories
        stories = []
        not_found = []
        for feature_name in feature_names:
            feature_normalized = normalize_name(feature_name)
            story = None
            for s in _story_registry:
                if normalize_name(s["feature"]) == feature_normalized:
                    story = s
                    break
            if story:
                stories.append(story)
            else:
                not_found.append(feature_name)

        # Calculate relative paths
        docname = self.env.docname
        prefix = path_to_root(docname)

        # Group by persona, then by benefit
        by_persona = defaultdict(lambda: defaultdict(list))
        for story in stories:
            by_persona[story["persona"]][story["so_that"]].append(story)

        result_nodes = []

        # Render each persona group
        for persona in sorted(by_persona.keys()):
            benefits = by_persona[persona]

            # Persona heading (strong)
            persona_heading = nodes.paragraph()
            persona_slug = persona.lower().replace(" ", "-")
            persona_path = f"{prefix}{config.get_doc_path('personas')}/{persona_slug}.html"
            persona_valid = normalize_name(persona) in _known_personas

            if persona_valid:
                persona_ref = nodes.reference("", "", refuri=persona_path)
                persona_ref += nodes.strong(text=persona)
                persona_heading += persona_ref
            else:
                persona_heading += nodes.strong(text=persona)
                persona_heading += nodes.emphasis(text=" (?)")

            result_nodes.append(persona_heading)

            # Outer bullet list for benefits
            benefit_list = nodes.bullet_list()

            for benefit in sorted(benefits.keys()):
                benefit_stories = benefits[benefit]

                # Benefit list item
                benefit_item = nodes.list_item()

                # Benefit text with "So that" prefix
                benefit_para = nodes.paragraph()
                benefit_para += nodes.Text("So that ")
                benefit_para += nodes.Text(benefit)
                benefit_item += benefit_para

                # Inner bullet list for features
                feature_list = nodes.bullet_list()

                for story in sorted(benefit_stories, key=lambda s: s["i_want"]):
                    feature_item = nodes.list_item()
                    feature_para = nodes.paragraph()

                    # Feature link with "I need to" prefix
                    feature_para += nodes.Text("I need to ")
                    feature_para += make_story_reference(story, docname)

                    # App in parentheses
                    feature_para += nodes.Text(" (")
                    app_path = f"{prefix}{config.get_doc_path('applications')}/{story['app']}.html"
                    app_valid = story["app_normalized"] in _known_apps

                    if app_valid:
                        app_ref = nodes.reference("", "", refuri=app_path)
                        app_ref += nodes.Text(story["app"].replace("-", " ").title())
                        feature_para += app_ref
                    else:
                        feature_para += nodes.Text(story["app"].replace("-", " ").title())
                        feature_para += nodes.emphasis(text=" (?)")

                    feature_para += nodes.Text(")")

                    feature_item += feature_para
                    feature_list += feature_item

                benefit_item += feature_list
                benefit_list += benefit_item

            result_nodes.append(benefit_list)

        # Add warnings for not found stories
        if not_found:
            warning_para = nodes.paragraph()
            warning_para += nodes.problematic(
                text=f"[Stories not found: {', '.join(not_found)}]"
            )
            result_nodes.append(warning_para)

        return result_nodes


class StoryRefDirective(SphinxDirective):
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


# Deprecated alias directives - emit warnings and delegate to new names

def _make_deprecated_directive(new_directive_class, old_name: str, new_name: str):
    """Create a deprecated alias directive that warns and delegates."""

    class DeprecatedDirective(new_directive_class):
        def run(self):
            logger.warning(
                f"Directive '{old_name}' is deprecated, use '{new_name}' instead. "
                f"(in {self.env.docname})"
            )
            return super().run()

    return DeprecatedDirective


def process_story_seealso_placeholders(app, doctree):
    """Replace story seealso placeholders with actual content.

    Uses doctree-read event so epic/journey registries are populated.
    """
    env = app.env
    docname = env.docname

    for node in doctree.traverse(StorySeeAlsoPlaceholder):
        story_feature = node['story_feature']
        story_persona = node['story_persona']
        story_app = node.get('story_app')

        # Build a minimal story dict for the helper function
        story = {
            'feature': story_feature,
            'persona': story_persona,
            'app': story_app,
        }

        seealso = build_story_seealso(story, env, docname)
        if seealso:
            node.replace_self([seealso])
        else:
            node.replace_self([])


def setup(app):
    app.connect("builder-inited", builder_inited)
    app.connect("doctree-read", process_story_seealso_placeholders)

    # New directive names
    app.add_directive("story", StoryRefDirective)
    app.add_directive("stories", StoriesDirective)
    app.add_directive("story-list-for-persona", StoryListForPersonaDirective)
    app.add_directive("story-list-for-app", StoryListForAppDirective)
    app.add_directive("story-index", StoryIndexDirective)
    app.add_directive("story-app", StoryAppDirective)

    # Deprecated aliases (gherkin-* -> story-*)
    app.add_directive(
        "gherkin-story",
        _make_deprecated_directive(StoryRefDirective, "gherkin-story", "story")
    )
    app.add_directive(
        "gherkin-stories",
        _make_deprecated_directive(StoriesDirective, "gherkin-stories", "stories")
    )
    app.add_directive(
        "gherkin-stories-for-persona",
        _make_deprecated_directive(
            StoryListForPersonaDirective,
            "gherkin-stories-for-persona",
            "story-list-for-persona"
        )
    )
    app.add_directive(
        "gherkin-stories-for-app",
        _make_deprecated_directive(
            StoryListForAppDirective,
            "gherkin-stories-for-app",
            "story-list-for-app"
        )
    )
    app.add_directive(
        "gherkin-stories-index",
        _make_deprecated_directive(StoryIndexDirective, "gherkin-stories-index", "story-index")
    )
    app.add_directive(
        "gherkin-app-stories",
        _make_deprecated_directive(StoryAppDirective, "gherkin-app-stories", "story-app")
    )

    app.add_node(StorySeeAlsoPlaceholder)

    return {
        "version": "1.0",
        "parallel_read_safe": False,  # Uses environment registries
        "parallel_write_safe": True,
    }

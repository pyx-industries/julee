"""Base directive and utilities for sphinx_hcd directives.

Provides common functionality for building docutils nodes and accessing
the HCDContext repositories.
"""

from typing import TYPE_CHECKING

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.shared import path_to_root
from julee.hcd.utils import slugify

from ..config import get_config
from ..context import HCDContext, get_hcd_context

if TYPE_CHECKING:
    pass


class HCDDirective(SphinxDirective):
    """Base directive with HCD context access.

    All HCD directives inherit from this to get easy access to:
    - HCDContext with all repositories
    - Config for path resolution
    - Common node-building utilities
    """

    @property
    def hcd_context(self) -> HCDContext:
        """Get the HCD context from Sphinx app."""
        return get_hcd_context(self.env.app)

    @property
    def hcd_config(self):
        """Get the HCD configuration."""
        return get_config()

    @property
    def docname(self) -> str:
        """Get the current document name."""
        return self.env.docname

    @property
    def prefix(self) -> str:
        """Get relative path prefix to docs root."""
        return path_to_root(self.docname)

    def get_doc_path(self, doc_type: str) -> str:
        """Get the path for a documentation type with prefix."""
        return f"{self.prefix}{self.hcd_config.get_doc_path(doc_type)}"

    def make_link(
        self,
        text: str,
        path: str,
        strong: bool = False,
    ) -> nodes.reference:
        """Create a reference node with text.

        Args:
            text: Link text
            path: Target path (relative or absolute)
            strong: Whether to make text bold

        Returns:
            Reference node
        """
        ref = nodes.reference("", "", refuri=path)
        if strong:
            ref += nodes.strong(text=text)
        else:
            ref += nodes.Text(text)
        return ref

    def make_app_link(self, app_slug: str) -> nodes.reference:
        """Create a link to an app page."""
        app_name = app_slug.replace("-", " ").title()
        app_path = f"{self.get_doc_path('applications')}/{app_slug}.html"
        return self.make_link(app_name, app_path)

    def make_persona_link(self, persona_name: str) -> nodes.reference:
        """Create a link to a persona page."""
        persona_slug = slugify(persona_name)
        persona_path = f"{self.get_doc_path('personas')}/{persona_slug}.html"
        return self.make_link(persona_name, persona_path)

    def make_epic_link(self, epic_slug: str) -> nodes.reference:
        """Create a link to an epic page."""
        epic_name = epic_slug.replace("-", " ").title()
        epic_path = f"{self.get_doc_path('epics')}/{epic_slug}.html"
        return self.make_link(epic_name, epic_path)

    def make_journey_link(self, journey_slug: str) -> nodes.reference:
        """Create a link to a journey page."""
        journey_name = journey_slug.replace("-", " ").title()
        journey_path = f"{self.get_doc_path('journeys')}/{journey_slug}.html"
        return self.make_link(journey_name, journey_path)

    def make_story_link(
        self,
        story,
        link_text: str | None = None,
    ) -> nodes.reference:
        """Create a link to a story on its app's story page.

        Args:
            story: Story entity or dict with app, slug, i_want
            link_text: Optional link text (defaults to i_want)

        Returns:
            Reference node linking to story anchor
        """
        # Handle both Story entities and legacy dicts
        if hasattr(story, "app_slug"):
            app_slug = story.app_slug
            story_slug = story.slug
            default_text = story.i_want
        else:
            app_slug = story.get("app", story.get("app_slug"))
            story_slug = story.get("slug")
            default_text = story.get("i_want", story.get("feature_title", ""))

        config = self.hcd_config
        target_doc = f"{config.get_doc_path('stories')}/{app_slug}"
        ref_uri = self._build_relative_uri(target_doc, story_slug)

        ref = nodes.reference("", "", refuri=ref_uri)
        ref += nodes.Text(link_text or default_text)
        return ref

    def _build_relative_uri(
        self,
        target_doc: str,
        anchor: str | None = None,
    ) -> str:
        """Build a relative URI from current doc to target.

        Args:
            target_doc: Target document path (without .html)
            anchor: Optional anchor within target

        Returns:
            Relative URI string
        """
        from_parts = self.docname.split("/")
        target_parts = target_doc.split("/")

        # Find common prefix
        common = 0
        for i in range(min(len(from_parts), len(target_parts))):
            if from_parts[i] == target_parts[i]:
                common += 1
            else:
                break

        # Build relative path
        up_levels = len(from_parts) - common - 1
        down_path = "/".join(target_parts[common:])

        if up_levels > 0:
            rel_path = "../" * up_levels + down_path + ".html"
        else:
            rel_path = down_path + ".html"

        if anchor:
            return f"{rel_path}#{anchor}"
        return rel_path

    def empty_result(self, message: str) -> list[nodes.Node]:
        """Create an emphasized message for empty results."""
        para = nodes.paragraph()
        para += nodes.emphasis(text=message)
        return [para]

    def warning_node(self, message: str) -> nodes.paragraph:
        """Create a warning paragraph with problematic text."""
        para = nodes.paragraph()
        para += nodes.problematic(text=f"[{message}]")
        return para


def parse_rst_content(rst_text: str, source_name: str = "<rst>") -> list[nodes.Node]:
    """Parse RST text into docutils nodes.

    Args:
        rst_text: RST-formatted text to parse
        source_name: Name for error messages

    Returns:
        List of docutils nodes
    """
    from docutils.core import publish_doctree
    from docutils.parsers.rst import Parser

    # Parse RST to doctree with full RST support
    doctree = publish_doctree(
        rst_text,
        source_path=source_name,
        parser=Parser(),
        settings_overrides={
            "report_level": 4,  # Only show severe errors
            "halt_level": 5,  # Never halt
            "input_encoding": "unicode",
            "output_encoding": "unicode",
        },
    )

    # Return children of the document (skip the document node itself)
    return list(doctree.children)


def make_deprecated_directive(
    base_class: type,
    old_name: str,
    new_name: str,
) -> type:
    """Create a deprecated alias directive that warns and delegates.

    Args:
        base_class: The directive class to wrap
        old_name: The deprecated directive name
        new_name: The new directive name

    Returns:
        A new directive class that warns and delegates
    """
    from sphinx.util import logging

    logger = logging.getLogger(__name__)

    class DeprecatedDirective(base_class):
        def run(self):
            logger.warning(
                f"Directive '{old_name}' is deprecated, use '{new_name}' instead. "
                f"(in {self.env.docname})"
            )
            return super().run()

    DeprecatedDirective.__name__ = f"Deprecated{base_class.__name__}"
    return DeprecatedDirective

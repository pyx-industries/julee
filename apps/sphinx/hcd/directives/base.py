"""Base directive and utilities for sphinx_hcd directives.

Provides common functionality for building docutils nodes and accessing
the HCDContext repositories.
"""

from typing import TYPE_CHECKING

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.shared import build_relative_uri, path_to_root
from apps.sphinx.shared.documentation_mapping import get_documentation_mapping
from apps.sphinx.shared.services.entity_link_builder import EntityLinkBuilder
from julee.hcd.utils import slugify

from ..config import get_config
from ..context import HCDContext, get_hcd_context

if TYPE_CHECKING:
    from apps.sphinx.shared.documentation_mapping import DocumentationMapping


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
    def solution_slug(self) -> str:
        """Get the current solution slug for entity scoping."""
        return self.hcd_config.solution_slug

    @property
    def docname(self) -> str:
        """Get the current document name."""
        return self.env.docname

    @property
    def prefix(self) -> str:
        """Get relative path prefix to docs root."""
        return path_to_root(self.docname)

    @property
    def link_builder(self) -> EntityLinkBuilder:
        """Get EntityLinkBuilder for creating entity links."""
        if not hasattr(self, "_link_builder"):
            self._link_builder = EntityLinkBuilder(get_documentation_mapping())
        return self._link_builder

    def get_doc_path(self, doc_type: str) -> str:
        """Get the path for a documentation type with prefix."""
        return f"{self.prefix}{self.hcd_config.get_doc_path(doc_type)}"

    def make_entity_link(
        self,
        entity_type: type,
        slug: str,
        title: str | None = None,
        anchor: str | None = None,
        strong: bool = False,
    ) -> nodes.reference:
        """Create a link to any entity using SemanticRelation.

        Uses EntityLinkBuilder and DocumentationMapping to resolve the
        entity type to its documentation page via semantic relations.

        Args:
            entity_type: The entity class (e.g., Persona, Accelerator)
            slug: Entity slug
            title: Display text (defaults to titlecased slug)
            anchor: Optional anchor within the page
            strong: Whether to make text bold

        Returns:
            Reference node
        """
        return self.link_builder.build_node(
            entity_type, slug, title, self.prefix, anchor, strong
        )

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
        """Create a link to an app page.

        Uses make_entity_link with HCD App entity type.
        """
        from julee.hcd.entities.app import App

        return self.make_entity_link(App, app_slug)

    def make_persona_link(self, persona_name: str) -> nodes.reference:
        """Create a link to a persona page.

        Uses make_entity_link with Persona entity type.
        Note: Accepts persona name and slugifies it.
        """
        from julee.hcd.entities.persona import Persona

        persona_slug = slugify(persona_name)
        return self.make_entity_link(Persona, persona_slug, title=persona_name)

    def make_epic_link(self, epic_slug: str) -> nodes.reference:
        """Create a link to an epic page.

        Uses make_entity_link with Epic entity type.
        """
        from julee.hcd.entities.epic import Epic

        return self.make_entity_link(Epic, epic_slug)

    def make_journey_link(self, journey_slug: str) -> nodes.reference:
        """Create a link to a journey page.

        Uses make_entity_link with Journey entity type.
        """
        from julee.hcd.entities.journey import Journey

        return self.make_entity_link(Journey, journey_slug)

    def make_accelerator_link(self, accelerator_slug: str) -> nodes.reference:
        """Create a link to an accelerator page.

        Uses make_entity_link with Accelerator entity type.
        Accelerator PROJECTS BoundedContext, so resolves to BC autoapi page.
        """
        from julee.supply_chain.entities.accelerator import Accelerator

        return self.make_entity_link(Accelerator, accelerator_slug)

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
        return build_relative_uri(self.docname, target_doc, anchor)

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

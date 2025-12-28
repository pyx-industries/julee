"""Jinja2 implementation of DocumentationRenderingService.

Renders entities to RST documentation using Jinja2 templates.
Handles Sphinx-specific path resolution for relative links.

Template discovery follows convention:
    {template_dir}/{entity_type}_{view_type}.rst.j2

Example:
    persona_index.rst.j2
    persona_detail.rst.j2
    epic_summary.rst.j2
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from pydantic import BaseModel


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _pluralize(name: str) -> str:
    """Simple English pluralization."""
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    elif name.endswith("s") or name.endswith("x") or name.endswith("ch"):
        return name + "es"
    return name + "s"


def _title_case(slug: str) -> str:
    """Convert slug to title case."""
    return slug.replace("-", " ").replace("_", " ").title()


def _first_sentence(text: str) -> str:
    """Extract first sentence from text."""
    if not text:
        return ""
    for i, char in enumerate(text):
        if char in ".!?" and (i + 1 >= len(text) or text[i + 1] in " \n"):
            return text[: i + 1]
    return text


def _path_to_root(docname: str) -> str:
    """Calculate relative path from document to docs root."""
    depth = docname.count("/")
    return "../" * depth


class RenderContext:
    """Context object passed to templates for path resolution."""

    def __init__(self, docname: str, doc_paths: dict[str, str] | None = None):
        """Initialize render context.

        Args:
            docname: Current document path (e.g., "users/personas/index")
            doc_paths: Mapping of doc types to paths (e.g., {"personas": "users/personas"})
        """
        self.docname = docname
        self.prefix = _path_to_root(docname)
        self._doc_paths = doc_paths or {}

    def doc_path(self, doc_type: str) -> str:
        """Get path for a documentation type."""
        path = self._doc_paths.get(doc_type, doc_type)
        return f"{self.prefix}{path}"

    def relative_uri(self, target_doc: str, anchor: str | None = None) -> str:
        """Build relative URI from current doc to target."""
        from_parts = self.docname.split("/")
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


class JinjaDocumentationRenderer:
    """Jinja2 implementation of DocumentationRenderingService.

    Renders entities to RST using Jinja2 templates with convention-based
    template discovery.
    """

    def __init__(
        self,
        template_dirs: list[Path],
        doc_paths: dict[str, str] | None = None,
    ):
        """Initialize with template directories.

        Args:
            template_dirs: List of directories to search for templates
            doc_paths: Mapping of doc types to paths for link generation
        """
        self._doc_paths = doc_paths or {}
        self._env = Environment(
            loader=FileSystemLoader([str(d) for d in template_dirs]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register common filters
        self._env.filters["snake_case"] = _to_snake_case
        self._env.filters["pluralize"] = _pluralize
        self._env.filters["title_case"] = _title_case
        self._env.filters["first_sentence"] = _first_sentence

    def render_index(
        self,
        entities: list[BaseModel],
        entity_type: str,
        docname: str,
        **options: Any,
    ) -> str:
        """Render a list of entities as an index view.

        Args:
            entities: List of entity instances to render
            entity_type: Entity type name (e.g., "persona", "epic")
            docname: Current document path for relative link calculation
            **options: Additional rendering options

        Returns:
            Rendered RST string
        """
        template_name = f"{entity_type}_index.rst.j2"
        return self._render(template_name, docname, entities=entities, **options)

    def render_entity(
        self,
        entity: BaseModel,
        entity_type: str,
        docname: str,
        view_type: str = "detail",
        **options: Any,
    ) -> str:
        """Render a single entity.

        Args:
            entity: Entity instance to render
            entity_type: Entity type name (e.g., "persona", "epic")
            docname: Current document path for relative link calculation
            view_type: View type (e.g., "detail", "summary")
            **options: Additional rendering options

        Returns:
            Rendered RST string
        """
        template_name = f"{entity_type}_{view_type}.rst.j2"
        return self._render(template_name, docname, entity=entity, **options)

    def _render(
        self,
        template_name: str,
        docname: str,
        **context: Any,
    ) -> str:
        """Render a template with context.

        Args:
            template_name: Template filename
            docname: Current document path
            **context: Template context variables

        Returns:
            Rendered string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        template = self._env.get_template(template_name)
        render_ctx = RenderContext(docname, self._doc_paths)

        return template.render(
            ctx=render_ctx,
            **context,
        )

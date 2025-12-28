"""Contrib module directives for sphinx_hcd.

Provides directives for contrib modules (reusable utilities):
- define-contrib: Define a contrib module with metadata
- contrib-index: Generate index of contrib modules
- contrib-list: Generate bullet list of contrib modules
"""

from docutils import nodes
from docutils.parsers.rst import directives

from apps.sphinx.shared import path_to_root
from julee.hcd.use_cases.crud import (
    CreateContribModuleRequest,
    GetContribModuleRequest,
    ListContribModulesRequest,
)

from .base import HCDDirective


class DefineContribPlaceholder(nodes.General, nodes.Element):
    """Placeholder for define-contrib, replaced at doctree-resolved."""

    pass


class ContribIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder for contrib-index, replaced at doctree-resolved."""

    pass


class ContribListPlaceholder(nodes.General, nodes.Element):
    """Placeholder for contrib-list, replaced at doctree-resolved."""

    pass


class DefineContribDirective(HCDDirective):
    """Define a contrib module with metadata.

    Usage::

        .. define-contrib:: polling
           :name: Polling Workflow
           :technology: Python, Temporal
           :path: src/julee/contrib/polling/

           A reusable workflow for long-running polling operations.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "name": directives.unchanged,
        "technology": directives.unchanged,
        "path": directives.unchanged,
    }

    def run(self):
        slug = self.arguments[0]
        docname = self.env.docname

        # Parse options
        name = self.options.get("name", "").strip()
        technology = self.options.get("technology", "").strip() or "Python"
        code_path = self.options.get("path", "").strip()
        description = "\n".join(self.content).strip()

        # Create contrib module via use case
        request = CreateContribModuleRequest(
            slug=slug,
            name=name,
            description=description,
            technology=technology,
            code_path=code_path,
            docname=docname,
            solution_slug=self.solution_slug,
        )
        self.hcd_context.create_contrib.execute_sync(request)

        # Return placeholder - rendering in doctree-resolved
        node = DefineContribPlaceholder()
        node["contrib_slug"] = slug
        return [node]


class ContribIndexDirective(HCDDirective):
    """Generate index of contrib modules.

    Usage::

        .. contrib-index::
    """

    def run(self):
        return [ContribIndexPlaceholder()]


class ContribListDirective(HCDDirective):
    """Generate bullet list of contrib modules.

    Usage::

        .. contrib-list::
    """

    def run(self):
        return [ContribListPlaceholder()]


def build_contrib_content(slug: str, docname: str, hcd_context):
    """Build content nodes for a contrib module page."""
    from sphinx.addnodes import seealso

    response = hcd_context.get_contrib.execute_sync(
        GetContribModuleRequest(slug=slug)
    )
    contrib = response.entity
    if not contrib:
        para = nodes.paragraph()
        para += nodes.problematic(text=f"Contrib module '{slug}' not found")
        return [para]

    result_nodes = []

    # Description - parse as RST for formatting support
    if contrib.description:
        from .base import parse_rst_content
        desc_nodes = parse_rst_content(contrib.description, f"<{slug}>")
        result_nodes.extend(desc_nodes)

    # Seealso with metadata
    seealso_node = seealso()

    # Technology
    if contrib.technology:
        tech_para = nodes.paragraph()
        tech_para += nodes.strong(text="Technology: ")
        tech_para += nodes.Text(contrib.technology)
        seealso_node += tech_para

    # Code path
    if contrib.code_path:
        path_para = nodes.paragraph()
        path_para += nodes.strong(text="Code: ")
        path_para += nodes.literal(text=contrib.code_path)
        seealso_node += path_para

    result_nodes.append(seealso_node)
    return result_nodes


def build_contrib_index(docname: str, hcd_context):
    """Build contrib module index."""
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    all_contribs = hcd_context.list_contribs.execute_sync(
        ListContribModulesRequest(solution_slug=solution)
    ).entities

    if not all_contribs:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No contrib modules defined")
        return [para]

    result_nodes = []

    # Contrib list
    contrib_list = nodes.bullet_list()

    for contrib in sorted(all_contribs, key=lambda c: c.slug):
        item = nodes.list_item()
        para = nodes.paragraph()

        # Link to contrib
        contrib_path = f"{contrib.slug}.html"
        ref = nodes.reference("", "", refuri=contrib_path)
        ref += nodes.Text(contrib.display_title)
        para += ref

        if contrib.description:
            first_sentence = contrib.description.split(".")[0]
            para += nodes.Text(f" - {first_sentence}")

        item += para
        contrib_list += item

    result_nodes.append(contrib_list)

    return result_nodes


def build_contrib_list(docname: str, hcd_context):
    """Build simple bullet list of contrib modules."""
    from ..config import get_config

    config = get_config()
    solution = config.solution_slug
    prefix = path_to_root(docname)
    all_contribs = hcd_context.list_contribs.execute_sync(
        ListContribModulesRequest(solution_slug=solution)
    ).entities

    if not all_contribs:
        para = nodes.paragraph()
        para += nodes.emphasis(text="No contrib modules defined")
        return [para]

    bullet_list = nodes.bullet_list()

    for contrib in sorted(all_contribs, key=lambda c: c.slug):
        item = nodes.list_item()
        item_para = nodes.paragraph()

        # Link to contrib doc
        if contrib.docname:
            ref = nodes.reference("", "", refuri=f"{prefix}{contrib.docname}.html")
            ref += nodes.Text(contrib.display_title)
            item_para += ref
        else:
            item_para += nodes.Text(contrib.display_title)

        # Description
        if contrib.description:
            first_sentence = contrib.description.split(".")[0]
            item_para += nodes.Text(f" - {first_sentence}")

        item += item_para
        bullet_list += item

    return [bullet_list]


# NOTE: process_contrib_placeholders removed - now handled by
# infrastructure/handlers/placeholder_resolution.py via ContribPlaceholderHandler

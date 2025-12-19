"""Component directive for C4 Sphinx integration.

Provides the define-component directive.
"""

from docutils import nodes
from docutils.parsers.rst import directives

from ...domain.models.component import Component
from .base import C4Directive


class DefineComponentDirective(C4Directive):
    """Define a component within a container.

    Usage::

        .. define-component:: auth-controller
           :name: Authentication Controller
           :container: api-app
           :system: banking-system
           :technology: Python
           :interface: REST API

           Handles user authentication and authorization.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "name": directives.unchanged_required,
        "container": directives.unchanged_required,
        "system": directives.unchanged_required,
        "technology": directives.unchanged,
        "interface": directives.unchanged,
        "code-path": directives.unchanged,
        "url": directives.unchanged,
        "tags": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        slug = self.arguments[0]
        name = self.options.get("name", slug.replace("-", " ").title())
        container_slug = self.options.get("container", "")
        system_slug = self.options.get("system", "")
        technology = self.options.get("technology", "")
        interface = self.options.get("interface", "")
        code_path = self.options.get("code-path", "")
        url = self.options.get("url", "")
        tags_str = self.options.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        description = "\n".join(self.content).strip()

        # Create component
        component = Component(
            slug=slug,
            name=name,
            container_slug=container_slug,
            system_slug=system_slug,
            description=description,
            technology=technology,
            interface=interface,
            code_path=code_path,
            url=url,
            tags=tags,
            docname=self.docname,
        )

        # Store in environment
        storage = self.get_c4_storage()
        storage["components"][slug] = component

        # Build output nodes
        result_nodes = []

        # Title
        section = nodes.section(ids=[slug])
        section += nodes.title(text=name)

        # Description
        if description:
            section += self.make_paragraph(description)

        # Metadata
        section += self.make_field("Container", container_slug)
        section += self.make_field("System", system_slug)
        if technology:
            section += self.make_field("Technology", technology)
        if interface:
            section += self.make_field("Interface", interface)
        if code_path:
            section += self.make_field("Code", code_path)
        if tags:
            section += self.make_field("Tags", ", ".join(tags))

        result_nodes.append(section)
        return result_nodes

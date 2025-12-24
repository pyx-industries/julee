"""Container directive for C4 Sphinx integration.

Provides the define-container directive.
"""

from docutils import nodes
from docutils.parsers.rst import directives

from julee.c4.domain.models.container import Container, ContainerType
from .base import C4Directive


class DefineContainerDirective(C4Directive):
    """Define a container within a software system.

    Usage::

        .. define-container:: api-app
           :name: API Application
           :system: banking-system
           :type: web_application
           :technology: FastAPI, Python 3.11

           Provides banking functionality via REST API.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "name": directives.unchanged_required,
        "system": directives.unchanged_required,
        "type": directives.unchanged,
        "technology": directives.unchanged,
        "url": directives.unchanged,
        "tags": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        slug = self.arguments[0]
        name = self.options.get("name", slug.replace("-", " ").title())
        system_slug = self.options.get("system", "")
        container_type = self.options.get("type", "other")
        technology = self.options.get("technology", "")
        url = self.options.get("url", "")
        tags_str = self.options.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        description = "\n".join(self.content).strip()

        # Create container
        container = Container(
            slug=slug,
            name=name,
            system_slug=system_slug,
            description=description,
            container_type=ContainerType(container_type),
            technology=technology,
            url=url,
            tags=tags,
            docname=self.docname,
        )

        # Store in environment
        storage = self.get_c4_storage()
        storage["containers"][slug] = container

        # Build output nodes
        result_nodes = []

        # Title
        section = nodes.section(ids=[slug])
        section += nodes.title(text=name)

        # Description
        if description:
            section += self.make_paragraph(description)

        # Metadata
        section += self.make_field("System", system_slug)
        if container_type != "other":
            section += self.make_field("Type", container_type)
        if technology:
            section += self.make_field("Technology", technology)
        if tags:
            section += self.make_field("Tags", ", ".join(tags))

        result_nodes.append(section)
        return result_nodes

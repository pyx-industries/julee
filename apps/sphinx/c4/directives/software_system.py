"""Software System directive for C4 Sphinx integration.

Provides the define-software-system directive.
"""

from docutils import nodes
from docutils.parsers.rst import directives

from julee.c4.entities.software_system import SoftwareSystem, SystemType

from .base import C4Directive


class DefineSoftwareSystemDirective(C4Directive):
    """Define a software system in the C4 model.

    Usage::

        .. define-software-system:: banking-system
           :name: Internet Banking System
           :type: internal
           :owner: Digital Team
           :technology: Java, Spring Boot

           Allows customers to view balances and make payments.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "name": directives.unchanged_required,
        "type": directives.unchanged,
        "owner": directives.unchanged,
        "technology": directives.unchanged,
        "url": directives.unchanged,
        "tags": directives.unchanged,
        "hidden": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        slug = self.arguments[0]
        name = self.options.get("name", slug.replace("-", " ").title())
        system_type = self.options.get("type", "internal")
        owner = self.options.get("owner", "")
        technology = self.options.get("technology", "")
        url = self.options.get("url", "")
        tags_str = self.options.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        description = "\n".join(self.content).strip()
        hidden = "hidden" in self.options

        # Create software system
        software_system = SoftwareSystem(
            slug=slug,
            name=name,
            description=description,
            system_type=SystemType(system_type),
            owner=owner,
            technology=technology,
            url=url,
            tags=tags,
            docname=self.docname,
        )

        # Store in environment
        storage = self.get_c4_storage()
        storage["software_systems"][slug] = software_system

        # If hidden, return empty (just register, no output)
        if hidden:
            return []

        # Build output nodes
        result_nodes = []

        # Title
        section = nodes.section(ids=[slug])
        section += nodes.title(text=name)

        # Description
        if description:
            section += self.make_paragraph(description)

        # Metadata
        if system_type:
            section += self.make_field("Type", system_type)
        if owner:
            section += self.make_field("Owner", owner)
        if technology:
            section += self.make_field("Technology", technology)
        if tags:
            section += self.make_field("Tags", ", ".join(tags))

        result_nodes.append(section)
        return result_nodes

"""Deployment Node directive for C4 Sphinx integration.

Provides the define-deployment-node directive.
"""

from docutils import nodes
from docutils.parsers.rst import directives

from julee.c4.entities.deployment_node import (
    ContainerInstance,
    DeploymentNode,
    NodeType,
)

from .base import C4Directive


class DefineDeploymentNodeDirective(C4Directive):
    """Define a deployment node in the C4 model.

    Usage::

        .. define-deployment-node:: web-server-1
           :name: Web Server 1
           :environment: production
           :type: server
           :technology: Ubuntu 22.04, Docker
           :parent: aws-region-east
           :containers: api-app, web-app

           Primary web server hosting the API and web application.
    """

    required_arguments = 1
    has_content = True
    option_spec = {
        "name": directives.unchanged_required,
        "environment": directives.unchanged,
        "type": directives.unchanged,
        "technology": directives.unchanged,
        "parent": directives.unchanged,
        "containers": directives.unchanged,
        "tags": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        slug = self.arguments[0]
        name = self.options.get("name", slug.replace("-", " ").title())
        environment = self.options.get("environment", "production")
        node_type = self.options.get("type", "other")
        technology = self.options.get("technology", "")
        parent_slug = self.options.get("parent", "") or None
        containers_str = self.options.get("containers", "")
        tags_str = self.options.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        description = "\n".join(self.content).strip()

        # Parse container instances
        container_instances = []
        if containers_str:
            for container_ref in containers_str.split(","):
                container_slug = container_ref.strip()
                if container_slug:
                    container_instances.append(
                        ContainerInstance(
                            container_slug=container_slug,
                            instance_id="1",
                        )
                    )

        # Create deployment node
        deployment_node = DeploymentNode(
            slug=slug,
            name=name,
            environment=environment,
            node_type=NodeType(node_type),
            technology=technology,
            parent_slug=parent_slug,
            container_instances=container_instances,
            description=description,
            tags=tags,
            docname=self.docname,
        )

        # Store in environment
        storage = self.get_c4_storage()
        storage["deployment_nodes"][slug] = deployment_node

        # Build output nodes
        result_nodes = []

        # Title
        section = nodes.section(ids=[slug])
        section += nodes.title(text=name)

        # Description
        if description:
            section += self.make_paragraph(description)

        # Metadata
        section += self.make_field("Environment", environment)
        if node_type != "other":
            section += self.make_field("Type", node_type)
        if technology:
            section += self.make_field("Technology", technology)
        if parent_slug:
            section += self.make_field("Parent", parent_slug)
        if container_instances:
            cont_names = ", ".join(ci.container_slug for ci in container_instances)
            section += self.make_field("Containers", cont_names)
        if tags:
            section += self.make_field("Tags", ", ".join(tags))

        result_nodes.append(section)
        return result_nodes

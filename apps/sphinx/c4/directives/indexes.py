"""C4 index directives for listing defined elements.

Provides directives for listing C4 elements defined via define-* directives:
- software-system-index: List all software systems
- container-index: List all containers
- component-index: List all components
- relationship-index: List all relationships
- deployment-node-index: List all deployment nodes
"""

from docutils import nodes

from .base import C4Directive


class SoftwareSystemIndexDirective(C4Directive):
    """List all defined software systems.

    Usage::

        .. software-system-index::

    Renders a bullet list of all software systems with their descriptions.
    """

    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        storage = self.get_c4_storage()
        systems = storage.get("software_systems", {})

        if not systems:
            return self.empty_result("No software systems defined.")

        result_list = nodes.bullet_list()

        for slug in sorted(systems.keys()):
            system = systems[slug]
            item = nodes.list_item()
            para = nodes.paragraph()

            # System name as strong text with link to definition
            ref = nodes.reference("", "", refuri=f"#{slug}")
            ref += nodes.strong(text=system.name)
            para += ref

            # Type badge
            if system.system_type:
                para += nodes.Text(f" [{system.system_type.value}]")

            # Description
            if system.description:
                para += nodes.Text(f" — {system.description[:80]}")
                if len(system.description) > 80:
                    para += nodes.Text("...")

            item += para
            result_list += item

        return [result_list]


class ContainerIndexDirective(C4Directive):
    """List all defined containers.

    Usage::

        .. container-index::

    Renders a bullet list of all containers grouped by parent system.
    """

    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        storage = self.get_c4_storage()
        containers = storage.get("containers", {})

        if not containers:
            return self.empty_result("No containers defined.")

        # Group by parent system
        by_system: dict[str, list] = {}
        for slug, container in containers.items():
            parent = container.parent_system or "unassigned"
            if parent not in by_system:
                by_system[parent] = []
            by_system[parent].append((slug, container))

        result_nodes = []

        for system_slug in sorted(by_system.keys()):
            system_containers = by_system[system_slug]

            # System heading
            heading = nodes.paragraph()
            heading += nodes.strong(text=system_slug.replace("-", " ").title())
            result_nodes.append(heading)

            # Container list
            container_list = nodes.bullet_list()

            for slug, container in sorted(system_containers, key=lambda x: x[0]):
                item = nodes.list_item()
                para = nodes.paragraph()

                # Container name with link
                ref = nodes.reference("", "", refuri=f"#{slug}")
                ref += nodes.Text(container.name)
                para += ref

                # Technology
                if container.technology:
                    para += nodes.Text(f" [{container.technology}]")

                # Description
                if container.description:
                    para += nodes.Text(f" — {container.description[:60]}")
                    if len(container.description) > 60:
                        para += nodes.Text("...")

                item += para
                container_list += item

            result_nodes.append(container_list)

        return result_nodes


class ComponentIndexDirective(C4Directive):
    """List all defined components.

    Usage::

        .. component-index::

    Renders a bullet list of all components grouped by parent container.
    """

    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        storage = self.get_c4_storage()
        components = storage.get("components", {})

        if not components:
            return self.empty_result("No components defined.")

        # Group by parent container
        by_container: dict[str, list] = {}
        for slug, component in components.items():
            parent = component.parent_container or "unassigned"
            if parent not in by_container:
                by_container[parent] = []
            by_container[parent].append((slug, component))

        result_nodes = []

        for container_slug in sorted(by_container.keys()):
            container_components = by_container[container_slug]

            # Container heading
            heading = nodes.paragraph()
            heading += nodes.strong(text=container_slug.replace("-", " ").title())
            result_nodes.append(heading)

            # Component list
            component_list = nodes.bullet_list()

            for slug, component in sorted(container_components, key=lambda x: x[0]):
                item = nodes.list_item()
                para = nodes.paragraph()

                # Component name with link
                ref = nodes.reference("", "", refuri=f"#{slug}")
                ref += nodes.Text(component.name)
                para += ref

                # Technology
                if component.technology:
                    para += nodes.Text(f" [{component.technology}]")

                # Description
                if component.description:
                    para += nodes.Text(f" — {component.description[:60]}")
                    if len(component.description) > 60:
                        para += nodes.Text("...")

                item += para
                component_list += item

            result_nodes.append(component_list)

        return result_nodes


class RelationshipIndexDirective(C4Directive):
    """List all defined relationships.

    Usage::

        .. relationship-index::

    Renders a table of all relationships between C4 elements.
    """

    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        storage = self.get_c4_storage()
        relationships = storage.get("relationships", {})

        if not relationships:
            return self.empty_result("No relationships defined.")

        # Create a simple bullet list of relationships
        result_list = nodes.bullet_list()

        for rel_id in sorted(relationships.keys()):
            rel = relationships[rel_id]
            item = nodes.list_item()
            para = nodes.paragraph()

            # Format: source -> destination [description]
            para += nodes.literal(text=rel.source_slug)
            para += nodes.Text(" → ")
            para += nodes.literal(text=rel.destination_slug)

            if rel.description:
                para += nodes.Text(f" — {rel.description}")

            if rel.technology:
                para += nodes.Text(f" [{rel.technology}]")

            item += para
            result_list += item

        return [result_list]


class DeploymentNodeIndexDirective(C4Directive):
    """List all defined deployment nodes.

    Usage::

        .. deployment-node-index::

    Renders a hierarchical list of deployment nodes.
    """

    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        storage = self.get_c4_storage()
        nodes_dict = storage.get("deployment_nodes", {})

        if not nodes_dict:
            return self.empty_result("No deployment nodes defined.")

        # Group by parent (for hierarchy)
        by_parent: dict[str, list] = {"": []}  # Root nodes have empty parent
        for slug, node in nodes_dict.items():
            parent = node.parent or ""
            if parent not in by_parent:
                by_parent[parent] = []
            by_parent[parent].append((slug, node))

        # Build hierarchical list starting from root
        def build_node_list(parent_slug: str) -> nodes.bullet_list:
            node_list = nodes.bullet_list()
            children = by_parent.get(parent_slug, [])

            for slug, deployment_node in sorted(children, key=lambda x: x[0]):
                item = nodes.list_item()
                para = nodes.paragraph()

                # Node name with link
                ref = nodes.reference("", "", refuri=f"#{slug}")
                ref += nodes.strong(text=deployment_node.name)
                para += ref

                # Type/technology
                if deployment_node.technology:
                    para += nodes.Text(f" [{deployment_node.technology}]")

                # Description
                if deployment_node.description:
                    para += nodes.Text(f" — {deployment_node.description[:50]}")
                    if len(deployment_node.description) > 50:
                        para += nodes.Text("...")

                item += para

                # Add children recursively
                if slug in by_parent:
                    item += build_node_list(slug)

                node_list += item

            return node_list

        return [build_node_list("")]

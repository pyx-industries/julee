"""Entity relationship graph directive.

Renders a visual graph of HCD entity semantic relations using Mermaid.
"""

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.shared.services.relation_traversal import get_relation_traversal


class EntityGraphDirective(SphinxDirective):
    """Render the HCD entity relationship graph.

    Shows how HCD entities relate via semantic relations:
    - PROJECTS: Viewpoint → Core (solid arrow)
    - PART_OF: Contained → Container (dotted arrow)
    - CONTAINS: Container → Contained (solid arrow)
    - REFERENCES: Source → Target (dashed arrow)

    Usage::

        .. entity-graph::

    Options::

        :format: mermaid (default) or table
        :show-inverse: Include inverse relations (default: false)
    """

    has_content = False
    option_spec = {
        "format": lambda x: x.lower() if x else "mermaid",
        "show-inverse": lambda x: x.lower() in ("true", "yes", "1"),
    }

    def run(self) -> list[nodes.Node]:
        """Generate the entity graph."""
        fmt = self.options.get("format", "mermaid")
        traversal = get_relation_traversal()
        graph = traversal.build_entity_graph()

        if fmt == "table":
            return self._render_table(graph)
        return self._render_mermaid(graph)

    def _render_mermaid(self, graph: dict) -> list[nodes.Node]:
        """Render graph as Mermaid diagram."""
        lines = [
            "```mermaid",
            "graph LR",
            "    %% HCD Entity Relationship Graph",
            "    %% Generated from semantic relations",
            "",
            "    %% Style definitions",
            "    classDef core fill:#e1f5fe,stroke:#01579b",
            "    classDef hcd fill:#f3e5f5,stroke:#7b1fa2",
            "    classDef viewpoint fill:#e8f5e9,stroke:#2e7d32",
            "",
        ]

        # Add nodes with styling
        node_styles = {
            "BoundedContext": "core",
            "Application": "core",
            "Story": "hcd",
            "Epic": "hcd",
            "Journey": "hcd",
            "Persona": "hcd",
            "App": "viewpoint",
            "Accelerator": "viewpoint",
        }

        for node in graph["nodes"]:
            node_id = node["id"]
            style = node_styles.get(node_id, "hcd")
            lines.append(f"    {node_id}[{node_id}]:::{style}")

        lines.append("")

        # Add edges with different arrow styles per relation type
        arrow_styles = {
            "projects": "-->",      # solid arrow
            "part_of": "-.->",      # dotted arrow
            "contains": "==>",      # thick arrow
            "references": "-->",    # dashed with label
        }

        for edge in graph["edges"]:
            source = edge["source"]
            target = edge["target"]
            relation = edge["relation"]
            arrow = arrow_styles.get(relation, "-->")

            if relation == "references":
                lines.append(f"    {source} -.->|{relation}| {target}")
            elif relation == "part_of":
                lines.append(f"    {source} -.->|{relation}| {target}")
            else:
                lines.append(f"    {source} {arrow}|{relation}| {target}")

        lines.append("```")

        # Create a raw node with the mermaid content
        mermaid_content = "\n".join(lines)

        # Use sphinxcontrib-mermaid directive format
        mermaid_node = nodes.container()
        mermaid_node["classes"].append("mermaid")

        # Parse as RST with mermaid directive
        from apps.sphinx.directive_factory import parse_rst_to_nodes

        rst_content = f"""
.. mermaid::

    graph LR
        %% HCD Entity Relationship Graph
        %% Generated from semantic relations

        %% Style definitions
        classDef core fill:#e1f5fe,stroke:#01579b
        classDef hcd fill:#f3e5f5,stroke:#7b1fa2
        classDef viewpoint fill:#e8f5e9,stroke:#2e7d32

"""
        # Add nodes
        for node in graph["nodes"]:
            node_id = node["id"]
            style = node_styles.get(node_id, "hcd")
            rst_content += f"        {node_id}[{node_id}]:::{style}\n"

        rst_content += "\n"

        # Add edges
        for edge in graph["edges"]:
            source = edge["source"]
            target = edge["target"]
            relation = edge["relation"]

            if relation == "projects":
                rst_content += f"        {source} -->|projects| {target}\n"
            elif relation == "part_of":
                rst_content += f"        {source} -.->|part_of| {target}\n"
            elif relation == "contains":
                rst_content += f"        {source} ==>|contains| {target}\n"
            elif relation == "references":
                rst_content += f"        {source} -.->|references| {target}\n"
            else:
                rst_content += f"        {source} -->|{relation}| {target}\n"

        return parse_rst_to_nodes(rst_content, self.env.docname)

    def _render_table(self, graph: dict) -> list[nodes.Node]:
        """Render graph as RST table."""
        from apps.sphinx.directive_factory import parse_rst_to_nodes

        rst_lines = [
            "**Entity Relationships**",
            "",
            ".. list-table::",
            "   :header-rows: 1",
            "   :widths: 25 25 25 25",
            "",
            "   * - Source",
            "     - Relation",
            "     - Target",
            "     - Description",
        ]

        relation_descriptions = {
            "projects": "Viewpoint entity projects Core entity",
            "part_of": "Entity is contained within another",
            "contains": "Entity aggregates others",
            "references": "Non-owning reference",
        }

        for edge in sorted(graph["edges"], key=lambda e: (e["source"], e["relation"])):
            desc = relation_descriptions.get(edge["relation"], "")
            rst_lines.extend([
                f"   * - {edge['source']}",
                f"     - {edge['relation']}",
                f"     - {edge['target']}",
                f"     - {desc}",
            ])

        rst_content = "\n".join(rst_lines)
        return parse_rst_to_nodes(rst_content, self.env.docname)


def setup(app):
    """Register the directive."""
    app.add_directive("entity-graph", EntityGraphDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

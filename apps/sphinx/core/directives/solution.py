"""Solution structure directives for architecture documentation.

Renders live solution structure by calling use cases via CoreContext.
Directives are thin presentation wrappers - all logic is in use cases.
"""

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from apps.sphinx.core.context import get_core_context


class SolutionOverviewDirective(SphinxDirective):
    """Show solution name and description.

    Usage::

        .. solution-overview:: julee

    Or for the root solution (no argument)::

        .. solution-overview::

    Takes an optional solution slug to identify which solution to describe.
    """

    required_arguments = 0
    optional_arguments = 1
    has_content = False
    final_argument_whitespace = True

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        context = get_core_context(self.env.app)

        # Determine solution name from argument or default
        if self.arguments:
            solution_slug = self.arguments[0]
        else:
            solution_slug = "julee"

        # Build output - for now just show the slug
        # A GetSolutionUseCase could be added later for richer data
        result = []
        para = nodes.paragraph()
        para += nodes.strong(text=solution_slug.replace("_", " ").replace("-", " ").title())
        result.append(para)

        return result


class BoundedContextListDirective(SphinxDirective):
    """List bounded contexts discovered in the solution.

    Usage::

        .. bounded-context-list::
           :show-description:

    Options:
        :show-description: Include 1-line description from __init__.py docstring
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    option_spec = {
        "show-description": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        context = get_core_context(self.env.app)
        show_description = "show-description" in self.options

        # Call use case via context
        bounded_contexts = context.list_solution_bounded_contexts()

        if not bounded_contexts:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No bounded contexts found.")
            return [para]

        # Build definition list
        dl = nodes.definition_list()

        for bc in bounded_contexts:
            item = nodes.definition_list_item()

            # Term: BC name
            term = nodes.term()
            term += nodes.strong(text=bc.display_name)
            if bc.is_viewpoint:
                term += nodes.Text(" [viewpoint]")
            if bc.is_contrib:
                term += nodes.Text(" [contrib]")
            item += term

            # Definition
            definition = nodes.definition()

            # Description first if available
            if show_description and bc.description:
                desc_para = nodes.paragraph()
                desc_para += nodes.Text(bc.description)
                definition += desc_para

            # Path
            path_para = nodes.paragraph()
            path_para += nodes.emphasis(text="Path: ")
            path_para += nodes.literal(text=bc.path)
            definition += path_para

            item += definition
            dl += item

        return [dl]


class ApplicationListDirective(SphinxDirective):
    """List applications discovered in the solution.

    Usage::

        .. application-list::
           :show-description:

    Options:
        :show-description: Include 1-line description from __init__.py docstring
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    option_spec = {
        "show-description": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        context = get_core_context(self.env.app)
        show_description = "show-description" in self.options

        # Call use case via context
        applications = context.list_applications()

        if not applications:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No applications found.")
            return [para]

        # Build definition list
        dl = nodes.definition_list()

        for app in applications:
            item = nodes.definition_list_item()

            # Term: App name with type
            term = nodes.term()
            term += nodes.strong(text=app.slug)
            term += nodes.Text(f" [{app.app_type.value}]")
            item += term

            # Definition
            definition = nodes.definition()

            # Description first if available
            if show_description and app.description:
                desc_para = nodes.paragraph()
                desc_para += nodes.Text(app.description)
                definition += desc_para

            # Path
            path_para = nodes.paragraph()
            path_para += nodes.emphasis(text="Path: ")
            path_para += nodes.literal(text=app.path)
            definition += path_para

            item += definition
            dl += item

        return [dl]


class DeploymentListDirective(SphinxDirective):
    """List deployments discovered in the solution.

    Usage::

        .. deployment-list::

    Shows links to deployment configurations.
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        context = get_core_context(self.env.app)

        # Call use case via context
        deployments = context.list_deployments()

        if not deployments:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No deployments configured.")
            return [para]

        # Build bullet list
        ul = nodes.bullet_list()

        for dep in deployments:
            item = nodes.list_item()
            para = nodes.paragraph()
            para += nodes.strong(text=dep.slug)
            para += nodes.Text(f" [{dep.deployment_type.value}]")
            if dep.description:
                para += nodes.Text(f" — {dep.description}")
            item += para
            ul += item

        return [ul]


class NestedSolutionListDirective(SphinxDirective):
    """List nested solutions (e.g., contrib modules).

    Usage::

        .. nested-solution-list::

    Shows nested solutions identified by containing bounded contexts.
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        context = get_core_context(self.env.app)

        # Filter BCs to find contrib ones (as proxy for nested solutions)
        all_bcs = context.list_solution_bounded_contexts()
        contrib_bcs = [bc for bc in all_bcs if bc.is_contrib]

        if not contrib_bcs:
            para = nodes.paragraph()
            para += nodes.emphasis(text="No nested solutions found.")
            return [para]

        # Group by parent directory (nested solution)
        nested: dict[str, list] = {}
        for bc in contrib_bcs:
            # Extract parent from path (e.g., src/julee/contrib/ceap -> contrib)
            parts = Path(bc.path).parts
            if "contrib" in parts:
                contrib_idx = parts.index("contrib")
                if contrib_idx + 1 < len(parts):
                    parent = parts[contrib_idx]
                else:
                    parent = "contrib"
            else:
                parent = "contrib"

            if parent not in nested:
                nested[parent] = []
            nested[parent].append(bc)

        # Build definition list
        dl = nodes.definition_list()

        for parent, bcs in sorted(nested.items()):
            item = nodes.definition_list_item()

            term = nodes.term()
            term += nodes.strong(text=parent.title())
            item += term

            definition = nodes.definition()
            bc_para = nodes.paragraph()
            bc_para += nodes.Text(f"Contains {len(bcs)} bounded context(s): ")
            bc_para += nodes.Text(", ".join(bc.slug for bc in bcs))
            definition += bc_para

            item += definition
            dl += item

        return [dl]


class ViewpointLinksDirective(SphinxDirective):
    """Show links to viewpoint bounded contexts (HCD, C4).

    Usage::

        .. viewpoint-links::

    Shows links to HCD and C4 viewpoints if they exist.
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        context = get_core_context(self.env.app)

        # Filter BCs to find viewpoints
        all_bcs = context.list_solution_bounded_contexts()
        viewpoints = [bc for bc in all_bcs if bc.is_viewpoint]

        if not viewpoints:
            return []

        # Build bullet list with doc references
        ul = nodes.bullet_list()

        for vp in sorted(viewpoints, key=lambda x: x.slug):
            item = nodes.list_item()
            para = nodes.paragraph()

            # Create reference to the viewpoint's API page
            ref = nodes.reference("", "", internal=True)
            ref["refuri"] = f"_generated/julee.{vp.slug}.html"
            ref += nodes.strong(text=vp.slug.upper())
            para += ref

            if vp.description:
                para += nodes.Text(f" — {vp.description}")

            item += para
            ul += item

        return [ul]


class SolutionStructureDirective(SphinxDirective):
    """Render live solution structure from filesystem introspection.

    Usage::

        .. solution-structure::
           :root: src/julee
           :depth: 3
           :show-files:

    Options:
        :root: Root directory to display (default: src)
        :depth: Maximum depth to traverse (default: 2)
        :show-files: Include Python files, not just directories
        :include-contrib: Include contrib directory
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    option_spec = {
        "root": directives.unchanged,
        "depth": directives.positive_int,
        "show-files": directives.flag,
        "include-contrib": directives.flag,
    }

    SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", "node_modules", ".venv", "venv"}

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        root = self.options.get("root", "src")
        depth = self.options.get("depth", 2)
        show_files = "show-files" in self.options
        include_contrib = "include-contrib" in self.options

        srcdir = Path(self.env.srcdir).parent
        root_path = srcdir / root

        if not root_path.exists():
            error = self.state_machine.reporter.error(
                f"Root path '{root}' does not exist",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        tree_lines = self._build_tree(
            root_path,
            prefix="",
            depth=depth,
            show_files=show_files,
            include_contrib=include_contrib,
            current_depth=0,
        )

        tree_text = "\n".join(tree_lines)
        literal = nodes.literal_block(tree_text, tree_text)
        literal["language"] = "text"

        return [literal]

    def _build_tree(
        self,
        path: Path,
        prefix: str,
        depth: int,
        show_files: bool,
        include_contrib: bool,
        current_depth: int,
    ) -> list[str]:
        """Build tree representation of directory structure."""
        if current_depth > depth:
            return []

        lines = []

        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return []

        filtered = []
        for entry in entries:
            if entry.name in self.SKIP_DIRS:
                continue
            if entry.name.startswith("."):
                continue
            if not include_contrib and entry.name == "contrib":
                continue
            if entry.is_file() and not show_files:
                continue
            if entry.is_file() and not entry.name.endswith(".py"):
                continue
            if entry.is_file() and entry.name == "__init__.py":
                continue
            filtered.append(entry)

        for i, entry in enumerate(filtered):
            is_last = i == len(filtered) - 1
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                name = f"{entry.name}/"
                marker = self._get_bc_marker(entry)
                if marker:
                    name += f"  # {marker}"
            else:
                name = entry.name

            lines.append(f"{prefix}{connector}{name}")

            if entry.is_dir() and current_depth < depth:
                child_lines = self._build_tree(
                    entry,
                    prefix + child_prefix,
                    depth,
                    show_files,
                    include_contrib,
                    current_depth + 1,
                )
                lines.extend(child_lines)

        return lines

    def _get_bc_marker(self, path: Path) -> str | None:
        """Check if a directory is a bounded context and return marker."""
        if not path.is_dir():
            return None

        has_entities = (path / "entities").is_dir()
        has_use_cases = (path / "use_cases").is_dir()

        if has_entities and has_use_cases:
            return "bounded context"
        if has_entities:
            return "domain"

        return None

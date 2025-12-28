"""Solution structure directives for architecture documentation.

Renders live solution structure from code introspection rather than
maintaining static documentation.
"""

import importlib
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


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

    # Directories to skip
    SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", "node_modules", ".venv", "venv"}

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        root = self.options.get("root", "src")
        depth = self.options.get("depth", 2)
        show_files = "show-files" in self.options
        include_contrib = "include-contrib" in self.options

        # Get the source directory from Sphinx config
        srcdir = Path(self.env.srcdir).parent  # docs -> project root

        root_path = srcdir / root
        if not root_path.exists():
            error = self.state_machine.reporter.error(
                f"Root path '{root}' does not exist",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        # Build tree structure
        tree_lines = self._build_tree(
            root_path,
            prefix="",
            depth=depth,
            show_files=show_files,
            include_contrib=include_contrib,
            current_depth=0,
        )

        # Render as literal block (preserves formatting)
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
        """Build tree representation of directory structure.

        Args:
            path: Current directory path
            prefix: Line prefix for tree drawing
            depth: Maximum depth to traverse
            show_files: Whether to include files
            include_contrib: Whether to include contrib directory
            current_depth: Current traversal depth

        Returns:
            List of formatted tree lines
        """
        if current_depth > depth:
            return []

        lines = []

        # Get and sort entries
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        except PermissionError:
            return []

        # Filter entries
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

            # Format entry name
            if entry.is_dir():
                name = f"{entry.name}/"
                # Check for special markers
                marker = self._get_bc_marker(entry)
                if marker:
                    name += f"  # {marker}"
            else:
                name = entry.name

            lines.append(f"{prefix}{connector}{name}")

            # Recurse into directories
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
        """Check if a directory is a bounded context and return marker.

        A directory is a bounded context if it has:
        - entities/ subdirectory
        - use_cases/ subdirectory
        - repositories/ subdirectory
        """
        if not path.is_dir():
            return None

        has_entities = (path / "entities").is_dir()
        has_use_cases = (path / "use_cases").is_dir()
        has_repos = (path / "repositories").is_dir()

        if has_entities and has_use_cases:
            return "bounded context"
        if has_entities:
            return "domain"

        return None


class BoundedContextListDirective(SphinxDirective):
    """List bounded contexts discovered in the solution.

    Usage::

        .. bounded-context-list::
           :root: src/julee
           :show-entities:

    Options:
        :root: Root directory to search (default: src)
        :show-entities: Include entity counts
        :show-use-cases: Include use case counts
    """

    required_arguments = 0
    optional_arguments = 0
    has_content = False

    option_spec = {
        "root": directives.unchanged,
        "show-entities": directives.flag,
        "show-use-cases": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Execute the directive."""
        root = self.options.get("root", "src")
        srcdir = Path(self.env.srcdir).parent
        root_path = srcdir / root

        if not root_path.exists():
            error = self.state_machine.reporter.error(
                f"Root path '{root}' does not exist",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error]

        # Find bounded contexts
        bcs = self._find_bounded_contexts(root_path)

        if not bcs:
            para = nodes.paragraph(text="No bounded contexts found")
            return [para]

        # Build definition list
        dl = nodes.definition_list()

        for bc_path, bc_info in sorted(bcs.items()):
            item = nodes.definition_list_item()

            # Term: BC name
            term = nodes.term()
            term += nodes.strong(text=bc_info["name"])
            item += term

            # Definition: path and counts
            definition = nodes.definition()

            path_para = nodes.paragraph()
            path_para += nodes.emphasis(text="Path: ")
            path_para += nodes.literal(text=str(bc_path.relative_to(srcdir)))
            definition += path_para

            if "show-entities" in self.options and bc_info["entity_count"] > 0:
                entity_para = nodes.paragraph()
                entity_para += nodes.Text(f"Entities: {bc_info['entity_count']}")
                definition += entity_para

            if "show-use-cases" in self.options and bc_info["use_case_count"] > 0:
                uc_para = nodes.paragraph()
                uc_para += nodes.Text(f"Use Cases: {bc_info['use_case_count']}")
                definition += uc_para

            item += definition
            dl += item

        return [dl]

    def _find_bounded_contexts(self, root: Path) -> dict[Path, dict]:
        """Recursively find bounded contexts.

        Returns:
            Dict mapping path to BC info dict
        """
        bcs = {}

        for path in root.rglob("*"):
            if not path.is_dir():
                continue
            if any(skip in path.parts for skip in ("__pycache__", ".git", "venv")):
                continue

            # Check for BC markers
            has_entities = (path / "entities").is_dir()
            has_use_cases = (path / "use_cases").is_dir()

            if has_entities and has_use_cases:
                entity_count = self._count_python_files(path / "entities")
                use_case_count = self._count_python_files(path / "use_cases")

                bcs[path] = {
                    "name": path.name,
                    "entity_count": entity_count,
                    "use_case_count": use_case_count,
                }

        return bcs

    def _count_python_files(self, path: Path) -> int:
        """Count Python files in a directory (excluding __init__.py)."""
        if not path.exists():
            return 0
        return len([f for f in path.glob("*.py") if f.name != "__init__.py"])

"""Reading what a file imports.

The dependency rule is about who may reach for whom, so checking it
needs to know what each file reaches for. This reads that out of the
AST: no module is imported to find out what it imports.

Imports anywhere in a file are found, not only at the top. A function
that imports inside itself is still an import, and deferring one is a
common way to reach somewhere a file is not supposed to reach — often
without meaning to, to break a cycle.
"""

import ast
import logging
from pathlib import Path

from pydantic import BaseModel, Field

__all__ = ["ImportInfo", "extract_imports", "imports_under"]

logger = logging.getLogger(__name__)


class ImportInfo(BaseModel):
    """One import statement, as written."""

    module: str = Field(
        description='Module imported from, e.g. "julee_hcd.domain.models"'
    )
    names: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Names taken from it, empty for a plain import",
    )
    is_relative: bool = Field(default=False, description="True for a from-dot import")
    file: str = Field(default="", description="The file the import is in")
    line: int = Field(default=0, description="Where in that file")


def extract_imports(file_path: Path) -> list[ImportInfo]:
    """Every import in one file, wherever it appears.

    A file that will not parse yields nothing and says so in the log,
    rather than failing: doctrine reports on a codebase, and a codebase
    with a syntax error has a more pressing problem than its imports.

    Args:
        file_path: The Python file to read

    Returns:
        Its imports, in the order they appear
    """
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except (OSError, SyntaxError, ValueError) as problem:
        logger.warning("Could not read imports from %s: %s", file_path, problem)
        return []

    found: list[ImportInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                ImportInfo(
                    module=alias.name,
                    file=str(file_path),
                    line=node.lineno,
                )
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            found.append(
                ImportInfo(
                    module=node.module or "",
                    names=tuple(alias.name for alias in node.names),
                    is_relative=node.level > 0,
                    file=str(file_path),
                    line=node.lineno,
                )
            )
    return sorted(found, key=lambda info: (info.line, info.module))


def imports_under(root: Path) -> list[ImportInfo]:
    """Every import in every Python file under a directory.

    Args:
        root: Directory to walk

    Returns:
        The imports found, with the file each came from
    """
    skip = {".venv", "build", "dist", "__pycache__", "node_modules", ".git"}
    return [
        info
        for py_file in sorted(root.rglob("*.py"))
        if not any(part in skip for part in py_file.parts)
        for info in extract_imports(py_file)
    ]

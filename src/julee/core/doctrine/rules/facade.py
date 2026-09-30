"""What the facade rule objects to.

An ``__init__.py`` imports nothing it does not use (ADR 019). A name it
imports and then does nothing with but list in ``__all__`` is a
re-export: a facade between a name and where it lives.

The test is use, not shape. A package's ``__init__`` that defines a
function and imports what that function needs is a module, whatever its
filename. A Sphinx extension's ``__init__`` that imports directives and
registers them in ``setup()`` is using them. Neither is a facade, and
neither needs an exception written for it.
"""

import ast
from collections.abc import Iterable

SKIPPED_DIRECTORIES = frozenset(
    {".venv", "build", "dist", "__pycache__", "node_modules"}
)
"""Where a walk of a source root does not go."""


def re_exports_in(source: str) -> list[str]:
    """The names an ``__init__.py`` imports and does nothing with.

    Every name bound by an import statement, less every name the
    module's own code refers to. ``__all__`` does not count as a
    reference: listing a name there is the re-export, not a use of it.

    Args:
        source: The module's text

    Returns:
        The re-exported names, in the order they were imported;
        ``"*"`` for a star import, which re-exports everything
    """
    tree = ast.parse(source)
    imported: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported += [
                alias.asname or alias.name.split(".")[0] for alias in node.names
            ]
        elif isinstance(node, ast.ImportFrom):
            imported += [alias.asname or alias.name for alias in node.names]

    used: set[str] = set()
    for node in tree.body:
        if _is_the_all_list(node):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Name):
                used.add(inner.id)
    return [name for name in imported if name == "*" or name not in used]


def _is_the_all_list(node: ast.stmt) -> bool:
    """Whether a statement is the ``__all__ = [...]`` assignment."""
    targets: list[ast.expr] = []
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign | ast.AugAssign):
        targets = [node.target]
    return any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets)


def facades(found: Iterable[tuple[str, tuple[str, ...]]]) -> list[str]:
    """One objection per ``__init__.py`` that re-exports.

    Args:
        found: Each ``__init__.py`` that re-exports, as its path relative
            to the target and the names it re-exports

    Returns:
        One sentence per file, naming the names
    """
    return [
        f"{path} re-exports {', '.join(names)}: a name is imported from the "
        f"module that defines it, and an __init__.py imports nothing it does "
        f"not use (ADR 019)"
        for path, names in found
    ]

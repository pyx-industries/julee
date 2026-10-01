"""Reading what a module declares.

The class parser answers what classes a file holds and what is in them.
This answers a plainer question about the same file: what it declares at
module level, and on which line. Nothing is imported to find out.

Module level is the module body and the blocks of any ``if``, ``try``
or ``with`` in it, however deep, because a class declared under ``if
TYPE_CHECKING`` or in a ``try`` is still the module's, and the class
parser reads it as one. Anything inside a class or a function is not:
a nested class and a method belong to what encloses them.
"""

import ast
from collections.abc import Iterator
from dataclasses import dataclass

__all__ = [
    "BINDING",
    "CLASS",
    "FUNCTION",
    "Found",
    "declarations_in",
]

CLASS = "class"
FUNCTION = "function"
BINDING = "binding"
"""A name assigned the result of a call, ``Name = something(...)``.

Identities and registries are made this way, a ``NewType`` or a table of
permissions. So are type variables and compiled patterns, and nothing
in the syntax tells them apart."""


@dataclass(frozen=True)
class Found:
    """One declaration, as far as the source alone says."""

    name: str
    kind: str
    line: int


def declarations_in(source: str) -> list[Found]:
    """What a module declares at module level.

    Classes, functions, and assignments of a call to a single name. Not
    other assignments, so not a constant or a plain alias, and not an
    imported name, which is declared somewhere else.

    Args:
        source: The text of a Python module

    Returns:
        Its declarations, in the order they appear

    Raises:
        SyntaxError: If the source does not parse
        ValueError: If the source cannot be parsed at all, as when it
            holds a null byte
    """
    return sorted(
        _found_in(ast.parse(source).body), key=lambda found: (found.line, found.name)
    )


def _found_in(statements: list[ast.stmt]) -> Iterator[Found]:
    """The declarations among some statements, and in the blocks they open."""
    for node in statements:
        if isinstance(node, ast.ClassDef):
            yield Found(node.name, CLASS, node.lineno)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield Found(node.name, FUNCTION, node.lineno)
        elif isinstance(node, ast.Assign):
            if (
                isinstance(node.value, ast.Call)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                yield Found(node.targets[0].id, BINDING, node.lineno)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.value, ast.Call) and isinstance(node.target, ast.Name):
                yield Found(node.target.id, BINDING, node.lineno)
        else:
            for block in _blocks_of(node):
                yield from _found_in(block)


def _blocks_of(node: ast.stmt) -> list[list[ast.stmt]]:
    """The statement blocks a module-level ``if``, ``try`` or ``with`` opens."""
    if isinstance(node, ast.If):
        return [node.body, node.orelse]
    if isinstance(node, ast.Try | ast.TryStar):
        return [
            node.body,
            *(handler.body for handler in node.handlers),
            node.orelse,
            node.finalbody,
        ]
    if isinstance(node, ast.With | ast.AsyncWith):
        return [node.body]
    return []

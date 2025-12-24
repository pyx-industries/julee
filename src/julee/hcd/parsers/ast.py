"""Python code introspection parser.

Re-exports from julee.shared.parsers.ast for backward compatibility.
These parsers are core introspection tools and live in shared/.
"""

from julee.shared.parsers.ast import (
    parse_bounded_context,
    parse_module_docstring,
    parse_python_classes,
    parse_python_classes_from_file,
    scan_bounded_contexts,
)

__all__ = [
    "parse_bounded_context",
    "parse_module_docstring",
    "parse_python_classes",
    "parse_python_classes_from_file",
    "scan_bounded_contexts",
]

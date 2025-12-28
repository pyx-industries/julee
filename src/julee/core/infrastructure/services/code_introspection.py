"""AST-based code introspection service implementation."""

from pathlib import Path

from julee.core.entities.code_info import BoundedContextInfo
from julee.core.parsers.ast import parse_bounded_context, scan_bounded_contexts


class AstCodeIntrospectionService:
    """Code introspection service using AST parsing.

    Wraps julee.core.parsers.ast to implement the CodeIntrospectionService protocol.
    """

    def get_bounded_context(self, context_path: Path) -> BoundedContextInfo | None:
        """Get introspection info for a bounded context."""
        return parse_bounded_context(context_path)

    def list_bounded_contexts(self, src_dir: Path) -> list[BoundedContextInfo]:
        """List all bounded contexts under a source directory."""
        return scan_bounded_contexts(src_dir)

"""Code introspection service protocol.

Service for introspecting code structure - discovering entities, repositories,
use cases, and bounded contexts from Python source.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from julee.core.entities.code_info import BoundedContextInfo


@runtime_checkable
class CodeIntrospectionService(Protocol):
    """Service for introspecting code structure.

    Provides domain-semantic access to code analysis, abstracting
    the underlying parsing implementation (AST, importlib, etc.).
    """

    def get_bounded_context(self, context_path: Path) -> BoundedContextInfo | None:
        """Get introspection info for a bounded context.

        Args:
            context_path: Path to the bounded context directory

        Returns:
            BoundedContextInfo if found, None otherwise
        """
        ...

    def list_bounded_contexts(self, src_dir: Path) -> list[BoundedContextInfo]:
        """List all bounded contexts under a source directory.

        Args:
            src_dir: Root source directory to scan

        Returns:
            List of discovered bounded contexts
        """
        ...

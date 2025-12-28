"""JuleeCodeRepository protocol.

Repository for accessing Julee-structured codebases, returning domain entities
like BoundedContextInfo that capture the semantic structure of the code.

This demonstrates that the Repository pattern applies to any persistent data
source, not just databases. A git repository IS a repository in the Clean
Architecture sense - it's a persistent store of data (code) that we query
for information, with implementation details (filesystem, remote, etc.)
abstracted away.

    Repository Pattern:
        - Abstracts data access from a persistent store
        - Returns domain entities
        - Implementation details are hidden

    JuleeCodeRepository:
        - Persistent store: a codebase (local filesystem, git repo, remote API)
        - Domain entities: BoundedContextInfo (Julee's semantic model of code)
        - Implementations: AstJuleeCodeRepository, RemoteJuleeCodeRepository, etc.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from julee.core.entities.code_info import BoundedContextInfo


@runtime_checkable
class JuleeCodeRepository(Protocol):
    """Repository for accessing Julee-structured codebases.

    Abstracts access to code that follows Julee conventions, returning
    domain entities like BoundedContextInfo. The backing store is a
    codebase - demonstrating that the Repository pattern applies to
    any persistent data source, not just databases.

    A git repository is literally an instance of the Repository pattern:
    this protocol abstracts access to it.
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
            List of discovered bounded contexts with their code structure
        """
        ...

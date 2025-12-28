"""Doctrine verifier service protocol.

Defines the interface for verifying doctrine compliance. The primary
implementation runs pytest on doctrine test files.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from julee.core.entities.doctrine import DoctrineVerificationReport


@runtime_checkable
class DoctrineVerifier(Protocol):
    """Service for verifying doctrine compliance.

    This runs the actual doctrine tests (via pytest) and reports
    results. It's a service, not a repository, because verification
    involves test execution, not just reading data.
    """

    async def verify(
        self,
        target: Path,
        area: str | None = None,
        scope: str = "all",
    ) -> DoctrineVerificationReport:
        """Verify a solution's compliance with doctrine.

        Args:
            target: Path to the solution to verify
            area: Optional area to filter verification
            scope: What to verify - "core", "apps", or "all"

        Returns:
            Complete verification report with pass/fail for each rule
        """
        ...

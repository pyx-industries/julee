"""Verify doctrine compliance use case.

Runs doctrine tests against a target solution and returns structured
results. The tests ARE the doctrine - this use case executes them.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.core.entities.doctrine import DoctrineVerificationReport
from julee.core.services.doctrine_verifier import DoctrineVerifier


class VerifyDoctrineRequest(BaseModel):
    """Request for verifying doctrine compliance."""

    target: Path = Field(description="Path to the solution to verify")
    area: str | None = Field(
        default=None,
        description="Optional area to filter (e.g., 'bounded_context')",
    )
    scope: str = Field(
        default="all",
        description="What to verify: 'core', 'apps', or 'all'",
    )

    model_config = {"arbitrary_types_allowed": True}


class VerifyDoctrineResponse(BaseModel):
    """Response containing verification results."""

    report: DoctrineVerificationReport
    exit_code: int = Field(description="0 if all passed, non-zero otherwise")

    model_config = {"arbitrary_types_allowed": True}


@use_case
class VerifyDoctrineUseCase:
    """Verify a solution's compliance with architectural doctrine.

    This use case runs doctrine tests via pytest and returns structured
    results. The tests ARE the doctrine - their assertions enforce the
    rules stated in their docstrings.
    """

    def __init__(self, doctrine_verifier: DoctrineVerifier) -> None:
        """Initialize with doctrine verifier service.

        Args:
            doctrine_verifier: Service for running doctrine tests
        """
        self.verifier = doctrine_verifier

    async def execute(self, request: VerifyDoctrineRequest) -> VerifyDoctrineResponse:
        """Execute the verification.

        Args:
            request: Request with target path and optional filters

        Returns:
            Response containing verification report and exit code
        """
        report = await self.verifier.verify(
            target=request.target,
            area=request.area,
        )

        exit_code = 0 if report.passed else 1

        return VerifyDoctrineResponse(report=report, exit_code=exit_code)

"""ValidateAcceleratorsUseCase with co-located request/response.

Use case for validating accelerators against code structure.

Compares documented accelerators (from RST define-accelerator:: directives)
with discovered bounded contexts (from src/ directory scanning) to identify:
- Bounded contexts in code that are not documented
- Documented accelerators that have no corresponding code
"""

from pydantic import BaseModel

from ...models.accelerator import AcceleratorValidationIssue
from ...repositories.accelerator import AcceleratorRepository
from ...repositories.code_info import CodeInfoRepository


class ValidateAcceleratorsRequest(BaseModel):
    """Request for validating accelerators against code structure.

    Compares documented accelerators (from RST) with discovered bounded
    contexts (from src/ directory scanning).
    """

    pass


class ValidateAcceleratorsResponse(BaseModel):
    """Response from validating accelerators against code structure.

    Contains lists of matched accelerators and any issues found.
    """

    documented_slugs: list[str]
    discovered_slugs: list[str]
    matched_slugs: list[str]
    issues: list[AcceleratorValidationIssue]

    @property
    def is_valid(self) -> bool:
        """Check if validation passed with no issues."""
        return len(self.issues) == 0


class ValidateAcceleratorsUseCase:
    """Use case for validating accelerators against discovered code.

    .. usecase-documentation:: julee.hcd.domain.use_cases.queries.validate_accelerators:ValidateAcceleratorsUseCase

    Cross-references documented accelerators with discovered bounded contexts
    to ensure documentation stays in sync with the codebase.
    """

    def __init__(
        self,
        accelerator_repo: AcceleratorRepository,
        code_info_repo: CodeInfoRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            accelerator_repo: Repository for documented accelerators
            code_info_repo: Repository for discovered bounded contexts
        """
        self.accelerator_repo = accelerator_repo
        self.code_info_repo = code_info_repo

    async def execute(
        self, request: ValidateAcceleratorsRequest
    ) -> ValidateAcceleratorsResponse:
        """Validate accelerators against code structure.

        Process:
        1. Get all documented accelerators from RST
        2. Get all discovered bounded contexts from code scanning
        3. Compare slugs to find matches and mismatches
        4. Generate issues for undocumented code and documented-but-no-code

        Args:
            request: Validation request (extensible for future filtering)

        Returns:
            Response containing validation results and any issues found
        """
        # Get documented accelerators
        documented = await self.accelerator_repo.list_all()
        documented_slugs = {acc.slug for acc in documented}

        # Get discovered bounded contexts
        discovered = await self.code_info_repo.list_all()
        discovered_slugs = {ctx.slug for ctx in discovered}

        # Find matches and mismatches
        matched_slugs = documented_slugs & discovered_slugs
        undocumented_slugs = discovered_slugs - documented_slugs
        no_code_slugs = documented_slugs - discovered_slugs

        # Build issues list
        issues: list[AcceleratorValidationIssue] = []

        for slug in sorted(undocumented_slugs):
            ctx = next((c for c in discovered if c.slug == slug), None)
            summary = ctx.summary() if ctx else "unknown"
            issues.append(
                AcceleratorValidationIssue(
                    slug=slug,
                    issue_type="undocumented",
                    message=f"Bounded context '{slug}' exists in code ({summary}) "
                    "but has no define-accelerator:: directive",
                )
            )

        for slug in sorted(no_code_slugs):
            issues.append(
                AcceleratorValidationIssue(
                    slug=slug,
                    issue_type="no_code",
                    message=f"Accelerator '{slug}' is documented but has no "
                    "corresponding bounded context in src/",
                )
            )

        return ValidateAcceleratorsResponse(
            documented_slugs=sorted(documented_slugs),
            discovered_slugs=sorted(discovered_slugs),
            matched_slugs=sorted(matched_slugs),
            issues=issues,
        )

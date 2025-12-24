"""Create accelerator use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from ...models.accelerator import Accelerator, IntegrationReference
from ...repositories.accelerator import AcceleratorRepository


class IntegrationReferenceItem(BaseModel):
    """Nested item representing an integration reference."""

    slug: str = Field(description="Integration slug")
    description: str = Field(default="", description="What is sourced/published")

    def to_domain_model(self) -> IntegrationReference:
        """Convert to IntegrationReference."""
        return IntegrationReference(slug=self.slug, description=self.description)


class CreateAcceleratorRequest(BaseModel):
    """Request model for creating an accelerator.

    Fields excluded from client control:
    - docname: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    status: str = Field(default="", description="Development status")
    milestone: str | None = Field(default=None, description="Target milestone")
    acceptance: str | None = Field(
        default=None, description="Acceptance criteria description"
    )
    objective: str = Field(default="", description="Business objective/description")
    sources_from: list[IntegrationReferenceItem] = Field(
        default_factory=list, description="Integrations this accelerator reads from"
    )
    feeds_into: list[str] = Field(
        default_factory=list, description="Other accelerators this one feeds data into"
    )
    publishes_to: list[IntegrationReferenceItem] = Field(
        default_factory=list, description="Integrations this accelerator writes to"
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Other accelerators this one depends on"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Accelerator.validate_slug(v)

    def to_domain_model(self) -> Accelerator:
        """Convert to Accelerator."""
        return Accelerator(
            slug=self.slug,
            status=self.status,
            milestone=self.milestone,
            acceptance=self.acceptance,
            objective=self.objective,
            sources_from=[s.to_domain_model() for s in self.sources_from],
            feeds_into=self.feeds_into,
            publishes_to=[p.to_domain_model() for p in self.publishes_to],
            depends_on=self.depends_on,
            docname="",
        )


class CreateAcceleratorResponse(BaseModel):
    """Response from creating an accelerator."""

    accelerator: Accelerator


class CreateAcceleratorUseCase:
    """Use case for creating an accelerator.

    .. usecase-documentation:: julee.hcd.domain.use_cases.accelerator.create:CreateAcceleratorUseCase
    """

    def __init__(self, accelerator_repo: AcceleratorRepository) -> None:
        """Initialize with repository dependency.

        Args:
            accelerator_repo: Accelerator repository instance
        """
        self.accelerator_repo = accelerator_repo

    async def execute(
        self, request: CreateAcceleratorRequest
    ) -> CreateAcceleratorResponse:
        """Create a new accelerator.

        Args:
            request: Accelerator creation request with accelerator data

        Returns:
            Response containing the created accelerator
        """
        accelerator = request.to_domain_model()
        await self.accelerator_repo.save(accelerator)
        return CreateAcceleratorResponse(accelerator=accelerator)

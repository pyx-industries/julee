"""Create dynamic step use case with co-located request/response."""

from pydantic import BaseModel, Field

from julee.c4.entities.dynamic_step import DynamicStep
from julee.c4.entities.relationship import ElementType
from julee.c4.repositories.dynamic_step import DynamicStepRepository


class CreateDynamicStepRequest(BaseModel):
    """Request model for creating a dynamic step."""

    slug: str = Field(
        default="", description="URL-safe identifier (auto-generated if empty)"
    )
    sequence_name: str = Field(description="Name of the dynamic sequence")
    step_number: int = Field(description="Order within sequence (1-based)")
    source_type: str = Field(description="Type of source element")
    source_slug: str = Field(description="Slug of source element")
    destination_type: str = Field(description="Type of destination element")
    destination_slug: str = Field(description="Slug of destination element")
    description: str = Field(default="", description="Step description")
    technology: str = Field(default="", description="Protocol/technology used")
    return_description: str = Field(default="", description="Return value description")
    is_return: bool = Field(default=False, description="Whether this is a return step")

    def to_domain_model(self) -> DynamicStep:
        """Convert to DynamicStep."""
        slug = self.slug
        if not slug:
            slug = f"{self.sequence_name}-step-{self.step_number}"
        return DynamicStep(
            slug=slug,
            sequence_name=self.sequence_name,
            step_number=self.step_number,
            source_type=ElementType(self.source_type),
            source_slug=self.source_slug,
            destination_type=ElementType(self.destination_type),
            destination_slug=self.destination_slug,
            description=self.description,
            technology=self.technology,
            return_value=self.return_description,
            is_async=self.is_return,
            docname="",
        )


class CreateDynamicStepResponse(BaseModel):
    """Response from creating a dynamic step."""

    dynamic_step: DynamicStep


class CreateDynamicStepUseCase:
    """Use case for creating a dynamic step.

    .. usecase-documentation:: julee.c4.domain.use_cases.dynamic_step.create:CreateDynamicStepUseCase
    """

    def __init__(self, dynamic_step_repo: DynamicStepRepository) -> None:
        """Initialize with repository dependency.

        Args:
            dynamic_step_repo: DynamicStep repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo

    async def execute(
        self, request: CreateDynamicStepRequest
    ) -> CreateDynamicStepResponse:
        """Create a new dynamic step.

        Args:
            request: Dynamic step creation request with data

        Returns:
            Response containing the created dynamic step
        """
        dynamic_step = request.to_domain_model()
        await self.dynamic_step_repo.save(dynamic_step)
        return CreateDynamicStepResponse(dynamic_step=dynamic_step)

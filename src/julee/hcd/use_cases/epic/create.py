"""Create epic use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from julee.core.decorators import use_case
from julee.hcd.entities.epic import Epic
from julee.hcd.repositories.epic import EpicRepository


class CreateEpicRequest(BaseModel):
    """Request model for creating an epic."""

    slug: str = Field(description="URL-safe identifier")
    description: str = Field(
        default="", description="Human-readable description of the epic"
    )
    story_refs: list[str] = Field(
        default_factory=list, description="List of story feature titles in this epic"
    )
    docname: str = Field(default="", description="RST document where defined")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Epic.validate_slug(v)

    def to_domain_model(self) -> Epic:
        """Convert to Epic."""
        return Epic(
            slug=self.slug,
            description=self.description,
            story_refs=self.story_refs,
            docname=self.docname,
        )


class CreateEpicResponse(BaseModel):
    """Response from creating an epic."""

    epic: Epic


@use_case
class CreateEpicUseCase:
    """Use case for creating an epic.

    .. usecase-documentation:: julee.hcd.domain.use_cases.epic.create:CreateEpicUseCase
    """

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: CreateEpicRequest) -> CreateEpicResponse:
        """Create a new epic.

        Args:
            request: Epic creation request with epic data

        Returns:
            Response containing the created epic
        """
        epic = request.to_domain_model()
        await self.epic_repo.save(epic)
        return CreateEpicResponse(epic=epic)

"""CreateSoftwareSystemUseCase with co-located request/response.

Use case for creating a new software system.
"""


from pydantic import BaseModel, Field, field_validator

from ...models.software_system import SoftwareSystem, SystemType
from ...repositories.software_system import SoftwareSystemRepository


class CreateSoftwareSystemRequest(BaseModel):
    """Request model for creating a software system."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    system_type: str = Field(
        default="internal", description="Type: internal, external, existing"
    )
    owner: str = Field(default="", description="Owning team")
    technology: str = Field(default="", description="High-level tech stack")
    url: str = Field(default="", description="Link to documentation")
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    def to_domain_model(self) -> SoftwareSystem:
        """Convert to SoftwareSystem."""
        return SoftwareSystem(
            slug=self.slug,
            name=self.name,
            description=self.description,
            system_type=SystemType(self.system_type),
            owner=self.owner,
            technology=self.technology,
            url=self.url,
            tags=self.tags,
            docname="",
        )


class CreateSoftwareSystemResponse(BaseModel):
    """Response from creating a software system."""

    software_system: SoftwareSystem


class CreateSoftwareSystemUseCase:
    """Use case for creating a software system.

    .. usecase-documentation:: julee.c4.domain.use_cases.software_system.create:CreateSoftwareSystemUseCase
    """

    def __init__(self, software_system_repo: SoftwareSystemRepository) -> None:
        """Initialize with repository dependency.

        Args:
            software_system_repo: SoftwareSystem repository instance
        """
        self.software_system_repo = software_system_repo

    async def execute(
        self, request: CreateSoftwareSystemRequest
    ) -> CreateSoftwareSystemResponse:
        """Create a new software system.

        Args:
            request: Software system creation request with data

        Returns:
            Response containing the created software system
        """
        software_system = request.to_domain_model()
        await self.software_system_repo.save(software_system)
        return CreateSoftwareSystemResponse(software_system=software_system)

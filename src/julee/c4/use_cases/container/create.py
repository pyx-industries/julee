"""Create container use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from julee.c4.entities.container import Container, ContainerType
from julee.c4.repositories.container import ContainerRepository


class CreateContainerRequest(BaseModel):
    """Request model for creating a container."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    system_slug: str = Field(description="Parent software system slug")
    description: str = Field(default="", description="Human-readable description")
    container_type: str = Field(default="other", description="Type of container")
    technology: str = Field(default="", description="Specific technology stack")
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

    @field_validator("system_slug")
    @classmethod
    def validate_system_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("system_slug cannot be empty")
        return v.strip()

    def to_domain_model(self) -> Container:
        """Convert to Container."""
        return Container(
            slug=self.slug,
            name=self.name,
            system_slug=self.system_slug,
            description=self.description,
            container_type=ContainerType(self.container_type),
            technology=self.technology,
            url=self.url,
            tags=self.tags,
            docname="",
        )


class CreateContainerResponse(BaseModel):
    """Response from creating a container."""

    container: Container


class CreateContainerUseCase:
    """Use case for creating a container.

    .. usecase-documentation:: julee.c4.domain.use_cases.container.create:CreateContainerUseCase
    """

    def __init__(self, container_repo: ContainerRepository) -> None:
        """Initialize with repository dependency.

        Args:
            container_repo: Container repository instance
        """
        self.container_repo = container_repo

    async def execute(self, request: CreateContainerRequest) -> CreateContainerResponse:
        """Create a new container.

        Args:
            request: Container creation request with data

        Returns:
            Response containing the created container
        """
        container = request.to_domain_model()
        await self.container_repo.save(container)
        return CreateContainerResponse(container=container)

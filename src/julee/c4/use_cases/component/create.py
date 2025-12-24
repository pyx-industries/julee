"""Create component use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from julee.c4.entities.component import Component
from julee.c4.repositories.component import ComponentRepository


class CreateComponentRequest(BaseModel):
    """Request model for creating a component."""

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    container_slug: str = Field(description="Parent container slug")
    system_slug: str = Field(description="Grandparent system slug")
    description: str = Field(default="", description="Human-readable description")
    technology: str = Field(default="", description="Implementation technology")
    interface: str = Field(default="", description="Interface description")
    code_path: str = Field(default="", description="Link to implementation code")
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

    def to_domain_model(self) -> Component:
        """Convert to Component."""
        return Component(
            slug=self.slug,
            name=self.name,
            container_slug=self.container_slug,
            system_slug=self.system_slug,
            description=self.description,
            technology=self.technology,
            interface=self.interface,
            code_path=self.code_path,
            url=self.url,
            tags=self.tags,
            docname="",
        )


class CreateComponentResponse(BaseModel):
    """Response from creating a component."""

    component: Component


class CreateComponentUseCase:
    """Use case for creating a component.

    .. usecase-documentation:: julee.c4.domain.use_cases.component.create:CreateComponentUseCase
    """

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: CreateComponentRequest) -> CreateComponentResponse:
        """Create a new component.

        Args:
            request: Component creation request with data

        Returns:
            Response containing the created component
        """
        component = request.to_domain_model()
        await self.component_repo.save(component)
        return CreateComponentResponse(component=component)

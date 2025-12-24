"""Create integration use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from ...models.integration import Direction, ExternalDependency, Integration
from ...repositories.integration import IntegrationRepository


class ExternalDependencyItem(BaseModel):
    """Nested item representing an external dependency."""

    name: str = Field(description="Display name of the external system")
    url: str | None = Field(
        default=None, description="URL for documentation or reference"
    )
    description: str = Field(default="", description="Brief description")

    def to_domain_model(self) -> ExternalDependency:
        """Convert to ExternalDependency."""
        return ExternalDependency(
            name=self.name, url=self.url, description=self.description
        )


class CreateIntegrationRequest(BaseModel):
    """Request model for creating an integration.

    Fields excluded from client control:
    - name_normalized: Computed by domain model
    - manifest_path: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    module: str = Field(description="Python module name")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    direction: str = Field(
        default="bidirectional",
        description="Data flow direction: inbound, outbound, bidirectional",
    )
    depends_on: list[ExternalDependencyItem] = Field(
        default_factory=list, description="List of external dependencies"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return Integration.validate_slug(v)

    @field_validator("module")
    @classmethod
    def validate_module(cls, v: str) -> str:
        return Integration.validate_module(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return Integration.validate_name(v)

    def to_domain_model(self) -> Integration:
        """Convert to Integration."""
        return Integration(
            slug=self.slug,
            module=self.module,
            name=self.name,
            description=self.description,
            direction=Direction.from_string(self.direction),
            depends_on=[d.to_domain_model() for d in self.depends_on],
            manifest_path="",
        )


class CreateIntegrationResponse(BaseModel):
    """Response from creating an integration."""

    integration: Integration


class CreateIntegrationUseCase:
    """Use case for creating an integration.

    .. usecase-documentation:: julee.hcd.domain.use_cases.integration.create:CreateIntegrationUseCase
    """

    def __init__(self, integration_repo: IntegrationRepository) -> None:
        """Initialize with repository dependency.

        Args:
            integration_repo: Integration repository instance
        """
        self.integration_repo = integration_repo

    async def execute(
        self, request: CreateIntegrationRequest
    ) -> CreateIntegrationResponse:
        """Create a new integration.

        Args:
            request: Integration creation request with integration data

        Returns:
            Response containing the created integration
        """
        integration = request.to_domain_model()
        await self.integration_repo.save(integration)
        return CreateIntegrationResponse(integration=integration)

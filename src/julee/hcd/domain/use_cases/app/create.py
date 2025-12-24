"""Create app use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from ...models.app import App, AppType
from ...repositories.app import AppRepository


class CreateAppRequest(BaseModel):
    """Request model for creating an app.

    Fields excluded from client control:
    - name_normalized: Computed by domain model
    - manifest_path: Set when persisted
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name")
    app_type: str = Field(
        default="unknown",
        description="Classification: staff, external, member-tool, unknown",
    )
    status: str | None = Field(default=None, description="Status indicator")
    description: str = Field(default="", description="Human-readable description")
    accelerators: list[str] = Field(
        default_factory=list, description="List of accelerator slugs"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return App.validate_slug(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return App.validate_name(v)

    def to_domain_model(self) -> App:
        """Convert to App."""
        return App(
            slug=self.slug,
            name=self.name,
            app_type=AppType.from_string(self.app_type),
            status=self.status,
            description=self.description,
            accelerators=self.accelerators,
            manifest_path="",
        )


class CreateAppResponse(BaseModel):
    """Response from creating an app."""

    app: App


class CreateAppUseCase:
    """Use case for creating an app.

    .. usecase-documentation:: julee.hcd.domain.use_cases.app.create:CreateAppUseCase
    """

    def __init__(self, app_repo: AppRepository) -> None:
        """Initialize with repository dependency.

        Args:
            app_repo: App repository instance
        """
        self.app_repo = app_repo

    async def execute(self, request: CreateAppRequest) -> CreateAppResponse:
        """Create a new app.

        Args:
            request: App creation request with app data

        Returns:
            Response containing the created app
        """
        app = request.to_domain_model()
        await self.app_repo.save(app)
        return CreateAppResponse(app=app)

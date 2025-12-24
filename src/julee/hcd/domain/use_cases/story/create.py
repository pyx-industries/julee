"""Create story use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from ...models.story import Story
from ...repositories.story import StoryRepository


class CreateStoryRequest(BaseModel):
    """Request model for creating a story.

    Fields excluded from client control:
    - slug: Generated from feature_title + app_slug
    - persona_normalized/app_normalized: Computed by domain model
    """

    feature_title: str = Field(description="The Feature: line from the Gherkin file")
    persona: str = Field(description="The actor from 'As a <persona>'")
    app_slug: str = Field(description="The application this story belongs to")
    i_want: str = Field(
        default="do something", description="The action from 'I want to <action>'"
    )
    so_that: str = Field(
        default="achieve a goal", description="The benefit from 'So that <benefit>'"
    )
    file_path: str = Field(default="", description="Relative path to the .feature file")
    abs_path: str = Field(default="", description="Absolute path to the .feature file")
    gherkin_snippet: str = Field(
        default="", description="The story header portion of the feature file"
    )

    @field_validator("feature_title")
    @classmethod
    def validate_feature_title(cls, v: str) -> str:
        return Story.validate_feature_title(v)

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: str) -> str:
        return Story.validate_persona(v)

    @field_validator("app_slug")
    @classmethod
    def validate_app_slug(cls, v: str) -> str:
        return Story.validate_app_slug(v)

    def to_domain_model(self) -> Story:
        """Convert to Story, generating slug from feature_title + app_slug."""
        return Story.from_feature_file(
            feature_title=self.feature_title,
            persona=self.persona,
            i_want=self.i_want,
            so_that=self.so_that,
            app_slug=self.app_slug,
            file_path=self.file_path,
            abs_path=self.abs_path,
            gherkin_snippet=self.gherkin_snippet,
        )


class CreateStoryResponse(BaseModel):
    """Response from creating a story."""

    story: Story


class CreateStoryUseCase:
    """Use case for creating a story.

    .. usecase-documentation:: julee.hcd.domain.use_cases.story.create:CreateStoryUseCase
    """

    def __init__(self, story_repo: StoryRepository) -> None:
        """Initialize with repository dependency.

        Args:
            story_repo: Story repository instance
        """
        self.story_repo = story_repo

    async def execute(self, request: CreateStoryRequest) -> CreateStoryResponse:
        """Create a new story.

        Args:
            request: Story creation request with story data

        Returns:
            Response containing the created story
        """
        story = request.to_domain_model()
        await self.story_repo.save(story)
        return CreateStoryResponse(story=story)

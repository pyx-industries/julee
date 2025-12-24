"""Create persona use case with co-located request/response."""

from pydantic import BaseModel, Field, field_validator

from julee.hcd.entities.persona import Persona

from ...repositories.persona import PersonaRepository


class CreatePersonaRequest(BaseModel):
    """Request model for creating a persona.

    Creates a first-class persona definition with HCD metadata.
    """

    slug: str = Field(description="URL-safe identifier")
    name: str = Field(description="Display name (used in Gherkin 'As a {name}')")
    goals: list[str] = Field(
        default_factory=list, description="What the persona wants to achieve"
    )
    frustrations: list[str] = Field(
        default_factory=list, description="Pain points and problems"
    )
    jobs_to_be_done: list[str] = Field(
        default_factory=list, description="JTBD framework items"
    )
    context: str = Field(default="", description="Background and situational context")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return Persona.validate_name(v)

    def to_domain_model(self, docname: str = "") -> Persona:
        """Convert to Persona."""
        return Persona.from_definition(
            slug=self.slug,
            name=self.name,
            goals=self.goals,
            frustrations=self.frustrations,
            jobs_to_be_done=self.jobs_to_be_done,
            context=self.context,
            docname=docname,
        )


class CreatePersonaResponse(BaseModel):
    """Response from creating a persona."""

    persona: Persona


class CreatePersonaUseCase:
    """Use case for creating a persona.

    .. usecase-documentation:: julee.hcd.domain.use_cases.persona.create:CreatePersonaUseCase
    """

    def __init__(self, persona_repo: PersonaRepository) -> None:
        """Initialize with repository dependency.

        Args:
            persona_repo: Persona repository instance
        """
        self.persona_repo = persona_repo

    async def execute(self, request: CreatePersonaRequest) -> CreatePersonaResponse:
        """Create a new persona.

        Args:
            request: Persona creation request with persona data

        Returns:
            Response containing the created persona
        """
        persona = request.to_domain_model()
        await self.persona_repo.save(persona)
        return CreatePersonaResponse(persona=persona)

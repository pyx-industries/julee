"""Create relationship use case with co-located request/response."""

from pydantic import BaseModel, Field

from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.repositories.relationship import RelationshipRepository


class CreateRelationshipRequest(BaseModel):
    """Request model for creating a relationship."""

    slug: str = Field(
        default="", description="URL-safe identifier (auto-generated if empty)"
    )
    source_type: str = Field(description="Type of source element")
    source_slug: str = Field(description="Slug of source element")
    destination_type: str = Field(description="Type of destination element")
    destination_slug: str = Field(description="Slug of destination element")
    description: str = Field(default="Uses", description="Relationship description")
    technology: str = Field(default="", description="Protocol/technology used")
    bidirectional: bool = Field(
        default=False, description="Whether relationship goes both ways"
    )
    tags: list[str] = Field(default_factory=list, description="Classification tags")

    def to_domain_model(self) -> Relationship:
        """Convert to Relationship."""
        slug = self.slug
        if not slug:
            slug = f"{self.source_slug}-to-{self.destination_slug}"
        return Relationship(
            slug=slug,
            source_type=ElementType(self.source_type),
            source_slug=self.source_slug,
            destination_type=ElementType(self.destination_type),
            destination_slug=self.destination_slug,
            description=self.description,
            technology=self.technology,
            bidirectional=self.bidirectional,
            tags=self.tags,
            docname="",
        )


class CreateRelationshipResponse(BaseModel):
    """Response from creating a relationship."""

    relationship: Relationship


class CreateRelationshipUseCase:
    """Use case for creating a relationship.

    .. usecase-documentation:: julee.c4.domain.use_cases.relationship.create:CreateRelationshipUseCase
    """

    def __init__(self, relationship_repo: RelationshipRepository) -> None:
        """Initialize with repository dependency.

        Args:
            relationship_repo: Relationship repository instance
        """
        self.relationship_repo = relationship_repo

    async def execute(
        self, request: CreateRelationshipRequest
    ) -> CreateRelationshipResponse:
        """Create a new relationship.

        Args:
            request: Relationship creation request with data

        Returns:
            Response containing the created relationship
        """
        relationship = request.to_domain_model()
        await self.relationship_repo.save(relationship)
        return CreateRelationshipResponse(relationship=relationship)

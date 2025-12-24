"""Get relationship use case with co-located request/response."""

from pydantic import BaseModel

from ...models.relationship import Relationship
from ...repositories.relationship import RelationshipRepository


class GetRelationshipRequest(BaseModel):
    """Request for getting a relationship by slug."""

    slug: str


class GetRelationshipResponse(BaseModel):
    """Response from getting a relationship."""

    relationship: Relationship | None


class GetRelationshipUseCase:
    """Use case for getting a relationship by slug.

    .. usecase-documentation:: julee.c4.domain.use_cases.relationship.get:GetRelationshipUseCase
    """

    def __init__(self, relationship_repo: RelationshipRepository) -> None:
        """Initialize with repository dependency.

        Args:
            relationship_repo: Relationship repository instance
        """
        self.relationship_repo = relationship_repo

    async def execute(self, request: GetRelationshipRequest) -> GetRelationshipResponse:
        """Get a relationship by slug.

        Args:
            request: Request containing the relationship slug

        Returns:
            Response containing the relationship if found, or None
        """
        relationship = await self.relationship_repo.get(request.slug)
        return GetRelationshipResponse(relationship=relationship)

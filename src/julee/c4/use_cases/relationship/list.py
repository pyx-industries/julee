"""List relationships use case with co-located request/response."""

from pydantic import BaseModel

from julee.c4.entities.relationship import Relationship
from julee.c4.repositories.relationship import RelationshipRepository


class ListRelationshipsRequest(BaseModel):
    """Request for listing relationships."""

    pass


class ListRelationshipsResponse(BaseModel):
    """Response from listing relationships."""

    relationships: list[Relationship]


class ListRelationshipsUseCase:
    """Use case for listing all relationships.

    .. usecase-documentation:: julee.c4.domain.use_cases.relationship.list:ListRelationshipsUseCase
    """

    def __init__(self, relationship_repo: RelationshipRepository) -> None:
        """Initialize with repository dependency.

        Args:
            relationship_repo: Relationship repository instance
        """
        self.relationship_repo = relationship_repo

    async def execute(
        self, request: ListRelationshipsRequest
    ) -> ListRelationshipsResponse:
        """List all relationships.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all relationships
        """
        relationships = await self.relationship_repo.list_all()
        return ListRelationshipsResponse(relationships=relationships)

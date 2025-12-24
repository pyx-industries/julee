"""Delete relationship use case with co-located request/response."""

from pydantic import BaseModel

from ...repositories.relationship import RelationshipRepository


class DeleteRelationshipRequest(BaseModel):
    """Request for deleting a relationship by slug."""

    slug: str


class DeleteRelationshipResponse(BaseModel):
    """Response from deleting a relationship."""

    deleted: bool


class DeleteRelationshipUseCase:
    """Use case for deleting a relationship.

    .. usecase-documentation:: julee.c4.domain.use_cases.relationship.delete:DeleteRelationshipUseCase
    """

    def __init__(self, relationship_repo: RelationshipRepository) -> None:
        """Initialize with repository dependency.

        Args:
            relationship_repo: Relationship repository instance
        """
        self.relationship_repo = relationship_repo

    async def execute(
        self, request: DeleteRelationshipRequest
    ) -> DeleteRelationshipResponse:
        """Delete a relationship by slug.

        Args:
            request: Delete request containing the relationship slug

        Returns:
            Response indicating if deletion was successful
        """
        deleted = await self.relationship_repo.delete(request.slug)
        return DeleteRelationshipResponse(deleted=deleted)

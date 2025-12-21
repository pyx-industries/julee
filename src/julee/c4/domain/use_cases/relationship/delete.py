"""DeleteRelationshipUseCase.

Use case for deleting a relationship.
"""

from ..requests import DeleteRelationshipRequest
from ..responses import DeleteRelationshipResponse
from ...repositories.relationship import RelationshipRepository


class DeleteRelationshipUseCase:
    """Use case for deleting a relationship."""

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

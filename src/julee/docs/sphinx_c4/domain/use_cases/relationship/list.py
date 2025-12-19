"""ListRelationshipsUseCase.

Use case for listing all relationships.
"""

from .....c4_api.requests import ListRelationshipsRequest
from .....c4_api.responses import ListRelationshipsResponse
from ...repositories.relationship import RelationshipRepository


class ListRelationshipsUseCase:
    """Use case for listing all relationships."""

    def __init__(self, relationship_repo: RelationshipRepository) -> None:
        """Initialize with repository dependency.

        Args:
            relationship_repo: Relationship repository instance
        """
        self.relationship_repo = relationship_repo

    async def execute(self, request: ListRelationshipsRequest) -> ListRelationshipsResponse:
        """List all relationships.

        Args:
            request: List request (extensible for future filtering)

        Returns:
            Response containing list of all relationships
        """
        relationships = await self.relationship_repo.list_all()
        return ListRelationshipsResponse(relationships=relationships)

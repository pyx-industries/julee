"""GetRelationshipUseCase.

Use case for getting a relationship by slug.
"""

from ...repositories.relationship import RelationshipRepository
from ..requests import GetRelationshipRequest
from ..responses import GetRelationshipResponse


class GetRelationshipUseCase:
    """Use case for getting a relationship by slug."""

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

"""CreateRelationshipUseCase.

Use case for creating a new relationship.
"""

from ..requests import CreateRelationshipRequest
from ..responses import CreateRelationshipResponse
from ...repositories.relationship import RelationshipRepository


class CreateRelationshipUseCase:
    """Use case for creating a relationship."""

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

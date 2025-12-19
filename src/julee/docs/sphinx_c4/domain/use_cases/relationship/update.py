"""UpdateRelationshipUseCase.

Use case for updating an existing relationship.
"""

from .....c4_api.requests import UpdateRelationshipRequest
from .....c4_api.responses import UpdateRelationshipResponse
from ...repositories.relationship import RelationshipRepository


class UpdateRelationshipUseCase:
    """Use case for updating a relationship."""

    def __init__(self, relationship_repo: RelationshipRepository) -> None:
        """Initialize with repository dependency.

        Args:
            relationship_repo: Relationship repository instance
        """
        self.relationship_repo = relationship_repo

    async def execute(
        self, request: UpdateRelationshipRequest
    ) -> UpdateRelationshipResponse:
        """Update an existing relationship.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated relationship if found
        """
        existing = await self.relationship_repo.get(request.slug)
        if not existing:
            return UpdateRelationshipResponse(relationship=None, found=False)

        updated = request.apply_to(existing)
        await self.relationship_repo.save(updated)
        return UpdateRelationshipResponse(relationship=updated, found=True)

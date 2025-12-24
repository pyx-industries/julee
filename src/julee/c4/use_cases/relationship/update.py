"""Update relationship use case with co-located request/response."""

from typing import Any

from pydantic import BaseModel

from julee.c4.entities.relationship import Relationship
from julee.c4.repositories.relationship import RelationshipRepository


class UpdateRelationshipRequest(BaseModel):
    """Request for updating a relationship."""

    slug: str
    description: str | None = None
    technology: str | None = None
    bidirectional: bool | None = None
    tags: list[str] | None = None

    def apply_to(self, existing: Relationship) -> Relationship:
        """Apply non-None fields to existing relationship."""
        updates: dict[str, Any] = {}
        if self.description is not None:
            updates["description"] = self.description
        if self.technology is not None:
            updates["technology"] = self.technology
        if self.bidirectional is not None:
            updates["bidirectional"] = self.bidirectional
        if self.tags is not None:
            updates["tags"] = self.tags
        return existing.model_copy(update=updates) if updates else existing


class UpdateRelationshipResponse(BaseModel):
    """Response from updating a relationship."""

    relationship: Relationship | None
    found: bool = True


class UpdateRelationshipUseCase:
    """Use case for updating a relationship.

    .. usecase-documentation:: julee.c4.domain.use_cases.relationship.update:UpdateRelationshipUseCase
    """

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

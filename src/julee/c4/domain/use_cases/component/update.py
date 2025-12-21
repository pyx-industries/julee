"""UpdateComponentUseCase.

Use case for updating an existing component.
"""

from ..requests import UpdateComponentRequest
from ..responses import UpdateComponentResponse
from ...repositories.component import ComponentRepository


class UpdateComponentUseCase:
    """Use case for updating a component."""

    def __init__(self, component_repo: ComponentRepository) -> None:
        """Initialize with repository dependency.

        Args:
            component_repo: Component repository instance
        """
        self.component_repo = component_repo

    async def execute(self, request: UpdateComponentRequest) -> UpdateComponentResponse:
        """Update an existing component.

        Args:
            request: Update request with slug and fields to update

        Returns:
            Response containing the updated component if found
        """
        existing = await self.component_repo.get(request.slug)
        if not existing:
            return UpdateComponentResponse(component=None, found=False)

        updated = request.apply_to(existing)
        await self.component_repo.save(updated)
        return UpdateComponentResponse(component=updated, found=True)

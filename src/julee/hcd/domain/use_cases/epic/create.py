"""CreateEpicUseCase.

Use case for creating a new epic.
"""

from ...repositories.epic import EpicRepository
from ..requests import CreateEpicRequest
from ..responses import CreateEpicResponse


class CreateEpicUseCase:
    """Use case for creating an epic.

    .. usecase-documentation:: julee.hcd.domain.use_cases.epic.create:CreateEpicUseCase
    """

    def __init__(self, epic_repo: EpicRepository) -> None:
        """Initialize with repository dependency.

        Args:
            epic_repo: Epic repository instance
        """
        self.epic_repo = epic_repo

    async def execute(self, request: CreateEpicRequest) -> CreateEpicResponse:
        """Create a new epic.

        Args:
            request: Epic creation request with epic data

        Returns:
            Response containing the created epic
        """
        epic = request.to_domain_model()
        await self.epic_repo.save(epic)
        return CreateEpicResponse(epic=epic)

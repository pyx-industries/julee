"""GetSolutionUseCase with co-located request/response.

Use case for getting the current solution structure.
"""

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.solution import Solution
from julee.core.repositories.solution import SolutionRepository


class GetSolutionRequest(BaseModel):
    """Request for getting the solution.

    Currently empty as there's only one solution per project root.
    """

    pass


class GetSolutionResponse(BaseModel):
    """Response from getting the solution."""

    solution: Solution


@use_case
class GetSolutionUseCase:
    """Use case for getting the current solution.

    Returns the solution structure discovered from the project root,
    including bounded contexts, applications, deployments, and nested solutions.
    """

    def __init__(self, solution_repo: SolutionRepository) -> None:
        """Initialize with repository dependency.

        Args:
            solution_repo: Repository for discovering solution structure
        """
        self.solution_repo = solution_repo

    async def execute(self, request: GetSolutionRequest) -> GetSolutionResponse:
        """Get the current solution.

        Args:
            request: Get request (currently unused)

        Returns:
            Response containing the discovered solution
        """
        solution = await self.solution_repo.get()
        return GetSolutionResponse(solution=solution)

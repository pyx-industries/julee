"""SolutionRepository protocol.

Defines the interface for retrieving solution structure.
"""

from typing import Protocol, runtime_checkable

from julee.core.entities.solution import Solution


@runtime_checkable
class SolutionRepository(Protocol):
    """Protocol for solution repository.

    The solution repository discovers the structure of the current solution,
    including bounded contexts, applications, deployments, and nested solutions.
    """

    async def get(self) -> Solution:
        """Get the current solution.

        Returns:
            The discovered solution structure
        """
        ...

"""Solution configuration repository protocol.

Defines the interface for reading solution-level configuration,
particularly [tool.julee] settings from pyproject.toml.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from julee.core.entities.policy import SolutionPolicyConfig


@runtime_checkable
class SolutionConfigRepository(Protocol):
    """Repository for reading solution configuration.

    Provides access to solution-level settings like policy adoption.
    The primary implementation reads from pyproject.toml.
    """

    async def get_policy_config(self, solution_root: Path) -> SolutionPolicyConfig:
        """Read policy configuration for a solution.

        Args:
            solution_root: Path to the solution root directory

        Returns:
            SolutionPolicyConfig with parsed settings
        """
        ...

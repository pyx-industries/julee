"""File-based solution configuration repository.

Reads [tool.julee] configuration from pyproject.toml.
"""

import tomllib
from pathlib import Path

from julee.core.entities.policy import SolutionPolicyConfig


class FileSolutionConfigRepository:
    """Reads solution configuration from pyproject.toml."""

    async def get_policy_config(self, solution_root: Path) -> SolutionPolicyConfig:
        """Read policy configuration from [tool.julee] in pyproject.toml.

        Args:
            solution_root: Path to the solution root directory

        Returns:
            SolutionPolicyConfig with parsed settings, or defaults if not found
        """
        pyproject_path = solution_root / "pyproject.toml"

        if not pyproject_path.exists():
            return SolutionPolicyConfig()

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError:
            return SolutionPolicyConfig()

        tool_julee = data.get("tool", {}).get("julee", None)

        if tool_julee is None:
            return SolutionPolicyConfig()

        return SolutionPolicyConfig(
            is_julee_solution=True,
            policies=tuple(tool_julee.get("policies", [])),
            skip_policies=tuple(tool_julee.get("skip_policies", [])),
        )

"""File-based solution configuration repository.

Reads [tool.julee] configuration from pyproject.toml.
"""

import tomllib
from pathlib import Path

from julee.core.entities.policy import SolutionPolicyConfig


class FileSolutionConfigRepository:
    """Reads solution configuration from pyproject.toml."""

    def get_policy_config_sync(self, solution_root: Path) -> SolutionPolicyConfig:
        """Read policy configuration from [tool.julee] in pyproject.toml.

        Synchronous version for CLI and test fixture usage.

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
            kits=tuple(tool_julee.get("kits", [])),
            search_root=tool_julee.get("search_root"),
            docs_root=tool_julee.get("docs_root"),
            # Left out means apps/, so a solution that has never heard of
            # this keeps the behaviour it had.
            composition_roots=tuple(tool_julee.get("composition_roots", ["apps"])),
        )

    async def get_policy_config(self, solution_root: Path) -> SolutionPolicyConfig:
        """Read policy configuration from [tool.julee] in pyproject.toml.

        Async version for use case compatibility.

        Args:
            solution_root: Path to the solution root directory

        Returns:
            SolutionPolicyConfig with parsed settings, or defaults if not found
        """
        return self.get_policy_config_sync(solution_root)

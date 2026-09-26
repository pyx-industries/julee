"""``pytest --julee-doctrine``: doctrine in a solution's own test run.

The console script answers "does this codebase comply?". This answers a
different question — "did my change break compliance?" — and it answers
it where the author is already looking, among their own failures, rather
than in a separate run somebody has to remember to do.

Registered through the ``pytest11`` entry point, so installing julee is
enough; a solution adds nothing to its conftest.
"""

import os
from pathlib import Path
from typing import Any

from pytest import UsageError

from julee.cli.verify import enclosing_solution

__all__ = ["pytest_addoption", "pytest_load_initial_conftests"]

DOCTRINE_PACKAGE = "julee.core.doctrine"
"""What gets collected when the flag is given."""

TARGET_VARIABLE = "JULEE_TARGET"
"""How the doctrine fixtures are told which codebase to read."""


def pytest_addoption(parser: Any) -> None:
    """Add the flag, and the ini setting for turning it on permanently."""
    parser.getgroup("julee").addoption(
        "--julee-doctrine",
        action="store_true",
        default=False,
        help="also collect julee's doctrine rules against this project",
    )


def pytest_load_initial_conftests(
    early_config: Any, parser: Any, args: list[str]
) -> None:
    """Add the doctrine package to what pytest collects.

    This hook rather than ``pytest_configure`` because collection
    arguments are read before configure runs, so appending there would
    be too late and would do nothing — quietly, which is the failure
    this whole area of the codebase keeps producing.

    The target is the nearest enclosing julee solution, found from the
    directory pytest was invoked in — not pytest's rootdir, which is
    where the ini file lives and is a different thing. In a workspace
    holding several solutions they differ: running a kit's tests from
    the kit's own directory has a rootdir of the workspace root, which
    declares no [tool.julee] at all.

    An explicit ``JULEE_TARGET`` still wins, so a run that already sets
    it keeps working unchanged.
    """
    if not early_config.known_args_namespace.julee_doctrine:
        return

    if TARGET_VARIABLE not in os.environ:
        invoked_in = Path(early_config.invocation_params.dir)
        solution = enclosing_solution(invoked_in)
        if solution is None:
            raise UsageError(
                f"--julee-doctrine: neither {invoked_in} nor any directory "
                f"above it has a pyproject.toml with a [tool.julee] "
                f"section, so there is no solution to check. Add one, or "
                f"set {TARGET_VARIABLE}."
            )
        os.environ[TARGET_VARIABLE] = str(solution)

    args.extend(["--pyargs", DOCTRINE_PACKAGE])

"""Running the doctrine suite against a solution on disk.

A subprocess, so that what is exercised is the suite's collection,
fixtures and assertions rather than a function it calls.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
"""The repository root: doctrine_suite, tests, core, julee, src, root.

The doctrine run needs it as its cwd to find pytest's config.
"""


def run_doctrine(
    target: Path, test_path: str, selector: str
) -> subprocess.CompletedProcess[str]:
    """Run part of the doctrine suite against a solution.

    Args:
        target: The solution root, passed as JULEE_TARGET
        test_path: The doctrine test module, relative to the repo root
        selector: A -k expression choosing the tests to run

    Returns:
        The finished process, stdout captured
    """
    env = {
        **os.environ,
        "JULEE_TARGET": str(target),
        "PYTHONPATH": str(target / "src"),
    }
    env.pop("COV_CORE_SOURCE", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            test_path,
            "-k",
            selector,
            "-q",
            "--no-cov",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:xdist",
            "-o",
            "addopts=",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def assert_doctrine_ran(
    result: subprocess.CompletedProcess[str], expected: int, selector: str
) -> None:
    """Check the expected doctrine tests were collected and run.

    A deleted doctrine test collects nothing, and a run that collects
    nothing reports no failures.

    Args:
        result: A finished doctrine run
        expected: How many tests the selector must collect
        selector: The -k expression, for the failure message
    """
    assert "no tests ran" not in result.stdout, (
        f"the doctrine tests were not collected — has {selector} been "
        f"renamed or deleted?\n{result.stdout}"
    )
    ran = sum(
        int(count) for count, _ in re.findall(r"(\d+) (passed|failed)", result.stdout)
    )
    assert ran == expected, (
        f"expected {expected} doctrine tests, {ran} ran — one has been "
        f"deleted or renamed:\n{result.stdout}"
    )


def a_julee_solution(root: Path) -> Path:
    """Write the pyproject and package roots every solution needs.

    Args:
        root: The solution root to write into

    Returns:
        The bounded context directory, for the caller to fill
    """
    context = root / "src" / "acme" / "stories"
    context.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "acme"\nversion = "0.1.0"\n\n'
        '[tool.julee]\nsearch_root = "src/acme"\ndocs_root = "docs"\n'
    )
    (root / "src" / "acme" / "__init__.py").write_text('"""Acme."""\n')
    (context / "__init__.py").write_text('"""Stories."""\n')
    return context

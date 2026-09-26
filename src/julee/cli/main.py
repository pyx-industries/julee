"""The ``julee`` command.

One subcommand so far: ``julee doctrine verify``. Doctrine was runnable
before this only as ``JULEE_TARGET=... pytest --pyargs
julee.core.doctrine`` — another project's tests, from a path inside an
installed package, with the target passed by environment variable. It
worked, and nobody would guess it (#192).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from julee.cli.verify import (
    pytest_arguments,
    resolve_target,
    target_objections,
)
from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)

__all__ = ["main", "verify"]


def _fail(objections: list[str]) -> int:
    for objection in objections:
        print(f"error: {objection}", file=sys.stderr)
    return 2


def verify(args: argparse.Namespace) -> int:
    """Run doctrine against a codebase and report.

    Returns:
        0 if doctrine passed, 1 if it objected, 2 if it could not run
    """
    target = resolve_target(args.target, Path.cwd()).resolve()
    config = FileSolutionConfigRepository().get_policy_config_sync(target)

    if objections := target_objections(target, config):
        return _fail(objections)

    # Flushed, or the subprocess writes its output first and the
    # header lands underneath what it heads.
    print(f"doctrine: {target} (search_root {config.search_root})", flush=True)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *pytest_arguments(target)],
        env={**os.environ, "JULEE_TARGET": str(target)},
    )
    return 0 if completed.returncode == 0 else 1


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch.

    Returns:
        The exit status, so a caller can test this without a SystemExit
    """
    parser = argparse.ArgumentParser(prog="julee", description="julee tooling")
    subcommands = parser.add_subparsers(dest="group", required=True)

    doctrine = subcommands.add_parser(
        "doctrine", help="check a codebase against julee's doctrine"
    ).add_subparsers(dest="command", required=True)

    check = doctrine.add_parser(
        "verify", help="run every doctrine rule against a codebase"
    )
    check.add_argument(
        "--target",
        default=None,
        metavar="PATH",
        help="the codebase to verify (default: the working directory)",
    )
    check.set_defaults(handler=verify)

    args = parser.parse_args(argv)
    status: int = args.handler(args)
    return status


if __name__ == "__main__":
    sys.exit(main())

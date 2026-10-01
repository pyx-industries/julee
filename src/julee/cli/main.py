"""The ``julee`` command.

Two subcommands, both under ``julee doctrine``. ``verify`` runs every
rule: doctrine was runnable before it only as ``JULEE_TARGET=... pytest
--pyargs julee.core.doctrine`` — another project's tests, from a path
inside an installed package, with the target passed by environment
variable. It worked, and nobody would guess it (#192). ``census`` says
which parser family holds each declaration in the source, and which
declarations no family holds.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from julee.cli.census import as_json, as_text, exit_status
from julee.cli.verify import (
    pytest_arguments,
    resolve_target,
    target_objections,
)
from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.infrastructure.repositories.introspection.census import take_census
from julee.core.kits import viewpoint_slugs

__all__ = ["census", "main", "verify"]


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


def census(args: argparse.Namespace) -> int:
    """Take a census of a codebase's declarations and print it.

    Returns:
        0 if the census is complete and its readers agree, 1 if a file
        in scope could not be read or they disagree, 2 if it could not
        be taken
    """
    target = resolve_target(args.target, Path.cwd()).resolve()
    config = FileSolutionConfigRepository().get_policy_config_sync(target)

    if objections := target_objections(target, config):
        return _fail(objections)

    # target_objections has refused a missing search_root already.
    search_root = config.search_root or ""
    taken = take_census(
        target,
        search_root,
        FilesystemBoundedContextRepository(
            target, search_root, viewpoint_slugs(target)
        ),
    )
    sys.stdout.write(as_json(taken) if args.format == "json" else as_text(taken))
    return exit_status(taken)


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

    count = doctrine.add_parser(
        "census",
        help="say which parser family holds each declaration in a codebase",
    )
    count.add_argument(
        "--target",
        default=None,
        metavar="PATH",
        help="the codebase to read (default: the working directory)",
    )
    count.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="text for a person, or json carrying every declaration",
    )
    count.set_defaults(handler=census)

    args = parser.parse_args(argv)
    status: int = args.handler(args)
    return status


if __name__ == "__main__":
    sys.exit(main())

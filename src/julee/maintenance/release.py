#!/usr/bin/env python3
"""
Release preparation and tagging script.

Usage:
    uv run python -m julee.maintenance.release prepare X.Y.Z [--message-file FILE]
    uv run python -m julee.maintenance.release tag X.Y.Z

The parts that decide something — what the commit says, which version a
file claims, what to tell the operator next — are separate functions that
take their inputs and return a value. The parts that change the world go
through ``runner``, which a test replaces. That split is why this module
has tests at all: every bug it has had was in the deciding, and every one
of them shipped because the deciding could only be exercised by cutting a
real release.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

Runner = Callable[..., "subprocess.CompletedProcess[str]"]
"""What runs a command. Real releases use :func:`run`; tests pass a fake."""

PYPROJECT_VERSION = r'^version\s*=\s*"[^"]*"'
"""Where pyproject.toml keeps the version, for reading and for writing."""

INIT_VERSION = r'^__version__\s*=\s*"[^"]*"'
"""Where a package __init__.py keeps it."""

VERSION_DECLARATION = "__version__"
"""What marks an __init__.py as the one holding the project's version."""


def run(
    cmd: str, check: bool = True, capture: bool = True
) -> "subprocess.CompletedProcess[str]":
    """Run a shell command."""
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {cmd}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result


def die(message: str) -> None:
    """Report and stop."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def commit_message(version: str, release_notes: str | None = None) -> str:
    """The release commit's message.

    ``Release 0.6.1``, matching every release commit in this repository's
    history. It read ``release: v0.6.1`` until #258 — a conventional-commit
    prefix, which this project does not use. The tool and the repository
    disagreed, the repository was right, and the disagreement was settled
    by hand on every release rather than here.

    Args:
        version: The version being released
        release_notes: Body text, if the caller supplied a message file

    Returns:
        The full commit message, subject and body
    """
    subject = f"Release {version}"
    return f"{subject}\n\n{release_notes}" if release_notes else subject


def tag_command(version: str) -> str:
    """What to run once the release PR is merged.

    Printed rather than run, because the tag belongs on the merge commit
    and only a human knows when that exists.
    """
    return f"uv run python -m julee.maintenance.release tag {version}"


def version_in_file(file_path: Path, pattern: str) -> str | None:
    """The version a file claims, or None if it claims none.

    Args:
        file_path: The file to read
        pattern: :data:`PYPROJECT_VERSION` or :data:`INIT_VERSION`

    Returns:
        The version string, or None if the file has no version line
    """
    if not file_path.exists():
        return None
    match = re.search(pattern, file_path.read_text(), flags=re.MULTILINE)
    if match is None:
        return None
    quoted = re.search(r'"([^"]*)"', match.group(0))
    return quoted.group(1) if quoted else None


def get_repo_root(runner: Runner = run) -> Path:
    """Get the repository root directory."""
    result = runner("git rev-parse --show-toplevel")
    return Path(result.stdout.strip())


def get_package_init(repo_root: Path) -> Path | None:
    """The one ``__init__.py`` under ``src/`` that declares ``__version__``.

    A package is a directory holding an ``__init__.py``. That is the
    whole of the test, and it has to be, because ``src/`` holds
    directories that are not packages: ``julee.egg-info`` is the one
    that mattered. Counting it made ``len(packages) != 1`` and this
    function returned None — quietly — so four releases shipped with
    ``__version__`` left behind, and #262's loud failure never got the
    chance to fire because nothing called it.

    Several versioned packages is a repository whose version does not
    live in one file, which is a real arrangement (julee-kits) and not
    this tool's job. ``prepare`` says so rather than passing over it.
    """
    src_dir = repo_root / "src"
    if not src_dir.exists():
        return None
    versioned = [
        init
        for package in sorted(src_dir.iterdir())
        if package.is_dir() and not package.name.startswith("_")
        if (init := package / "__init__.py").exists()
        if VERSION_DECLARATION in init.read_text()
    ]
    return versioned[0] if len(versioned) == 1 else None


def version_claims(repo_root: Path) -> dict[Path, str]:
    """Every file in the tree that states the project's version.

    What the tool checks its own work against. Each bug this module has
    had was a file it meant to update and did not, and each was found by
    a human noticing afterwards — or, four times, not noticing.

    Returns:
        The version each file claims, by path. A file that claims none
        is left out.
    """
    claims = {}
    pyproject = repo_root / "pyproject.toml"
    if version := version_in_file(pyproject, PYPROJECT_VERSION):
        claims[pyproject] = version

    # Every __init__.py under src/, not the one get_package_init picks.
    # Sharing that logic would have made this check blind in exactly the
    # direction it needs to see: the bug was get_package_init choosing
    # nothing, and a check built on it would have found nothing to
    # disagree with and passed.
    src_dir = repo_root / "src"
    if src_dir.exists():
        for package in sorted(src_dir.iterdir()):
            if not package.is_dir():
                continue
            init = package / "__init__.py"
            if version := version_in_file(init, INIT_VERSION):
                claims[init] = version
    return claims


def claims_disagreeing_with(version: str, claims: dict[Path, str]) -> list[str]:
    """Files still claiming something other than the version being cut.

    Args:
        version: The version the release is for
        claims: What each file says, from :func:`version_claims`

    Returns:
        One sentence per file that was not brought along
    """
    return [
        f"{path} still claims {claimed}, not {version}"
        for path, claimed in sorted(claims.items())
        if claimed != version
    ]


def validate_version(version: str) -> None:
    """Validate version string format."""
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        die(f"Invalid version format '{version}'. Expected X.Y.Z")


def validate_git_state(require_master: bool = True, runner: Runner = run) -> None:
    """Validate git working tree is clean and on correct branch."""
    # Check for uncommitted changes
    result = runner("git status --porcelain")
    if result.stdout.strip():
        die("Working tree has uncommitted changes")

    if require_master:
        # Check we're on master
        result = runner("git branch --show-current")
        branch = result.stdout.strip()
        if branch not in ("master", "main"):
            die(f"Must be on master or main branch, currently on '{branch}'")

        # Check we're up to date with remote
        runner("git fetch origin")
        result = runner(
            "git rev-list HEAD...origin/master --count 2>/dev/null "
            "|| git rev-list HEAD...origin/main --count",
            check=False,
        )
        if result.stdout.strip() != "0":
            die("Branch is not up to date with remote")


def update_version_in_file(
    file_path: Path, version: str, pattern: str, replacement: str
) -> None:
    """Update version string in a file, or stop.

    A failure here used to print WARNING and carry on, which is how
    ``src/julee/__init__.py`` sat four releases behind ``pyproject.toml``
    without anyone being told. A version bump that does not bump is not a
    warning; it is the one thing this command exists to do.
    """
    content = file_path.read_text()
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    if content == new_content:
        die(f"No version replacement made in {file_path} — pattern did not match")
    file_path.write_text(new_content)


def prepare(
    version: str,
    message_file: Path | None = None,
    runner: Runner = run,
    repo_root: Path | None = None,
) -> None:
    """Prepare a release: create branch, update versions, push, create PR."""
    validate_version(version)
    validate_git_state(require_master=True, runner=runner)

    # Read release notes if provided
    release_notes = None
    if message_file:
        if not message_file.exists():
            die(f"Message file not found: {message_file}")
        release_notes = message_file.read_text().strip()

    if repo_root is None:
        repo_root = get_repo_root(runner)
    branch_name = f"release/v{version}"

    # Create release branch
    print(f"Creating branch {branch_name}...")
    runner(f"git checkout -b {branch_name}")

    # Update pyproject.toml
    pyproject = repo_root / "pyproject.toml"
    print(f"Updating {pyproject}...")
    update_version_in_file(
        pyproject,
        version,
        PYPROJECT_VERSION,
        f'version = "{version}"',
    )

    # Update __init__.py if it exists with __version__
    init_file = get_package_init(repo_root)
    if init_file:
        print(f"Updating {init_file}...")
        update_version_in_file(
            init_file,
            version,
            INIT_VERSION,
            f'__version__ = "{version}"',
        )
    else:
        # Said out loud. This skipped silently until #266, and the four
        # releases that shipped a stale __version__ each printed nothing
        # at all about it.
        print("No single __init__.py under src/ declares __version__; skipping.")

    # Check the work before committing it rather than after publishing it.
    if disagreements := claims_disagreeing_with(version, version_claims(repo_root)):
        die(
            "The version bump did not reach every file:\n  "
            + "\n  ".join(disagreements)
        )

    # The lockfile names the project's own version, so it is part of the
    # bump rather than a consequence of it. Leaving it out meant every
    # release commit before #258 was completed by hand, and a release that
    # forgot still passed make check.
    print("Updating uv.lock...")
    runner("uv lock")

    # Commit with release notes or default message
    print("Committing version bump...")
    message = commit_message(version, release_notes)

    # Use a temp file for the commit message to handle multiline properly
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(message)
        commit_msg_file = f.name
    try:
        runner(f'git add -A && git commit -F "{commit_msg_file}"')
    finally:
        Path(commit_msg_file).unlink()

    # Push
    print(f"Pushing {branch_name}...")
    runner(f"git push -u origin {branch_name}")

    # Create PR with release notes as body
    print("Creating pull request...")
    pr_body = release_notes if release_notes else f"Bump version to {version}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(pr_body)
        pr_body_file = f.name
    try:
        result = runner(
            f'gh pr create --title "Release v{version}" --body-file "{pr_body_file}"',
            check=False,
        )
    finally:
        Path(pr_body_file).unlink()

    if result.returncode != 0:
        print(f"\nTo create PR manually:\n  gh pr create --title 'Release v{version}'")

    print(f"\nRelease branch ready. After PR is merged, run:\n  {tag_command(version)}")


def tag(
    version: str,
    runner: Runner = run,
    repo_root: Path | None = None,
) -> None:
    """Tag a release after PR is merged."""
    validate_version(version)

    # Checkout master and pull
    print("Checking out master...")
    runner("git checkout master || git checkout main")
    runner("git pull")

    validate_git_state(require_master=True, runner=runner)

    if repo_root is None:
        repo_root = get_repo_root(runner)

    # The version asked for has to be the version master is actually at.
    # Without this, tagging the wrong number puts v0.7.0 on the commit that
    # released 0.6.1 — a tag pointing at the wrong commit, which looks
    # entirely normal until someone installs it.
    declared = version_in_file(repo_root / "pyproject.toml", PYPROJECT_VERSION)
    if declared is None:
        die(f"No version found in {repo_root / 'pyproject.toml'}")
    if declared != version:
        die(
            f"master is at version {declared}, not {version}. "
            f"Merge the release PR for {version} first, or tag {declared}"
        )

    tag_name = f"v{version}"

    # Check tag doesn't already exist
    result = runner(f"git tag -l {tag_name}")
    if result.stdout.strip():
        die(f"Tag {tag_name} already exists")

    # Create and push tag
    print(f"Creating tag {tag_name}...")
    runner(f"git tag {tag_name}")
    print(f"Pushing tag {tag_name}...")
    runner(f"git push origin {tag_name}")

    print(f"\nRelease {tag_name} tagged and pushed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Release preparation and tagging script"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # prepare subcommand
    prepare_parser = subparsers.add_parser(
        "prepare", help="Create release branch and PR"
    )
    prepare_parser.add_argument("version", help="Version number (X.Y.Z)")
    prepare_parser.add_argument(
        "--message-file",
        "-m",
        type=Path,
        help="File containing release notes for commit message and PR body",
    )

    # tag subcommand
    tag_parser = subparsers.add_parser("tag", help="Tag after PR is merged")
    tag_parser.add_argument("version", help="Version number (X.Y.Z)")

    args = parser.parse_args()

    if args.command == "prepare":
        prepare(args.version, args.message_file)
    elif args.command == "tag":
        tag(args.version)


if __name__ == "__main__":
    main()

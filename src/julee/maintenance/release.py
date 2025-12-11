#!/usr/bin/env python3
"""
Release preparation and tagging script.

Usage:
    release.py prepare X.Y.Z [--message-file FILE]  # Create release branch and PR
    release.py tag X.Y.Z                            # Tag after PR is merged
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {cmd}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result


def get_repo_root() -> Path:
    """Get the repository root directory."""
    result = run("git rev-parse --show-toplevel")
    return Path(result.stdout.strip())


def get_package_init(repo_root: Path) -> Path | None:
    """Find __init__.py with __version__ in src/ directory."""
    src_dir = repo_root / "src"
    if not src_dir.exists():
        return None
    packages = [p for p in src_dir.iterdir() if p.is_dir() and not p.name.startswith("_")]
    if len(packages) != 1:
        # Multiple packages (bounded contexts) - no single __init__.py to update
        return None
    init_file = packages[0] / "__init__.py"
    if init_file.exists() and "__version__" in init_file.read_text():
        return init_file
    return None


def validate_version(version: str) -> None:
    """Validate version string format."""
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        print(f"ERROR: Invalid version format '{version}'. Expected X.Y.Z", file=sys.stderr)
        sys.exit(1)


def validate_git_state(require_master: bool = True) -> None:
    """Validate git working tree is clean and on correct branch."""
    # Check for uncommitted changes
    result = run("git status --porcelain")
    if result.stdout.strip():
        print("ERROR: Working tree has uncommitted changes", file=sys.stderr)
        sys.exit(1)

    if require_master:
        # Check we're on master
        result = run("git branch --show-current")
        branch = result.stdout.strip()
        if branch not in ("master", "main"):
            print(f"ERROR: Must be on master or main branch, currently on '{branch}'", file=sys.stderr)
            sys.exit(1)

        # Check we're up to date with remote
        run("git fetch origin")
        result = run("git rev-list HEAD...origin/master --count 2>/dev/null || git rev-list HEAD...origin/main --count", check=False)
        if result.stdout.strip() != "0":
            print("ERROR: Branch is not up to date with remote", file=sys.stderr)
            sys.exit(1)


def update_version_in_file(file_path: Path, version: str, pattern: str, replacement: str) -> None:
    """Update version string in a file."""
    content = file_path.read_text()
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    if content == new_content:
        print(f"WARNING: No version replacement made in {file_path}", file=sys.stderr)
    file_path.write_text(new_content)


def prepare(version: str, message_file: Path | None = None) -> None:
    """Prepare a release: create branch, update versions, push, create PR."""
    validate_version(version)
    validate_git_state(require_master=True)

    # Read release notes if provided
    release_notes = None
    if message_file:
        if not message_file.exists():
            print(f"ERROR: Message file not found: {message_file}", file=sys.stderr)
            sys.exit(1)
        release_notes = message_file.read_text().strip()

    repo_root = get_repo_root()
    branch_name = f"release/v{version}"

    # Create release branch
    print(f"Creating branch {branch_name}...")
    run(f"git checkout -b {branch_name}")

    # Update pyproject.toml
    pyproject = repo_root / "pyproject.toml"
    print(f"Updating {pyproject}...")
    update_version_in_file(
        pyproject,
        version,
        r'^version\s*=\s*"[^"]*"',
        f'version = "{version}"',
    )

    # Update __init__.py if it exists with __version__
    init_file = get_package_init(repo_root)
    if init_file:
        print(f"Updating {init_file}...")
        update_version_in_file(
            init_file,
            version,
            r'^__version__\s*=\s*"[^"]*"',
            f'__version__ = "{version}"',
        )

    # Commit with release notes or default message
    print("Committing version bump...")
    if release_notes:
        commit_msg = f"release: v{version}\n\n{release_notes}"
    else:
        commit_msg = f"release: bump version to {version}"

    # Use a temp file for the commit message to handle multiline properly
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(commit_msg)
        commit_msg_file = f.name
    try:
        run(f'git add -A && git commit -F "{commit_msg_file}"')
    finally:
        Path(commit_msg_file).unlink()

    # Push
    print(f"Pushing {branch_name}...")
    run(f"git push -u origin {branch_name}")

    # Create PR with release notes as body
    print("Creating pull request...")
    pr_body = release_notes if release_notes else f"Bump version to {version}"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(pr_body)
        pr_body_file = f.name
    try:
        result = run(
            f'gh pr create --title "Release v{version}" --body-file "{pr_body_file}"',
            check=False,
        )
    finally:
        Path(pr_body_file).unlink()

    if result.returncode != 0:
        print(f"\nTo create PR manually:\n  gh pr create --title 'Release v{version}'")

    print(f"\nRelease branch ready. After PR is merged, run:\n  ./maintenance/release.py tag {version}")


def tag(version: str) -> None:
    """Tag a release after PR is merged."""
    validate_version(version)

    # Checkout master and pull
    print("Checking out master...")
    run("git checkout master || git checkout main")
    run("git pull")

    validate_git_state(require_master=True)

    tag_name = f"v{version}"

    # Check tag doesn't already exist
    result = run(f"git tag -l {tag_name}")
    if result.stdout.strip():
        print(f"ERROR: Tag {tag_name} already exists", file=sys.stderr)
        sys.exit(1)

    # Create and push tag
    print(f"Creating tag {tag_name}...")
    run(f"git tag {tag_name}")
    print(f"Pushing tag {tag_name}...")
    run(f"git push origin {tag_name}")

    print(f"\nRelease {tag_name} tagged and pushed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Release preparation and tagging script")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # prepare subcommand
    prepare_parser = subparsers.add_parser("prepare", help="Create release branch and PR")
    prepare_parser.add_argument("version", help="Version number (X.Y.Z)")
    prepare_parser.add_argument(
        "--message-file", "-m",
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

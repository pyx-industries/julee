#!/usr/bin/env python3
"""
Release preparation and tagging script.

Usage:
    uv run python -m julee.maintenance.release notes [X.Y.Z]
    uv run python -m julee.maintenance.release prepare X.Y.Z [--message-file FILE]
    uv run python -m julee.maintenance.release prepare X.Y.Z --edit
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
import os
import random
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Sequence
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


# =============================================================================
# Drafting release notes (#39)
# =============================================================================

ADJECTIVES = (
    "scheming",
    "nefarious",
    "unrepentant",
    "gleeful",
    "feckless",
    "conniving",
    "impertinent",
    "swaggering",
    "devious",
    "brazen",
)
"""Mischievous, so a draft in /tmp is easy to spot and fun to say."""

PHYSICISTS = (
    "einstein",
    "bohr",
    "heisenberg",
    "schrodinger",
    "dirac",
    "pauli",
    "planck",
    "born",
    "debroglie",
    "feynman",
)
"""Quantum, Einstein to Feynman."""

NOUNS = (
    "kumquat",
    "trombone",
    "hovercraft",
    "pemmican",
    "wombat",
    "spatula",
    "gazebo",
    "kerfuffle",
    "bandicoot",
    "waffle",
)
"""Absurd, for the same reason."""

SEMVER_GUIDANCE = {
    "patch": (
        "A patch fixes bugs and small improvements without adding features "
        "or breaking compatibility. Keep it brief — a sentence or two is "
        "fine."
    ),
    "minor": (
        "A minor adds features while staying backward compatible. Be "
        "thorough: this may be the first a reader hears of them."
    ),
    "major": (
        "A major may break backward compatibility. Be thorough and "
        "specific — a reader needs to understand the impact before "
        "upgrading."
    ),
}
"""What each kind of release is for, and the tone that suits it.

Written into the draft as an HTML comment, for the author to read and
delete. Guidance that lives in a wiki is guidance nobody reads at the
moment they need it.
"""


VERSION_TAG = re.compile(r"^v?\d+(\.\d+)*$")
"""What a tag naming a version looks like.

``git tag -l`` answers with every tag a repository has, and not all of
them name releases: this one carries ``archive/docs_architecture_domain``.
Reading those as versions is how the first run of ``notes`` fell over.
"""


def version_tags(tags: Iterable[str]) -> list[str]:
    """The tags that name a version, without their leading "v".

    Args:
        tags: Every tag, as git reports them

    Returns:
        Versions, sorted oldest first, without duplicates
    """
    return sorted(
        {tag.lstrip("v") for tag in tags if VERSION_TAG.match(tag)},
        key=version_key,
    )


def version_key(version: str) -> tuple[int, ...]:
    """A version as numbers, for ordering.

    Args:
        version: "1.2.3", with or without a leading "v"

    Returns:
        Its parts as integers
    """
    return tuple(int(part) for part in version.lstrip("v").split("."))


def previous_version(new_version: str, tags: Iterable[str]) -> str | None:
    """The version a release follows, which is not always the highest.

    Releasing 0.3.8 as a maintenance backport, with 1.1.3 already out,
    follows 0.3.7 and not 1.1.3. So the new version is slotted into the
    sorted list and the one before it is the answer, rather than taking
    the maximum.

    Args:
        new_version: The version about to be released
        tags: Existing tags, with or without a leading "v"

    Returns:
        The version this one follows, or None if it is the first
    """
    versions = sorted(set(version_tags(tags)) | {new_version}, key=version_key)
    position = versions.index(new_version)
    return versions[position - 1] if position else None


def release_kind(new_version: str, previous: str | None) -> str:
    """Which of patch, minor or major this release is.

    Args:
        new_version: The version about to be released
        previous: What it follows, or None for a first release

    Returns:
        "major", "minor", "patch", or "first" when there is nothing to
        compare against
    """
    if previous is None:
        return "first"
    was, now = version_key(previous), version_key(new_version)
    if now[0] != was[0]:
        return "major"
    if len(now) > 1 and len(was) > 1 and now[1] != was[1]:
        return "minor"
    return "patch"


def next_versions(current: str | None) -> dict[str, str]:
    """What a patch, minor or major from here would be called.

    Args:
        current: The highest released version, or None

    Returns:
        Kind to version. A first release offers only a patch, because
        there is nothing to increment a minor or major from.
    """
    if current is None:
        return {"patch": "0.0.1"}
    major, minor, patch = (version_key(current) + (0, 0))[:3]
    return {
        "patch": f"{major}.{minor}.{patch + 1}",
        "minor": f"{major}.{minor + 1}.0",
        "major": f"{major + 1}.0.0",
    }


def draft_name(kind: str, version: str, words: Sequence[str]) -> str:
    """What to call a draft file.

    Args:
        kind: "release" or "changelog"
        version: The version being drafted
        words: Three words, from :func:`cute_words`

    Returns:
        A filename, e.g. release-0.2.0-scheming-heisenberg-kumquat.md
    """
    return f"{kind}-{version}-{'-'.join(words)}.md"


def cute_words(choose: Callable[[Sequence[str]], str]) -> tuple[str, str, str]:
    """Three words for a draft filename.

    Args:
        choose: Picks one of a sequence; ``random.choice`` in a release

    Returns:
        An adjective, a physicist and a noun
    """
    return choose(ADJECTIVES), choose(PHYSICISTS), choose(NOUNS)


def notes_template(version: str, previous: str | None, subjects: Iterable[str]) -> str:
    """A draft for an author to cut down.

    The commits are listed rather than summarised, because a summary a
    script writes is one an author has to check before trusting, and
    checking it costs more than writing the summary would have.

    Args:
        version: The version being released
        previous: What it follows, or None
        subjects: Commit subjects since the previous release

    Returns:
        Markdown, with the guidance as an HTML comment to delete
    """
    kind = release_kind(version, previous)
    since = f"since {previous}" if previous else "in the first release"
    guidance = SEMVER_GUIDANCE.get(kind, SEMVER_GUIDANCE["patch"])
    listed = "\n".join(f"- {subject}" for subject in subjects) or "- (none)"
    return (
        f"<!-- {version} is a {kind} release. {guidance}\n\n"
        f"     Write what a reader needs in order to decide whether to "
        f"upgrade.\n"
        f"     Delete this comment, and the commit list once you have "
        f"used it. -->\n"
        f"\n"
        f"## Commits {since}\n"
        f"\n"
        f"{listed}\n"
    )


def changelog_document(version: str, releases: Iterable[tuple[str, str]]) -> str:
    """The notes a minor or major gathers up, as context for writing it.

    A patch is the sum of the commits since the last patch. A minor is
    the culmination of every patch since the last minor, and should
    summarise them rather than repeat them — which needs them to hand.

    Args:
        version: The version being drafted
        releases: Version and its notes, oldest first

    Returns:
        Markdown, to read beside the draft rather than to publish
    """
    sections = [f"## {released}\n\n{notes.strip()}\n" for released, notes in releases]
    body = "\n".join(sections) or "(no intermediate releases)\n"
    return (
        f"<!-- Context for writing {version}, not something to publish.\n"
        f"     These are the releases it gathers up. Summarise them; the\n"
        f"     reader of {version} has not read any of them. -->\n"
        f"\n"
        f"{body}"
    )


def gathered_releases(version: str, tags: Iterable[str]) -> list[str]:
    """The releases a minor or major culminates, oldest first.

    A minor 0.12.0 gathers the whole 0.11 line — 0.11.0 and every patch
    after it — because that is what it is the culmination of. The
    previous minor is included, not excluded: its notes are the ones a
    reader of 0.12.0 has most likely not seen.

    A major gathers every release since the previous major, by the same
    reasoning one rank up.

    A patch gathers nothing. It is the sum of the commits it carries,
    which the draft already lists.

    Args:
        version: The version being drafted
        tags: Existing tags

    Returns:
        Versions from the previous release of the same rank, inclusive,
        up to but not including this one
    """
    versions = version_tags(tags)
    here = version_key(version)
    major, minor = (here + (0, 0))[:2]

    if len(here) > 2 and here[2] != 0:
        return []

    def is_same_rank(candidate: tuple[int, ...]) -> bool:
        padded = candidate + (0, 0)
        if minor == 0:
            return padded[1] == 0 and padded[2] == 0
        return padded[0] == major and padded[2] == 0

    earlier = [
        released
        for released in versions
        if version_key(released) < here and is_same_rank(version_key(released))
    ]
    if not earlier:
        return [v for v in versions if version_key(v) < here]

    floor = version_key(earlier[-1])
    return [released for released in versions if floor <= version_key(released) < here]


def existing_tags(runner: Runner = run) -> list[str]:
    """Every version tag in the repository.

    Args:
        runner: What runs the command

    Returns:
        Tag names, unordered
    """
    result = runner("git tag -l", check=False)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def commit_subjects(since: str | None, runner: Runner = run) -> list[str]:
    """The subject line of each commit since a tag.

    Args:
        since: The tag to start after, or None for the whole history
        runner: What runs the command

    Returns:
        Subjects, newest first
    """
    span = f"v{since}..HEAD" if since else "HEAD"
    result = runner(f"git log --no-merges --format=%s {span}", check=False)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def notes_of(version: str, runner: Runner = run) -> str:
    """What a released version said about itself.

    Read from the release commit's body, which is where prepare put the
    notes it was given.

    Args:
        version: The released version
        runner: What runs the command

    Returns:
        The notes, or an empty string if the tag says nothing
    """
    result = runner(f"git log -1 --format=%b v{version}", check=False)
    return result.stdout.strip()


def write_drafts(
    version: str,
    directory: Path,
    runner: Runner = run,
    choose: Callable[[Sequence[str]], str] = random.choice,
) -> tuple[Path, Path | None]:
    """Write a draft for this release, and its context if it needs one.

    Args:
        version: The version being drafted
        directory: Where to put the files
        runner: What runs git
        choose: Picks a word for the filename

    Returns:
        The draft's path, and the changelog's if one was written
    """
    tags = existing_tags(runner)
    previous = previous_version(version, tags)
    words = cute_words(choose)

    draft = directory / draft_name("release", version, words)
    draft.write_text(
        notes_template(version, previous, commit_subjects(previous, runner)),
        encoding="utf-8",
    )

    # A patch is the sum of the commits it carries. A minor or major is
    # the culmination of the releases since the last one of its rank,
    # and cannot be written well without them to hand.
    if release_kind(version, previous) not in {"minor", "major"}:
        return draft, None

    gathered = gathered_releases(version, tags)
    changelog = directory / draft_name("changelog", version, words)
    changelog.write_text(
        changelog_document(
            version, [(each, notes_of(each, runner)) for each in gathered]
        ),
        encoding="utf-8",
    )
    return draft, changelog


def choose_version(current: str | None, ask: Callable[[str], str]) -> str:
    """Which version to draft, asked interactively.

    Args:
        current: The highest released version, or None
        ask: Prompts and returns what was typed

    Returns:
        The version to draft

    Raises:
        ValueError: If the answer names no option
    """
    offered = next_versions(current)
    lines = [
        f"  {number}. {kind:6} -> {candidate}"
        for number, (kind, candidate) in enumerate(offered.items(), start=1)
    ]
    lines.append(f"  {len(offered) + 1}. other  -> specify version")
    answer = ask("\n".join(lines) + "\n\nWhich release? ").strip()

    candidates = list(offered.values())
    if answer.isdigit() and 1 <= int(answer) <= len(candidates):
        return candidates[int(answer) - 1]
    if answer.isdigit() and int(answer) == len(candidates) + 1:
        answer = ask("Version: ").strip()
    validate_version(answer)
    return answer


def notes(
    version: str | None = None,
    runner: Runner = run,
    directory: Path | None = None,
    ask: Callable[[str], str] = input,
) -> Path:
    """Write a draft of the release notes for an author to cut down.

    Named rather than generated into the commit, because notes a script
    writes are notes an author has to check, and checking costs more
    than writing would have. What this saves is the gathering: which
    commits, which previous release, what kind of release this is.

    Args:
        version: The version to draft, or None to be asked
        runner: What runs git
        directory: Where to write, defaulting to a temporary directory
        ask: Prompts, when no version was named

    Returns:
        The draft's path
    """
    tags = existing_tags(runner)
    if version is None:
        released = version_tags(tags)
        if not released:
            print("No existing tags found.\n")
        version = choose_version(released[-1] if released else None, ask)
    validate_version(version)

    draft, changelog = write_drafts(
        version, directory or Path(tempfile.gettempdir()), runner
    )
    print(f"Draft:     {draft}")
    if changelog:
        print(f"Context:   {changelog}")
        print("\nRead the context, then write the draft so it reads beside it.")
    print(
        f"\nWhen it says what you mean:\n  make release-prepare "
        f"VERSION={version} NOTES={draft}"
    )
    return draft


def edited(path: Path, editor: str, runner: Runner = run) -> bool:
    """Open a draft, and say whether the author changed it.

    Git's rule: a commit message left exactly as the template gave it
    is taken as "I have not written this yet", and the operation stops.
    A release nobody described is worse than no release.

    Args:
        path: The draft to open
        editor: The command to open it with
        runner: What runs the command

    Returns:
        True if the file differs from what was written
    """
    before = path.read_text(encoding="utf-8")
    runner(f"{editor} {path}", capture=False)
    return path.read_text(encoding="utf-8") != before


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
    prepare_parser.add_argument(
        "--edit",
        "-e",
        action="store_true",
        help="Draft the notes, open $EDITOR, and stop if nothing was written",
    )

    # notes subcommand
    notes_parser = subparsers.add_parser(
        "notes", help="Draft release notes for a version"
    )
    notes_parser.add_argument(
        "version", nargs="?", help="Version number (X.Y.Z); asks if omitted"
    )

    # tag subcommand
    tag_parser = subparsers.add_parser("tag", help="Tag after PR is merged")
    tag_parser.add_argument("version", help="Version number (X.Y.Z)")

    args = parser.parse_args()

    if args.command == "prepare":
        message_file = args.message_file
        if args.edit:
            message_file = notes(args.version)
            editor = os.environ.get("EDITOR", "emacs")
            if not edited(message_file, editor):
                die(
                    f"{message_file} is unchanged, so the release says "
                    f"nothing. Nothing was prepared."
                )
        prepare(args.version, message_file)
    elif args.command == "notes":
        notes(args.version)
    elif args.command == "tag":
        tag(args.version)


if __name__ == "__main__":
    main()

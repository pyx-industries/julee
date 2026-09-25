"""Tests for the release tooling.

Every bug this module has had was a decision it got wrong — what the
commit says, which files the bump touches, what to tell the operator
next — and every one of them shipped because the only way to exercise a
decision was to cut a real release. So the decisions are functions that
return values, the commands go through an injected runner, and nothing
here runs git.

The fake runner records what it was asked to do and answers plausibly.
That is enough to pin the two failures that actually happened: a commit
message with the wrong shape, and a step that was simply missing.
"""

import subprocess
from pathlib import Path

import pytest

from julee.maintenance.release import (
    INIT_VERSION,
    PYPROJECT_VERSION,
    claims_disagreeing_with,
    commit_message,
    get_package_init,
    prepare,
    tag,
    tag_command,
    update_version_in_file,
    validate_git_state,
    validate_version,
    version_claims,
    version_in_file,
)

pytestmark = pytest.mark.unit


class FakeRunner:
    """Records commands instead of running them.

    Answers whatever a caller needs to get past its checks: a clean tree,
    master, in step with the remote. A test that wants a different world
    overrides one answer rather than building a git repository.
    """

    def __init__(self, **answers: str) -> None:
        """Start with the answers of a repository ready to release."""
        self.commands: list[str] = []
        self.answers = {
            "git status --porcelain": "",
            "git branch --show-current": "master",
            "git rev-list": "0",
            "git rev-parse --show-toplevel": "/repo",
            "git tag -l": "",
            **answers,
        }

    def __call__(
        self, cmd: str, check: bool = True, capture: bool = True
    ) -> "subprocess.CompletedProcess[str]":
        """Record the command and answer it."""
        self.commands.append(cmd)
        stdout = ""
        for prefix, answer in self.answers.items():
            if cmd.startswith(prefix):
                stdout = answer
                break
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    def ran(self, fragment: str) -> bool:
        """Whether any command contained this."""
        return any(fragment in cmd for cmd in self.commands)

    def index_of(self, fragment: str) -> int:
        """Where a command ran, for asserting on order."""
        for i, cmd in enumerate(self.commands):
            if fragment in cmd:
                return i
        raise AssertionError(f"no command contained {fragment!r}: {self.commands}")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repository root with a pyproject and a package __init__."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "julee"\nversion = "0.6.1"\n'
    )
    package = tmp_path / "src" / "julee"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Julee."""\n\n__version__ = "0.6.1"\n')
    return tmp_path


# =============================================================================
# What the commit says
# =============================================================================


def test_the_subject_is_how_the_history_spells_it() -> None:
    """Release 0.6.1, matching every release commit in this repository.

    It read "release: v0.6.1" until #258 — a conventional-commit prefix
    this project does not use.
    """
    assert commit_message("0.6.1") == "Release 0.6.1"


def test_the_subject_carries_no_conventional_commit_prefix() -> None:
    message = commit_message("0.6.1", "Some notes.")

    assert not message.startswith("release:")
    assert message.splitlines()[0] == "Release 0.6.1"


def test_the_subject_has_no_v_before_the_number() -> None:
    """The tag is v0.6.1; the commit subject is not."""
    assert "v0.6.1" not in commit_message("0.6.1")


def test_release_notes_become_the_body_under_a_blank_line() -> None:
    message = commit_message("0.6.1", "Carries two fixes.")

    assert message == "Release 0.6.1\n\nCarries two fixes."


def test_a_release_without_notes_is_just_the_subject() -> None:
    """No body rather than a body saying nothing."""
    assert "\n" not in commit_message("0.6.1")


def test_the_subject_fits_the_fifty_character_guideline() -> None:
    """Linux kernel style, which this project follows."""
    assert len(commit_message("10.20.30").splitlines()[0]) <= 50


# =============================================================================
# What the operator is told to do next
# =============================================================================


def test_the_next_step_is_a_command_that_exists() -> None:
    """It named ./maintenance/release.py, which is not where this lives."""
    assert tag_command("0.6.1") == (
        "uv run python -m julee.maintenance.release tag 0.6.1"
    )


def test_the_next_step_does_not_name_a_path_that_moved() -> None:
    assert "./maintenance/release.py" not in tag_command("0.6.1")


# =============================================================================
# Reading a version out of a file
# =============================================================================


def test_a_pyproject_version_is_read(repo: Path) -> None:
    assert version_in_file(repo / "pyproject.toml", PYPROJECT_VERSION) == "0.6.1"


def test_an_init_version_is_read(repo: Path) -> None:
    init = repo / "src" / "julee" / "__init__.py"

    assert version_in_file(init, INIT_VERSION) == "0.6.1"


def test_a_missing_file_claims_no_version(tmp_path: Path) -> None:
    assert version_in_file(tmp_path / "absent.toml", PYPROJECT_VERSION) is None


def test_a_file_without_a_version_line_claims_none(tmp_path: Path) -> None:
    unversioned = tmp_path / "pyproject.toml"
    unversioned.write_text('[project]\nname = "julee"\n')

    assert version_in_file(unversioned, PYPROJECT_VERSION) is None


def test_a_dependency_pin_is_not_mistaken_for_the_version(tmp_path: Path) -> None:
    """The pattern is anchored, so an indented pin is not the project's own."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nversion = "0.6.1"\ndependencies = [\n    "version = 9.9.9",\n]\n'
    )

    assert version_in_file(pyproject, PYPROJECT_VERSION) == "0.6.1"


# =============================================================================
# Writing a version into a file
# =============================================================================


def test_a_version_is_replaced(repo: Path) -> None:
    pyproject = repo / "pyproject.toml"

    update_version_in_file(pyproject, "0.7.0", PYPROJECT_VERSION, 'version = "0.7.0"')

    assert version_in_file(pyproject, PYPROJECT_VERSION) == "0.7.0"


def test_a_bump_that_does_not_bump_stops_the_release(tmp_path: Path) -> None:
    """The bug that let __init__.py sit four releases behind pyproject.

    It printed WARNING and carried on, so a version bump that bumped
    nothing produced a release commit that looked entirely normal. A
    version bump failing to bump is not a warning.
    """
    unversioned = tmp_path / "pyproject.toml"
    unversioned.write_text('[project]\nname = "julee"\n')

    with pytest.raises(SystemExit):
        update_version_in_file(
            unversioned, "0.7.0", PYPROJECT_VERSION, 'version = "0.7.0"'
        )


def test_the_rest_of_the_file_is_left_alone(repo: Path) -> None:
    pyproject = repo / "pyproject.toml"

    update_version_in_file(pyproject, "0.7.0", PYPROJECT_VERSION, 'version = "0.7.0"')

    assert 'name = "julee"' in pyproject.read_text()


# =============================================================================
# Finding the package __init__
# =============================================================================


def test_the_package_init_is_found(repo: Path) -> None:
    assert get_package_init(repo) == repo / "src" / "julee" / "__init__.py"


def test_a_tree_with_no_src_has_no_package_init(tmp_path: Path) -> None:
    assert get_package_init(tmp_path) is None


def test_two_versioned_packages_mean_no_single_init(repo: Path) -> None:
    """Several bounded contexts, so no one file holds the version."""
    other = repo / "src" / "other"
    other.mkdir()
    (other / "__init__.py").write_text('__version__ = "0.6.1"\n')

    assert get_package_init(repo) is None


def test_a_directory_that_is_not_a_package_does_not_count(repo: Path) -> None:
    """src/julee.egg-info is a directory and was counted as a package.

    That made two, so the function returned None, so the version bump
    skipped __init__.py without a word. Four releases shipped claiming a
    version they were not (#266). Every release run has a build artifact
    sitting there, so this was not an edge case.
    """
    (repo / "src" / "julee.egg-info").mkdir()

    assert get_package_init(repo) == repo / "src" / "julee" / "__init__.py"


def test_a_package_without_a_version_does_not_make_it_ambiguous(repo: Path) -> None:
    """Only a package claiming a version is a candidate to hold it."""
    plain = repo / "src" / "plain"
    plain.mkdir()
    (plain / "__init__.py").write_text('"""No version here."""\n')

    assert get_package_init(repo) == repo / "src" / "julee" / "__init__.py"


def test_an_init_without_a_version_is_not_offered(tmp_path: Path) -> None:
    package = tmp_path / "src" / "julee"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Julee."""\n')

    assert get_package_init(tmp_path) is None


# =============================================================================
# Version format
# =============================================================================


@pytest.mark.parametrize("version", ["0.6.1", "1.0.0", "10.20.30"])
def test_a_three_part_version_is_accepted(version: str) -> None:
    validate_version(version)


@pytest.mark.parametrize("version", ["v0.6.1", "0.6", "0.6.1rc1", "", "0.6.1.2"])
def test_anything_else_is_refused(version: str) -> None:
    with pytest.raises(SystemExit):
        validate_version(version)


# =============================================================================
# What prepare actually does
# =============================================================================


def test_prepare_bumps_both_files_and_the_lockfile(repo: Path) -> None:
    """The three things a release commit has to contain.

    uv.lock was the one missing: the bump landed in pyproject.toml alone,
    make check passed anyway, and every release commit in the history was
    completed by hand afterwards.
    """
    runner = FakeRunner()

    prepare("0.7.0", runner=runner, repo_root=repo)

    assert version_in_file(repo / "pyproject.toml", PYPROJECT_VERSION) == "0.7.0"
    init = repo / "src" / "julee" / "__init__.py"
    assert version_in_file(init, INIT_VERSION) == "0.7.0"
    assert runner.ran("uv lock")


def test_the_lockfile_is_updated_before_the_commit(repo: Path) -> None:
    """Order matters: after the commit it would be a separate change."""
    runner = FakeRunner()

    prepare("0.7.0", runner=runner, repo_root=repo)

    assert runner.index_of("uv lock") < runner.index_of("git commit")


def test_prepare_commits_the_message_it_built(repo: Path) -> None:
    """Read back through the runner, since the file is deleted afterwards."""
    written: list[str] = []

    class ReadingRunner(FakeRunner):
        def __call__(
            self, cmd: str, check: bool = True, capture: bool = True
        ) -> "subprocess.CompletedProcess[str]":
            if "git commit -F" in cmd:
                path = cmd.split('git commit -F "')[1].rstrip('"')
                written.append(Path(path).read_text())
            return super().__call__(cmd, check, capture)

    prepare("0.7.0", runner=ReadingRunner(), repo_root=repo)

    assert written == ["Release 0.7.0"]


def test_release_notes_reach_the_commit(repo: Path, tmp_path: Path) -> None:
    written: list[str] = []

    class ReadingRunner(FakeRunner):
        def __call__(
            self, cmd: str, check: bool = True, capture: bool = True
        ) -> "subprocess.CompletedProcess[str]":
            if "git commit -F" in cmd:
                path = cmd.split('git commit -F "')[1].rstrip('"')
                written.append(Path(path).read_text())
            return super().__call__(cmd, check, capture)

    notes = tmp_path / "notes.md"
    notes.write_text("Carries two fixes.\n")

    prepare("0.7.0", notes, runner=ReadingRunner(), repo_root=repo)

    assert written == ["Release 0.7.0\n\nCarries two fixes."]


def test_prepare_branches_before_it_edits(repo: Path) -> None:
    """Otherwise the bump lands on master."""
    runner = FakeRunner()

    prepare("0.7.0", runner=runner, repo_root=repo)

    assert runner.index_of("git checkout -b release/v0.7.0") < runner.index_of(
        "git commit"
    )


def test_a_missing_message_file_stops_before_branching(repo: Path) -> None:
    runner = FakeRunner()

    with pytest.raises(SystemExit):
        prepare("0.7.0", Path("/no/such/notes.md"), runner=runner, repo_root=repo)

    assert not runner.ran("git checkout -b")


def test_prepare_refuses_a_dirty_tree(repo: Path) -> None:
    runner = FakeRunner(**{"git status --porcelain": " M somefile.py"})

    with pytest.raises(SystemExit):
        prepare("0.7.0", runner=runner, repo_root=repo)

    assert not runner.ran("git checkout -b")


def test_prepare_refuses_a_feature_branch(repo: Path) -> None:
    runner = FakeRunner(**{"git branch --show-current": "some-feature"})

    with pytest.raises(SystemExit):
        prepare("0.7.0", runner=runner, repo_root=repo)


# =============================================================================
# What tag actually does
# =============================================================================


def test_tag_tags_the_version_master_is_at(repo: Path) -> None:
    runner = FakeRunner()

    tag("0.6.1", runner=runner, repo_root=repo)

    assert runner.ran("git tag v0.6.1")
    assert runner.ran("git push origin v0.6.1")


def test_tag_refuses_a_version_master_is_not_at(repo: Path) -> None:
    """The failure this check exists for.

    Without it, tagging the wrong number puts v0.7.0 on the commit that
    released 0.6.1. Nothing looks wrong: the tag exists, CI is green, and
    the mismatch only surfaces when someone installs it.
    """
    runner = FakeRunner()

    with pytest.raises(SystemExit):
        tag("0.7.0", runner=runner, repo_root=repo)

    assert not runner.ran("git tag v0.7.0")


def test_tag_does_not_push_when_it_refuses(repo: Path) -> None:
    runner = FakeRunner()

    with pytest.raises(SystemExit):
        tag("0.7.0", runner=runner, repo_root=repo)

    assert not runner.ran("git push origin")


def test_tag_refuses_when_the_tag_already_exists(repo: Path) -> None:
    runner = FakeRunner(**{"git tag -l": "v0.6.1"})

    with pytest.raises(SystemExit):
        tag("0.6.1", runner=runner, repo_root=repo)

    assert not runner.ran("git push origin v0.6.1")


def test_tag_refuses_when_pyproject_names_no_version(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "julee"\n')
    runner = FakeRunner()

    with pytest.raises(SystemExit):
        tag("0.6.1", runner=runner, repo_root=tmp_path)


# =============================================================================
# Git state
# =============================================================================


def test_a_clean_master_in_step_with_the_remote_passes() -> None:
    validate_git_state(runner=FakeRunner())


def test_being_behind_the_remote_is_refused() -> None:
    runner = FakeRunner(**{"git rev-list": "3"})

    with pytest.raises(SystemExit):
        validate_git_state(runner=runner)


def test_main_counts_as_master() -> None:
    validate_git_state(runner=FakeRunner(**{"git branch --show-current": "main"}))


def test_a_branch_check_can_be_waived_but_a_dirty_tree_cannot() -> None:
    runner = FakeRunner(**{"git branch --show-current": "some-feature"})

    validate_git_state(require_master=False, runner=runner)

    dirty = FakeRunner(**{"git status --porcelain": " M x.py"})
    with pytest.raises(SystemExit):
        validate_git_state(require_master=False, runner=dirty)


# =============================================================================
# Checking the work
# =============================================================================


def test_every_file_that_claims_a_version_is_read(repo: Path) -> None:
    assert set(version_claims(repo)) == {
        repo / "pyproject.toml",
        repo / "src" / "julee" / "__init__.py",
    }


def test_a_tree_claiming_nothing_yields_nothing(tmp_path: Path) -> None:
    assert version_claims(tmp_path) == {}


def test_agreeing_claims_raise_no_objection() -> None:
    claims = {Path("pyproject.toml"): "0.7.0", Path("src/julee/__init__.py"): "0.7.0"}

    assert claims_disagreeing_with("0.7.0", claims) == []


def test_a_file_left_behind_is_objected_to() -> None:
    """The four-release drift, caught before the commit rather than after."""
    claims = {Path("pyproject.toml"): "0.7.0", Path("src/julee/__init__.py"): "0.6.1"}

    (objection,) = claims_disagreeing_with("0.7.0", claims)

    assert "src/julee/__init__.py" in objection
    assert "0.6.1" in objection


def test_the_objection_names_the_version_being_cut() -> None:
    """So the reader can see which way round the disagreement is."""
    (objection,) = claims_disagreeing_with("0.7.0", {Path("pyproject.toml"): "0.6.1"})

    assert "0.7.0" in objection


def test_prepare_bumps_the_init_with_a_build_artifact_present(repo: Path) -> None:
    """The regression, at the level it actually happened.

    Every real release runs in a tree that has been built, so src/ has
    an egg-info beside the package. That was enough to skip the bump.
    """
    (repo / "src" / "julee.egg-info").mkdir()

    prepare("0.7.0", runner=FakeRunner(), repo_root=repo)

    init = repo / "src" / "julee" / "__init__.py"
    assert version_in_file(init, INIT_VERSION) == "0.7.0"


def test_prepare_stops_when_a_file_is_left_behind(repo: Path) -> None:
    """The backstop, for the next way this goes wrong rather than this one.

    Two packages both claiming the version: get_package_init declines to
    choose, which is right, but the release would otherwise be cut with
    both files stale. prepare checks its own work before committing, so
    the release is not cut at all.

    The check reads every __init__.py under src/ rather than the one
    get_package_init picks. Sharing that logic would have made it blind
    in the one direction it has to see.
    """
    other = repo / "src" / "other"
    other.mkdir()
    (other / "__init__.py").write_text('__version__ = "0.6.1"\n')

    with pytest.raises(SystemExit):
        prepare("0.7.0", runner=FakeRunner(), repo_root=repo)


def test_the_check_sees_an_init_the_selection_passed_over(repo: Path) -> None:
    """The original bug, seen by the check that guards against it.

    get_package_init returned None because src/julee.egg-info counted as
    a package, so __init__.py was never bumped. A check built on the same
    selection would have found nothing to disagree with.
    """
    (repo / "src" / "julee" / "__init__.py").write_text('__version__ = "0.6.1"\n')
    (repo / "pyproject.toml").write_text('[project]\nversion = "0.7.0"\n')

    assert claims_disagreeing_with("0.7.0", version_claims(repo))

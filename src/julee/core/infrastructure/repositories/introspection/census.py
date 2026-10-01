"""Taking a census of a solution on disk.

Reads every Python file in scope under the search root, asks the class
parser for each bounded context's families, and hands both to
:func:`julee.core.census.census_of_context`. Source is read as text and
parsed; nothing of the solution is imported.

Scope is every ``.py`` file under the search root except three kinds:
test files, by the parser's own definition; anything under a directory
whose name begins with a dot; and anything git ignores. Everything else
is read, which includes a package's ``__init__.py``, though the class
parser reads no class out of one, and a file in a directory that is no
bounded context. The census is complete when every file in scope was
read.
"""

import os
import subprocess
from pathlib import Path

from julee.core.census import census_of_context, families_of
from julee.core.doctrine.resolution import module_name_for
from julee.core.infrastructure.repositories.introspection.bounded_context import (
    FilesystemBoundedContextRepository,
)
from julee.core.parsers.ast import (
    is_test_file,
    parse_bounded_context,
    unreadable_python_files,
)
from julee.core.parsers.declarations import declarations_in
from julee.core.values.census import (
    Census,
    ContextCensus,
    Declaration,
    Exclusion,
    PassedOver,
)
from julee.core.values.code_info import UnreadableFile

__all__ = ["take_census"]

HIDDEN = "hidden directory"
GIT_IGNORED = "git-ignored"
IN_THE_SEARCH_ROOT = "in the search root itself, beside the bounded contexts"


def take_census(
    project_root: Path,
    search_root: str,
    repo: FilesystemBoundedContextRepository,
) -> Census:
    """Read a solution's source and say which family holds each declaration.

    Args:
        project_root: The solution root, which paths are reported against
        search_root: Where its source lives, relative to that root
        repo: Discovery for the same root, which says what is a bounded
            context and why the rest is not

    Returns:
        The census
    """
    search_path = project_root / search_root

    def relative(path: Path) -> str:
        return path.relative_to(project_root).as_posix()

    files, exclusions = _files_in_scope(search_path, project_root)
    tests = [file for file in files if is_test_file(file)]
    in_scope = [file for file in files if not is_test_file(file)]

    declared: dict[Path, list[Declaration]] = {}
    unreadable: dict[str, UnreadableFile] = {}
    for file in in_scope:
        found, problem = _declarations_of(file, relative(file))
        if problem is not None:
            unreadable[problem.file] = problem
        else:
            declared[file] = found

    contexts: list[ContextCensus] = []
    claimed_files: set[Path] = set()
    for context in repo.discover_all():
        context_path = Path(context.path)
        own = [file for file in in_scope if context_path in file.parents]
        claimed_files.update(own)
        contexts.append(
            census_of_context(
                slug=context.slug,
                path=relative(context_path),
                declarations=[
                    declaration
                    for file in own
                    for declaration in declared.get(file, ())
                ],
                families=families_of(parse_bounded_context(context_path)),
            )
        )
        # What the class parser could not load, where its loader is
        # stricter than Python's own parser.
        for skipped in unreadable_python_files(context_path, relative_to=project_root):
            unreadable.setdefault(Path(skipped.file).as_posix(), skipped)

    return Census(
        search_root=Path(search_root).as_posix(),
        files_read=len(declared),
        test_files_excluded=len(tests),
        exclusions=tuple(
            Exclusion(relative(path), reason) for path, reason in sorted(exclusions)
        ),
        unreadable=tuple(unreadable[file] for file in sorted(unreadable)),
        contexts=tuple(sorted(contexts, key=lambda context: context.path)),
        passed_over=_passed_over(
            [file for file in in_scope if file not in claimed_files],
            declared,
            search_path,
            project_root,
            repo,
        ),
    )


def _declarations_of(
    file: Path, relative: str
) -> tuple[list[Declaration], UnreadableFile | None]:
    """What one file declares, or why it could not be read."""
    try:
        found = declarations_in(file.read_text(encoding="utf-8"))
    except SyntaxError as error:
        return [], UnreadableFile(
            relative, f"Syntax error: {error.msg} (line {error.lineno})"
        )
    except (OSError, ValueError) as error:
        return [], UnreadableFile(relative, f"{type(error).__name__}: {error}")

    module = module_name_for(file) or file.stem
    return [
        Declaration(module, each.name, each.kind, relative, each.line) for each in found
    ], None


def _files_in_scope(
    search_path: Path, project_root: Path
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Every Python file the census may read, and what was left out.

    A directory is named as an exclusion only if leaving it out removed
    a Python file from scope, so a ``__pycache__`` is not listed.

    Returns:
        The files, test files among them, and each excluded path with
        its reason
    """
    files: list[Path] = []
    directories: list[Path] = []
    exclusions: list[tuple[Path, str]] = []

    for current, names, file_names in os.walk(search_path):
        here = Path(current)
        for name in sorted(names):
            if name.startswith("."):
                if any((here / name).rglob("*.py")):
                    exclusions.append((here / name, HIDDEN))
            else:
                directories.append(here / name)
        names[:] = sorted(name for name in names if not name.startswith("."))
        files.extend(here / name for name in sorted(file_names) if name.endswith(".py"))

    ignored = _git_ignored([*directories, *files], project_root)
    kept: list[Path] = []
    named: set[Path] = set()
    for file in files:
        reason = next(
            (
                ancestor
                for ancestor in [*reversed(file.parents), file]
                if ancestor in ignored
            ),
            None,
        )
        if reason is None:
            kept.append(file)
        elif reason not in named:
            named.add(reason)
            exclusions.append((reason, GIT_IGNORED))

    return kept, exclusions


def _git_ignored(candidates: list[Path], project_root: Path) -> set[Path]:
    """Which of some paths git ignores.

    Git is asked once for all of them. Where it cannot be asked, because
    it is not installed or the solution is not in a repository, nothing
    is ignored, which is how discovery decides the same question.
    """
    if not candidates:
        return set()
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--stdin", "-z"],
            cwd=project_root,
            input="\0".join(str(path) for path in candidates),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return set()
    if result.returncode != 0:
        return set()
    return {Path(path) for path in result.stdout.split("\0") if path}


def _passed_over(
    files: list[Path],
    declared: dict[Path, list[Declaration]],
    search_path: Path,
    project_root: Path,
    repo: FilesystemBoundedContextRepository,
) -> tuple[PassedOver, ...]:
    """Source in no bounded context, by the directory discovery passed over."""
    groups: dict[Path, list[Declaration]] = {}
    for file in files:
        inside = file.relative_to(search_path).parts
        group = search_path / inside[0] if len(inside) > 1 else search_path
        groups.setdefault(group, []).extend(declared.get(file, ()))

    passed_over = []
    for group in sorted(groups):
        if group == search_path:
            # Every package has an __init__.py here. It is worth a line
            # only when it declares something.
            if not groups[group]:
                continue
            reason = IN_THE_SEARCH_ROOT
        else:
            reason = repo.why_passed_over(group) or IN_THE_SEARCH_ROOT
        passed_over.append(
            PassedOver(
                path=group.relative_to(project_root).as_posix(),
                reason=reason,
                declarations=tuple(groups[group]),
            )
        )
    return tuple(passed_over)

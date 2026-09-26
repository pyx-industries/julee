"""What `julee doctrine verify` decides, and what it runs.

The deciding is separated from the doing, as in
:mod:`julee.maintenance.release` and for the same reason: every part of
this that can be wrong is a decision, and a decision that can only be
exercised by running a real verification against a real solution is a
decision nobody tests.

Nothing here runs doctrine. :func:`pytest_arguments` says how, and
:func:`julee.cli.main` is what calls it.
"""

from pathlib import Path

from julee.core.entities.policy import SolutionPolicyConfig

__all__ = [
    "enclosing_solution",
    "pytest_arguments",
    "resolve_target",
    "target_objections",
]


def resolve_target(explicit: str | None, cwd: Path) -> Path:
    """Which codebase to verify.

    The working directory when nothing is named, or the nearest
    enclosing julee solution if the working directory is not one — so
    running from inside ``src/`` or a tests directory does the expected
    thing rather than reporting that there is nothing to check.

    Until #192 the default was the checkout containing julee itself,
    found by walking up from the installed package. Right for julee, and
    silently wrong everywhere else: a solution running this from its own
    root was told about the framework's compliance, and told it was
    green.

    Args:
        explicit: What ``--target`` said, or None
        cwd: Where the command was run

    Returns:
        The directory to verify. Not checked for existence here.
    """
    if explicit:
        return Path(explicit).expanduser()
    return enclosing_solution(cwd) or cwd


def enclosing_solution(start: Path) -> Path | None:
    """The nearest directory at or above ``start`` declaring [tool.julee].

    Read as text rather than parsed. This runs before anything is known
    about the tree, a malformed pyproject.toml further up should not
    stop the search, and the file that matters is read properly by
    :class:`~julee.core.infrastructure.repositories.file.solution_config.FileSolutionConfigRepository` immediately afterwards.

    Args:
        start: Where to begin looking

    Returns:
        The solution root, or None if no ancestor declares one
    """
    for directory in [start, *start.parents]:
        pyproject = directory / "pyproject.toml"
        try:
            if pyproject.is_file() and "[tool.julee]" in pyproject.read_text():
                return directory
        except (OSError, UnicodeDecodeError):
            # UnicodeDecodeError is not an OSError, and a pyproject.toml
            # that is not UTF-8 is a real thing to walk past rather than
            # a reason to stop looking for the solution below it.
            continue
    return None


def target_objections(target: Path, config: SolutionPolicyConfig) -> list[str]:
    """Reasons this directory cannot be verified at all.

    Distinct from a doctrine violation: these say the question cannot be
    asked, not that the answer is no. Running anyway would produce a
    green report about nothing, which is the failure mode every rule in
    :mod:`julee.core.doctrine` exists to prevent.

    Args:
        target: The directory named, or the working directory
        config: Its ``[tool.julee]`` section, read already

    Returns:
        One sentence per reason, or empty if it can be verified
    """
    if not target.is_dir():
        return [f"{target} is not a directory"]
    if not (target / "pyproject.toml").is_file():
        return [f"{target} has no pyproject.toml, so it declares nothing"]
    if not config.is_julee_solution:
        return [
            f"{target}/pyproject.toml has no [tool.julee] section, so it "
            f"does not claim to be a julee solution. Add one naming "
            f"search_root, and doctrine has something to look at."
        ]
    if config.search_root is None:
        return [
            f"{target}/pyproject.toml has [tool.julee] but no search_root, "
            f'so there is nowhere to look. Add search_root = "src".'
        ]
    if not (target / config.search_root).is_dir():
        return [
            f"search_root is {config.search_root!r}, which is not a "
            f"directory under {target}. Doctrine would find nothing and "
            f"every rule that iterates bounded contexts would pass."
        ]
    return []


def pytest_arguments(target: Path) -> list[str]:
    """How to run the doctrine suite against a target.

    ``-o addopts=`` is the part worth explaining. A solution's own
    pytest configuration is almost certainly not one doctrine should
    inherit — coverage over its packages, its markers, its plugins,
    ``-x`` — and inheriting it would make the result depend on the
    solution's test setup rather than on its architecture.

    Args:
        target: The codebase to verify

    Returns:
        Arguments for a pytest subprocess, target passed by environment
    """
    return [
        "--pyargs",
        "julee.core.doctrine",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        "--no-header",
        "-q",
    ]

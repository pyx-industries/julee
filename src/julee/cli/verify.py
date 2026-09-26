"""What `julee doctrine verify` decides, and what it runs.

The deciding is separated from the doing, as in
:mod:`julee.maintenance.release` and for the same reason: every part of
this that can be wrong is a decision, and a decision that can only be
exercised by running a real verification against a real solution is a
decision nobody tests.

Nothing here runs doctrine. :func:`pytest_arguments` says how, and
:func:`julee.cli.main` is what calls it.
"""

from collections.abc import Callable, Iterable
from pathlib import Path

from julee.core.entities.policy import SolutionPolicyConfig
from julee.core.semantics import SEMANTICS_FILE

__all__ = [
    "SKIPPED_DIRECTORIES",
    "claim_packages_in",
    "enclosing_solution",
    "packages_doctrine_cannot_import",
    "pytest_arguments",
    "resolve_target",
    "target_objections",
]

SKIPPED_DIRECTORIES = frozenset(
    {".venv", "venv", "build", "dist", "__pycache__", "node_modules", ".git"}
)
"""Directories a search of a solution's tree walks past.

The same set the semantics fixture skips. A `.venv` holds every installed
kit's own semantics.toml, and counting those would ask the solution to
answer for its dependencies.
"""


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


def claim_packages_in(target: Path) -> list[str]:
    """The packages publishing a semantics.toml in this tree.

    Named by the directory holding the file, which is how the semantics
    doctrine pairs a claim with its publisher.

    Args:
        target: The codebase to search

    Returns:
        Package names, sorted, without duplicates
    """
    found = {
        document.parent.name
        for document in target.rglob(SEMANTICS_FILE)
        if not SKIPPED_DIRECTORIES.intersection(document.parts)
    }
    return sorted(found)


def packages_doctrine_cannot_import(
    packages: Iterable[str], can_import: Callable[[str], bool]
) -> list[str]:
    """Claim publishers that are not importable from this environment.

    The semantics rules resolve a claim's near end by importing it, so
    their answer depends on what is installed here rather than on what
    is in the target directory. A package that is not installed makes
    every claim it publishes look dangling, and the rule cannot tell
    that apart from a class that was renamed or deleted (#269).

    Checked before the run rather than reported as violations during it,
    because "the premise does not hold" and "your claims are wrong" are
    different things and only one of them is the operator's fault.

    Args:
        packages: The claim publishers found in the target
        can_import: Answers whether a package imports here

    Returns:
        One sentence per package that would poison the semantics rules
    """
    return [
        f"{package} publishes semantic claims but is not importable from "
        f"this environment, so every claim it makes would be reported as "
        f"naming a class that does not exist"
        for package in packages
        if not can_import(package)
    ]


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

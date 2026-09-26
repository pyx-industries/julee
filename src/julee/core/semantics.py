"""Reading what kits claim, and what a solution accepts.

A kit ships ``semantics.toml`` beside its code. A solution keeps a
``semantics/`` directory beside ``apps/``, saying which of those claims
it takes and what it says itself.

Nothing here imports a kit. A claim's ends are dotted paths in a data
file, and the file is located as package data rather than by importing
the package that holds it, so reading every kit's claims runs no kit
code at all. Resolving an end works the same way: the source is read,
never executed (#269).

Nothing merges by itself either. A solution that says nothing gets
nothing: adopting a kit does not adopt its opinions about its
neighbours.
"""

import ast
import tomllib
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from julee.core.entities.claim import Claim
from julee.core.entities.kit import Kit

__all__ = [
    "SEMANTICS_FILE",
    "SKIPPED_DIRECTORIES",
    "accepted_claims",
    "claim_packages",
    "claims_from_toml",
    "kit_claims",
    "load_semantics",
    "names_bound_in",
    "resolves_in",
    "semantics_documents",
    "solution_claims",
]

SEMANTICS_FILE = "semantics.toml"
"""What a kit calls the file it publishes its claims in."""

SKIPPED_DIRECTORIES = frozenset(
    {".venv", "venv", "build", "dist", "__pycache__", "node_modules", ".git"}
)
"""Directories a search of a solution's tree walks past.

A ``.venv`` holds every installed kit's own semantics.toml, and counting
those would ask the solution to answer for its dependencies.
"""


def semantics_documents(solution_root: Path) -> tuple[Path, ...]:
    """Every semantics.toml this codebase publishes, in path order.

    Found on disk rather than through the kit registry, because a kit is
    a julee solution in its own right and does not adopt itself.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        Paths to the documents, sorted
    """
    return tuple(
        document
        for document in sorted(solution_root.rglob(SEMANTICS_FILE))
        if not SKIPPED_DIRECTORIES.intersection(document.parts)
    )


def claim_packages(solution_root: Path) -> dict[str, Path]:
    """Where each package publishing claims in this tree actually lives.

    A semantics.toml sits inside the package it speaks for, so its parent
    directory is that package's root. Knowing the directory is what lets
    a claim's near end be resolved by reading rather than importing.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        Package name to the directory holding it
    """
    return {
        document.parent.name: document.parent
        for document in semantics_documents(solution_root)
    }


def names_bound_in(source: str) -> frozenset[str]:
    """Every name a module's source binds at its top level.

    Classes, functions, assignments and imports, including the ones
    inside a module-level ``if`` or ``try``, because a conditional
    re-export is still a name the module offers.

    Unparseable source binds nothing, which reads as a claim about a
    class that is not there. That is the right way round: a file doctrine
    cannot read is a fact worth an objection, not one to pass over.

    Args:
        source: The text of a Python module

    Returns:
        The names it binds
    """
    try:
        module = ast.parse(source)
    except SyntaxError:
        return frozenset()

    names: set[str] = set()

    def collect(body: list[ast.stmt]) -> None:
        for statement in body:
            match statement:
                case ast.ClassDef() | ast.FunctionDef() | ast.AsyncFunctionDef():
                    names.add(statement.name)
                case ast.Assign():
                    names.update(
                        target.id
                        for target in statement.targets
                        if isinstance(target, ast.Name)
                    )
                case ast.AnnAssign(target=ast.Name() as target):
                    names.add(target.id)
                case ast.Import() | ast.ImportFrom():
                    names.update(
                        alias.asname or alias.name.split(".")[0]
                        for alias in statement.names
                    )
                case ast.If() | ast.Try():
                    collect(statement.body)
                    collect(statement.orelse)
                    for handler in getattr(statement, "handlers", []):
                        collect(handler.body)
                    collect(getattr(statement, "finalbody", []))

    collect(module.body)
    return frozenset(names)


def resolves_in(dotted_path: str, package_directory: Path) -> bool:
    """Whether a dotted path names something in this package's source.

    The path's first segment is the package itself; what follows locates
    a module under ``package_directory`` and names something in it. A
    name that is itself a module counts, as it would if the package were
    imported.

    Args:
        dotted_path: For example "julee_hcd.domain.models.story.Story"
        package_directory: Where that package's source lives

    Returns:
        True if the source binds that name
    """
    _, _, within = dotted_path.partition(".")
    if not within:
        return False
    *module_parts, name = within.split(".")
    directory = package_directory.joinpath(*module_parts)

    if (directory / f"{name}.py").is_file() or (directory / name).is_dir():
        return True

    for module in (directory.with_suffix(".py"), directory / "__init__.py"):
        if module.is_file():
            return name in names_bound_in(module.read_text(encoding="utf-8"))
    return False


def claims_from_toml(text: str, origin: str) -> tuple[Claim, ...]:
    """Read claims out of a semantics document.

    Args:
        text: The document's contents
        origin: What to name in an error, for someone who has to fix it

    Returns:
        The claims it declares, in the order it declares them

    Raises:
        ValueError: If the document is malformed or declares one id twice
    """
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{origin} is not readable TOML: {exc}") from exc

    claims = tuple(Claim(**entry) for entry in data.get("claim", []))

    seen: set[str] = set()
    for claim in claims:
        if claim.id in seen:
            raise ValueError(f"{origin} declares {claim.id!r} more than once")
        seen.add(claim.id)
    return claims


def kit_claims(kit: Kit) -> tuple[Claim, ...]:
    """What one kit claims about how its terms line up with others'.

    A kit that publishes no semantics.toml claims nothing, which is the
    usual case and not an error.

    Args:
        kit: The kit to read

    Returns:
        Its claims, or an empty tuple
    """
    try:
        root: Traversable = files(kit.package)
    except (ImportError, TypeError, ModuleNotFoundError):
        return ()

    document = root / SEMANTICS_FILE
    if not document.is_file():
        return ()
    return claims_from_toml(
        document.read_text(encoding="utf-8"), f"{kit.slug}'s {SEMANTICS_FILE}"
    )


def solution_claims(solution_root: Path) -> tuple[Claim, ...]:
    """What a solution says itself, as against what it accepts from kits.

    Every ``*.toml`` under ``semantics/`` is read, in filename order.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        The claims the solution declares, or an empty tuple

    Raises:
        ValueError: If two documents declare the same id
    """
    directory = solution_root / "semantics"
    if not directory.is_dir():
        return ()

    claims: list[Claim] = []
    seen: dict[str, str] = {}
    for document in sorted(directory.glob("*.toml")):
        for claim in claims_from_toml(
            document.read_text(encoding="utf-8"), str(document)
        ):
            if claim.id in seen:
                raise ValueError(
                    f"{document} declares {claim.id!r}, which "
                    f"{seen[claim.id]} already declares"
                )
            seen[claim.id] = str(document)
            claims.append(claim)
    return tuple(claims)


def accepted_claims(
    kit: Kit,
    accept: str | list[str],
) -> tuple[Claim, ...]:
    """The claims of one kit that a solution has said it accepts.

    ``accept`` is either ``"all"``, ``"none"``, or the ids to take. Taking
    a subset is how a solution keeps what it agrees with; taking none and
    writing its own is how it disagrees.

    Args:
        kit: The kit whose claims are being considered
        accept: "all", "none", or a list of claim ids

    Returns:
        The accepted claims, in the order the kit declares them

    Raises:
        ValueError: If a named id is not one the kit claims
    """
    claims = kit_claims(kit)
    if accept == "all":
        return claims
    if accept == "none":
        return ()
    if isinstance(accept, str):
        raise ValueError(
            f"{kit.slug} is accepted as {accept!r}; say 'all', 'none', or "
            f"list the claim ids to take"
        )

    by_id = {claim.id: claim for claim in claims}
    unknown = [wanted for wanted in accept if wanted not in by_id]
    if unknown:
        raise ValueError(
            f"{kit.slug} does not claim {', '.join(repr(u) for u in unknown)}"
        )
    return tuple(claim for claim in claims if claim.id in set(accept))


def _adoptions(solution_root: Path) -> dict[str, str | list[str]]:
    """What the solution says it accepts from each kit.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        Kit slug to "all", "none", or a list of claim ids

    Raises:
        ValueError: If two documents say different things about one kit
    """
    directory = solution_root / "semantics"
    if not directory.is_dir():
        return {}

    adoptions: dict[str, str | list[str]] = {}
    origin: dict[str, str] = {}
    for document in sorted(directory.glob("*.toml")):
        data = tomllib.loads(document.read_text(encoding="utf-8"))
        for slug, accept in data.get("adopt", {}).items():
            if slug in adoptions and adoptions[slug] != accept:
                raise ValueError(
                    f"{document} and {origin[slug]} disagree about what to "
                    f"accept from {slug}"
                )
            adoptions[slug] = accept
            origin[slug] = str(document)
    return adoptions


def load_semantics(solution_root: Path, kits: tuple[Kit, ...]) -> tuple[Claim, ...]:
    """Everything a solution holds true about how its terms line up.

    What it accepts from the kits it has adopted, plus what it says
    itself. A kit the solution says nothing about contributes nothing:
    silence is not consent.

    Args:
        solution_root: Path to the solution root directory
        kits: The kits the solution has adopted

    Returns:
        The resolved claims, kit claims first in adoption order

    Raises:
        ValueError: If the solution accepts from a kit it has not adopted,
            or two claims share an id
    """
    adoptions = _adoptions(solution_root)
    by_slug = {kit.slug: kit for kit in kits}

    unadopted = sorted(set(adoptions) - set(by_slug))
    if unadopted:
        raise ValueError(
            f"semantics accepts from {', '.join(unadopted)}, which "
            f"[tool.julee] kits does not adopt"
        )

    claims: list[Claim] = []
    for kit in kits:
        claims.extend(accepted_claims(kit, adoptions.get(kit.slug, "none")))
    claims.extend(solution_claims(solution_root))

    seen: set[str] = set()
    for claim in claims:
        if claim.id in seen:
            raise ValueError(f"{claim.id!r} is claimed twice")
        seen.add(claim.id)
    return tuple(claims)

"""What the kit rules object to.

Each function takes kits and returns its objections. Whether a package
can be imported is asked of a callable passed in, so a test can answer
that itself rather than arranging for packages to exist.
"""

from collections.abc import Callable, Iterable

from julee.core.entities.code_info import ClassInfo
from julee.core.entities.kit import Kit

__all__ = [
    "CanImport",
    "activities_not_contributed",
    "contributions_naming_nothing",
    "circular_requirements",
    "duplicate_slugs",
    "malformed_contributions",
    "slugs_colliding_with_contexts",
    "unadopted_requirements",
    "unimportable_packages",
]

CanImport = Callable[[str], bool]
"""Answers whether a package can be imported."""


def unadopted_requirements(adopted: Iterable[Kit]) -> list[str]:
    """Kits requiring a kit the solution has not adopted.

    Adoption is explicit, so a kit cannot pull in another on the
    solution's behalf. If ceap requires polling, the solution says so.

    Args:
        adopted: The kits the solution adopts

    Returns:
        One sentence per unmet requirement
    """
    adopted = list(adopted)
    slugs = {kit.slug for kit in adopted}
    return [
        f"{kit.slug} requires {required}, which is not adopted"
        for kit in adopted
        for required in kit.requires
        if required not in slugs
    ]


def circular_requirements(adopted: Iterable[Kit]) -> list[str]:
    """Kits that require themselves, however indirectly.

    Requirements form a directed acyclic graph, because a cycle has no
    order to install or describe the kits in.

    Args:
        adopted: The kits the solution adopts

    Returns:
        The slugs caught in a cycle, sorted
    """
    requirements = {kit.slug: set(kit.requires) for kit in adopted}

    def reaches(start: str, target: str, seen: set[str]) -> bool:
        for nxt in requirements.get(start, set()):
            if nxt == target or (
                nxt not in seen and reaches(nxt, target, seen | {nxt})
            ):
                return True
        return False

    return sorted(slug for slug in requirements if reaches(slug, slug, {slug}))


def duplicate_slugs(installed: Iterable[Kit]) -> list[str]:
    """Slugs claimed by more than one installed kit.

    The slug addresses a kit in [tool.julee] kits, so a duplicate makes
    adoption ambiguous.

    Args:
        installed: Every installed kit

    Returns:
        The duplicated slugs, sorted
    """
    slugs = [kit.slug for kit in installed]
    return sorted({slug for slug in slugs if slugs.count(slug) > 1})


def slugs_colliding_with_contexts(
    adopted: Iterable[Kit], context_slugs: Iterable[str]
) -> list[str]:
    """Kit slugs that are also the solution's own bounded contexts.

    Both are names in the same namespace as far as a reader is
    concerned, and doctrine reports on both.

    Args:
        adopted: The kits the solution adopts
        context_slugs: The solution's own bounded context slugs

    Returns:
        The colliding slugs, sorted
    """
    return sorted({kit.slug for kit in adopted} & set(context_slugs))


def unimportable_packages(adopted: Iterable[Kit], can_import: CanImport) -> list[str]:
    """Kits whose declared package is not there.

    The package is how doctrine and the documentation find a kit's
    bounded contexts. A manifest naming a package nobody can import
    describes a kit nobody can use.

    Args:
        adopted: The kits the solution adopts
        can_import: Answers whether a package can be imported

    Returns:
        One sentence per kit that cannot be found
    """
    return [
        f"{kit.slug} declares package {kit.package}"
        for kit in adopted
        if not can_import(kit.package)
    ]


def malformed_contributions(adopted: Iterable[Kit]) -> list[str]:
    """Contributions that are not a dotted path.

    Contributions are paths rather than objects so that reading a
    manifest imports nothing. Only the shape is checked here; resolving
    the path is the job of whichever integration consumes it.

    A point may offer one path or several, and both are checked the same
    way.

    Args:
        adopted: The kits the solution adopts

    Returns:
        One sentence per malformed contribution
    """
    return [
        f"{kit.slug}: {point} = {path!r}"
        for kit in adopted
        for point in kit.contributes
        for path in kit.contributed(point)
        if not path or path.count(":") > 1 or " " in path
    ]


def contributions_naming_nothing(
    adopted: Iterable[Kit], resolves: Callable[[str], bool]
) -> list[str]:
    """Contributions naming something that is not there.

    A manifest is a promise that a solution acts on. One naming a module
    that has moved, or an attribute that has been renamed, is a promise
    the solution finds broken at the moment it tries to mount a router —
    which is startup, in front of whoever is waiting.

    Shape is checked elsewhere and cheaply. This resolves, which costs an
    import, and is worth it because a dotted path in a data file is
    exactly the kind of thing a rename leaves behind.

    Args:
        adopted: The kits the solution adopts
        resolves: Answers whether a contribution path names something

    Returns:
        One sentence per contribution that names nothing
    """
    return [
        f"{kit.slug}: {point} = {path!r}"
        for kit in adopted
        for point in kit.contributes
        for path in kit.contributed(point)
        if not resolves(path)
    ]


def activities_not_contributed(
    classes: Iterable[ClassInfo],
    contributed: Iterable[str],
    decorator: str = "temporal_activity_registration",
) -> list[str]:
    """Activity classes a kit has but does not hand to a solution.

    Decorating a class registers its methods as Temporal activities. A
    worker still has to be told the class exists, and the way a kit tells
    a solution is its manifest. A class carrying the decorator and named
    by no contribution is an activity the kit has and no worker will run:
    the workflow calling it waits until it times out, which is the
    failure furthest from the cause.

    This is the other direction from
    :func:`contributions_naming_nothing`. That one starts from the
    manifest and asks whether each path leads somewhere. This starts from
    the code and asks whether the manifest mentions it.

    Args:
        classes: The classes the kit's own source defines
        contributed: Names of the classes the kit contributes as
            activities, already resolved from its manifest
        decorator: Name of the decorator that marks an activity class

    Returns:
        One sentence per uncontributed activity class, sorted
    """
    contributed = set(contributed)
    return sorted(
        f"{cls.name} ({cls.file}) is decorated @{decorator} "
        f"but no contribution names it"
        for cls in classes
        if cls.decorated_with(decorator) and cls.name not in contributed
    )

"""Joining what a bounded context declares to the families that hold it.

The class parser says what is in each family. The declaration reader
says what the source declares and where. This sets the two side by
side, so that a declaration in no family is as visible as one in a
family, and reads nothing itself: both sides are handed to it.

The two readers are different programs reading the same files, and
that is deliberate. Where a family member names a file and the
declarations of that file hold no such class, one of them is wrong,
and the join says so rather than choosing.
"""

from collections.abc import Iterable, Mapping, Sequence

from julee.core import doctrine_constants as paths
from julee.core.entities.bounded_context_info import BoundedContextInfo
from julee.core.parsers.declarations import CLASS
from julee.core.values.census import (
    AMBIGUOUS,
    CANDIDATE,
    CLAIMED_AT_ITS_LOCATION,
    CLAIMED_BY_NAME,
    EXTERNAL,
    RESOLVED,
    UNCLAIMED,
    ContextCensus,
    Declaration,
    Disagreement,
    Membership,
    NameOnlyMember,
)
from julee.core.values.code_info import ClassInfo

__all__ = ["FAMILY_DIRECTORIES", "census_of_context", "families_of"]

FAMILY_DIRECTORIES: Mapping[str, tuple[tuple[str, ...], ...]] = {
    "entities": (paths.ENTITIES_PATH, paths.DOMAIN_PATH),
    "values": (paths.VALUES_PATH, paths.DOMAIN_PATH),
    "use_cases": (paths.USE_CASES_PATH,),
    "requests": (paths.USE_CASES_PATH,),
    "responses": (paths.USE_CASES_PATH,),
    "dtos": (paths.DTOS_PATH,),
    "repository_protocols": (paths.REPOSITORIES_PATH, paths.DOMAIN_PATH),
    "service_protocols": (paths.SERVICES_PATH, paths.DOMAIN_PATH),
    "handler_protocols": (
        paths.HANDLERS_PATH,
        paths.SERVICES_PATH,
        paths.DOMAIN_PATH,
    ),
    "oracle_protocols": (paths.ORACLES_PATH, paths.DOMAIN_PATH),
    "calculator_protocols": (paths.CALCULATORS_PATH, paths.DOMAIN_PATH),
    "witness_protocols": (paths.WITNESSES_PATH, paths.DOMAIN_PATH),
}
"""Each family and the directories a member's file is counted from.

The first is the family's own directory. Handlers have two because one
still sitting in ``domain/services/`` is read as a handler while it
waits to be moved. A family under ``domain/`` has ``domain/`` itself
last, because a member read in an area carries its path from there
(ADR 023).

This restates what the parser does, and the join is what checks it: a
directory missing here leaves that family's members unfound, and every
one of them is reported as a disagreement.
"""


def families_of(info: BoundedContextInfo | None) -> dict[str, tuple[ClassInfo, ...]]:
    """The parser's families for one bounded context, by name.

    Args:
        info: What the parser returned, or None if it returned nothing

    Returns:
        Family name to its members, for every family named in
        :data:`FAMILY_DIRECTORIES`
    """
    if info is None:
        return dict.fromkeys(FAMILY_DIRECTORIES, ())
    return {family: getattr(info, family) for family in FAMILY_DIRECTORIES}


def census_of_context(
    slug: str,
    path: str,
    declarations: Iterable[Declaration],
    families: Mapping[str, Sequence[ClassInfo]],
) -> ContextCensus:
    """Set a context's declarations beside the families that hold them.

    Every declaration comes back in exactly one state, and every family
    member is accounted for: found where it says it is, resolved by its
    name, ambiguous, external, or in disagreement.

    Args:
        slug: The bounded context's slug
        path: Its directory, relative to the solution root
        declarations: What its files declare, files relative to the same root
        families: The parser's families for it, by family name

    Returns:
        The context's census
    """
    declarations = sorted(
        declarations, key=lambda found: (found.file, found.line, found.name)
    )
    classes_at: dict[tuple[str, str], list[Declaration]] = {}
    classes_named: dict[str, list[Declaration]] = {}
    for declaration in declarations:
        if declaration.kind != CLASS:
            continue
        classes_at.setdefault((declaration.file, declaration.name), []).append(
            declaration
        )
        classes_named.setdefault(declaration.name, []).append(declaration)

    at_location: dict[Declaration, list[str]] = {}
    by_name: dict[Declaration, list[str]] = {}
    candidates: dict[Declaration, list[str]] = {}
    name_only: list[NameOnlyMember] = []
    disagreements: list[Disagreement] = []

    for family, directories in FAMILY_DIRECTORIES.items():
        for member in families.get(family, ()):
            if member.file:
                places = [
                    "/".join((path, *directory, member.file))
                    for directory in directories
                ]
                found = next(
                    (
                        classes_at[(place, member.name)]
                        for place in places
                        if (place, member.name) in classes_at
                    ),
                    None,
                )
                if found is None:
                    disagreements.append(Disagreement(family, member.name, places[0]))
                    continue
                for declaration in found:
                    at_location.setdefault(declaration, []).append(family)
                continue

            named = tuple(classes_named.get(member.name, ()))
            if len(named) == 1:
                state = RESOLVED
                by_name.setdefault(named[0], []).append(family)
            elif named:
                state = AMBIGUOUS
                for declaration in named:
                    candidates.setdefault(declaration, []).append(family)
            else:
                state = EXTERNAL
            name_only.append(NameOnlyMember(family, member.name, state, named))

    family_directories = {
        "/".join((path, *directory)) + "/"
        for directories in FAMILY_DIRECTORIES.values()
        for directory in directories
        if directory != paths.DOMAIN_PATH
    }
    domain = "/".join((path, *paths.DOMAIN_PATH)) + "/"

    def in_family_directory(file: str) -> bool:
        # A directory under domain/ is a kind's or an area, and both are
        # read. A module directly under domain/ is in neither.
        if file.startswith(domain) and "/" in file[len(domain) :]:
            return True
        return any(file.startswith(directory) for directory in family_directories)

    def membership(declaration: Declaration) -> Membership:
        if declaration in at_location:
            state, claiming = CLAIMED_AT_ITS_LOCATION, at_location[declaration]
        elif declaration in by_name:
            state, claiming = CLAIMED_BY_NAME, by_name[declaration]
        elif declaration in candidates:
            state, claiming = CANDIDATE, candidates[declaration]
        else:
            state, claiming = UNCLAIMED, []
        return Membership(
            declaration=declaration,
            state=state,
            families=tuple(claiming),
            in_family_directory=in_family_directory(declaration.file),
        )

    return ContextCensus(
        slug=slug,
        path=path,
        memberships=tuple(membership(declaration) for declaration in declarations),
        name_only=tuple(
            sorted(name_only, key=lambda member: (member.family, member.name))
        ),
        disagreements=tuple(
            sorted(disagreements, key=lambda found: (found.file, found.name))
        ),
    )

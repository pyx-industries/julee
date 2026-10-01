"""What a census of a solution's declarations holds.

The class parser sorts classes into families, by the directory a class
sits in and for use cases by its name, and the rules that take a family
see its members and nothing else. A census sets every module-level
declaration in the source beside the family that holds it, or beside
none.

It reports family membership. It does not report which rules check a
declaration: the dependency rule reads a use case file's imports
whatever the file declares, and other rules import a layer's modules
and ask Python. Unclaimed means in no family, not unchecked. Claimed
means a member of a family, not compliant.
"""

from dataclasses import dataclass

from julee.core.values.code_info import UnreadableFile

__all__ = [
    "AMBIGUOUS",
    "CANDIDATE",
    "CLAIMED_AT_ITS_LOCATION",
    "CLAIMED_BY_NAME",
    "EXTERNAL",
    "RESOLVED",
    "UNCLAIMED",
    "Census",
    "ContextCensus",
    "Declaration",
    "Disagreement",
    "Exclusion",
    "Membership",
    "NameOnlyMember",
    "PassedOver",
]

CLAIMED_AT_ITS_LOCATION = "claimed at its location"
"""A family member carries this declaration's file and name."""

CLAIMED_BY_NAME = "claimed by name"
"""A family member carries only this name, and this is the one
declaration of it in the bounded context."""

CANDIDATE = "candidate"
"""A family member carries only this name, and the bounded context
holds several declarations of it. None of them is claimed, because
nothing says which was meant."""

UNCLAIMED = "unclaimed"
"""In no family."""

RESOLVED = "resolved"
"""A name-only family member with exactly one declaration in its
bounded context."""

AMBIGUOUS = "ambiguous"
"""A name-only family member with several declarations in its bounded
context."""

EXTERNAL = "external"
"""A name-only family member with no declaration in its bounded
context: the class is declared somewhere else."""


@dataclass(frozen=True)
class Declaration:
    """A class, function or binding declared at module level, and where."""

    module: str
    """Dotted module name, as the declaration would be imported from."""

    name: str
    kind: str
    """``class``, ``function`` or ``binding``."""

    file: str
    """Path relative to the solution root."""

    line: int

    @property
    def identity(self) -> str:
        """Module and name. Two declarations of one name in one module,
        as in the branches of an ``if``, share it and differ by line."""
        return f"{self.module}:{self.name}"


@dataclass(frozen=True)
class Membership:
    """One declaration and the family that holds it, if any."""

    declaration: Declaration
    state: str
    families: tuple[str, ...] = ()
    """The families that claim it, or that it is a candidate for."""

    in_family_directory: bool = False
    """Whether it sits in a directory the parser fills a family from.
    An unclaimed declaration there is one the parser looked at and
    passed over."""


@dataclass(frozen=True)
class NameOnlyMember:
    """A family member that carries a name and no file.

    The parser makes one for a request or response a use case file
    imports. It is a name, not a declaration, and the census never
    presents it as one.
    """

    family: str
    name: str
    state: str
    declarations: tuple[Declaration, ...] = ()
    """Every declaration of that name in the bounded context. One when
    resolved, several when ambiguous, none when external."""


@dataclass(frozen=True)
class Disagreement:
    """A family member whose file holds no class of its name.

    The parser and the census read the same file and found different
    things. That is a fault in one of the readers, not in the solution,
    and a census holding one is not to be trusted.
    """

    family: str
    name: str
    file: str
    """Path relative to the solution root."""


@dataclass(frozen=True)
class ContextCensus:
    """The census of one bounded context."""

    slug: str
    path: str
    """Path relative to the solution root."""

    memberships: tuple[Membership, ...] = ()
    name_only: tuple[NameOnlyMember, ...] = ()
    disagreements: tuple[Disagreement, ...] = ()


@dataclass(frozen=True)
class PassedOver:
    """Source under the search root that is in no bounded context."""

    path: str
    """Path relative to the solution root."""

    reason: str
    """Why discovery does not read it as a bounded context."""

    declarations: tuple[Declaration, ...] = ()


@dataclass(frozen=True)
class Exclusion:
    """A path the census did not read, and why."""

    path: str
    """Path relative to the solution root."""

    reason: str


@dataclass(frozen=True)
class Census:
    """Every declaration under a search root, and the family that holds it."""

    search_root: str
    files_read: int = 0
    test_files_excluded: int = 0
    exclusions: tuple[Exclusion, ...] = ()
    unreadable: tuple[UnreadableFile, ...] = ()
    """Files in scope that could not be read."""

    contexts: tuple[ContextCensus, ...] = ()
    passed_over: tuple[PassedOver, ...] = ()

    @property
    def is_complete(self) -> bool:
        """Whether every file in scope was read."""
        return not self.unreadable

    @property
    def readers_agree(self) -> bool:
        """Whether every family member that carries a file was found in it."""
        return not any(context.disagreements for context in self.contexts)

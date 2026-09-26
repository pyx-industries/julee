"""What the driven port rules object to.

ADR 016 names six driven ports and classifies each on two axes: how many
of its context's entities it is bound to, and whether a workflow must
reach it through an activity or may call it inline.

Every one of them is found by the directory it sits in, never by what it
is called, so a protocol whose name does not fit is read and objected to
rather than dropped. The name is then a claim these rules check.

Each rule takes what a codebase has and returns its objections. Nothing
here reads a file or imports a module.
"""

from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath

from julee.core.doctrine_constants import (
    CALCULATOR_SUFFIX,
    HANDLER_SUFFIX,
    ORACLE_SUFFIX,
    SERVICE_SUFFIX,
    WITNESS_SUFFIX,
)
from julee.core.entities.code_info import ClassInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

__all__ = [
    "ROLES_BY_DIRECTORY",
    "ZERO_ENTITY_DIRECTORIES",
    "port_implementations_outside_infrastructure",
    "ports_bound_to_entities_they_should_not_be",
    "ports_misnamed_for_their_directory",
]

ROLES_BY_DIRECTORY: Mapping[str, tuple[str, ...]] = {
    "services": (SERVICE_SUFFIX,),
    "handlers": (HANDLER_SUFFIX,),
    "oracles": (ORACLE_SUFFIX,),
    "calculators": (CALCULATOR_SUFFIX,),
    "witnesses": (WITNESS_SUFFIX,),
}
"""The roles a protocol may claim, by the directory it sits in.

``domain/repositories/`` is absent deliberately. A repository declares
itself by inheriting ``RepositoryOf[Entity]``, which is stronger than a
suffix because mypy reads it too, and the one-entity rule already checks
it. The other four have no such declaration, so the name is what they
have.

Every entry holds one role. ``services`` used to hold two, because
handlers lived there and were told apart by their name — the one place
the arrangement did not hold, and a reader noticed it immediately
(#256). Handlers have their own directory now, and nothing is found by
its name.
"""

ZERO_ENTITY_DIRECTORIES: Mapping[str, str] = {
    "oracles": ORACLE_SUFFIX,
    "witnesses": WITNESS_SUFFIX,
}
"""Where a protocol bound to one of its context's entities is misfiled.

Maps the directory to the role it holds, so an objection can name the
role rather than derive it from the directory. Deriving it is how the
first draft of this rule told an author that "a witnesse is bound to no
entity".

An Oracle deals in a foreign system's currency and a Witness in the
execution's own, so neither names an entity of the bounded context. One
that does is a Repository or a Service that has wandered, and the entity
it names says which.

A Calculator is absent because ADR 016 lets it be bound to any number:
what makes it a Calculator is that its answer follows from its
arguments, not how many entities those arguments involve.
"""


def ports_misnamed_for_their_directory(
    ports: Iterable[tuple[str, CodeArtifactWithContext]],
) -> list[str]:
    """Protocols whose names claim nothing their directory offers.

    A name is a claim and doctrine checks claims. ``SchemaOracle`` says it
    must be reached through an activity; ``NewDataCalculator`` says it may
    be called from workflow code and will replay the same. A protocol
    claiming neither leaves a reader to guess at the one thing ADR 016
    exists to make sayable.

    There are only two good answers when this fires, and the objection
    offers both: the name drifted and should be corrected, or the
    protocol is in the wrong directory.

    Args:
        ports: Directory name paired with the protocol found in it, e.g.
            ("oracles", found)

    Returns:
        One sentence per protocol whose name claims nothing
    """
    objections = []
    for directory, found in ports:
        roles = ROLES_BY_DIRECTORY.get(directory)
        if roles is None or found.artifact.name.endswith(roles):
            continue
        if directory == "services" and found.artifact.name.endswith(HANDLER_SUFFIX):
            # Correctly named, wrong shelf. Saying "rename it" here would
            # be the wrong advice and the wrong diagnosis.
            objections.append(
                f"{found.bounded_context}.{found.artifact.name}: a handler "
                f"in domain/services/. Handlers have their own directory "
                f"since ADR 016 — move it to domain/handlers/"
            )
            continue
        # Every directory offers exactly one role today, and "named
        # neither *Oracle" is what the plural phrasing produced for one.
        # Kept general because the grid has room for a directory that
        # offers two, and read once by a person who then has to act on it.
        if len(roles) == 1:
            wanted = f"not named *{roles[0]}"
            remedy = "Rename it if it is one"
        else:
            wanted = "named neither " + " nor ".join(f"*{role}" for role in roles)
            remedy = "Rename it if it is one of those"
        objections.append(
            f"{found.bounded_context}.{found.artifact.name}: in "
            f"domain/{directory}/ but {wanted}. {remedy}; if it is not, "
            f"it belongs in another of ADR 016's directories"
        )
    return objections


def ports_bound_to_entities_they_should_not_be(
    ports: Iterable[tuple[str, CodeArtifactWithContext]],
    entity_names_by_context: Mapping[str, set[str]],
) -> list[str]:
    """Oracles and witnesses naming an entity of their own context.

    Both sit at arity zero on ADR 016's grid, and for the same reason:
    what they deal in was never ours to model. An Oracle returns whatever
    the remote system says; a Witness returns what the runtime recorded.

    A protocol here that names one of its context's entities is something
    else wearing the wrong name — most often a Repository, since a single
    entity is what a Repository is bound to. Naming the entity it found
    says so, rather than leaving the author to work out why the rule
    fired.

    Args:
        ports: Directory name paired with the protocol found in it
        entity_names_by_context: Entity names, by bounded context slug

    Returns:
        One sentence per protocol bound to something it should not be
    """
    objections = []
    for directory, found in ports:
        if directory not in ZERO_ENTITY_DIRECTORIES:
            continue
        known = entity_names_by_context.get(found.bounded_context, set())
        named = sorted(found.artifact.referenced_types & known)
        if not named:
            continue
        role = ZERO_ENTITY_DIRECTORIES[directory]
        objections.append(
            f"{found.bounded_context}.{found.artifact.name}: a {role} is "
            f"bound to no entity of its context, but this one names "
            f"{named}. A protocol bound to one entity is a repository"
        )
    return objections


def protocols_in(
    directory: str, classes: Iterable[ClassInfo], slug: str
) -> list[tuple[str, CodeArtifactWithContext]]:
    """Pair each class with its directory and context, for the rules above.

    A small helper rather than a rule: it takes what a parser found and
    shapes it, and objects to nothing.

    Args:
        directory: The directory name, e.g. "oracles"
        classes: The classes parsed out of it
        slug: The bounded context they belong to

    Returns:
        Pairs ready to pass to a rule in this module
    """
    return [
        (
            directory,
            CodeArtifactWithContext(artifact=cls, bounded_context=slug),
        )
        for cls in classes
    ]


def port_implementations_outside_infrastructure(
    found: Iterable[tuple[str, ClassInfo]],
) -> list[str]:
    """Classes claiming a port role from somewhere neither ADR allows.

    ADR 002 says a driven port lives in its own directory under
    ``domain/`` and its implementations in ``infrastructure/``. The
    naming rules made the first half a claim doctrine checks; this is
    the second half, and it had been stated since ADR 002 was written
    without ever being tested (#236).

    A name ending in one of ADR 016's five role suffixes is a claim
    about how a workflow may reach it, so the same name in ``usecases/``
    or an ``apps/`` layer tells a reader the thing is a port when the
    layout says it is something else. One of the two is wrong, and
    neither can be told from the other by reading.

    Repositories are outside this, as they are outside the naming rules:
    they declare themselves by inheriting ``RepositoryOf[Entity]`` rather
    than by what they are called, so a class ending in "Repository"
    claims nothing for this rule to hold it to.

    A port protocol under the wrong port directory is left alone here.
    :func:`ports_misnamed_for_their_directory` already objects to it, and
    once is enough.

    Args:
        found: Classes of a bounded context, paired with its slug, each
            carrying a path relative to the context root

    Returns:
        One sentence per class claiming a role from the wrong layer
    """
    port_directories = {f"domain/{directory}" for directory in ROLES_BY_DIRECTORY}

    objections = []
    for slug, cls in found:
        role = next(
            (
                suffix
                for suffixes in ROLES_BY_DIRECTORY.values()
                for suffix in suffixes
                if cls.name.endswith(suffix)
            ),
            None,
        )
        if role is None:
            continue
        parts = PurePosixPath(cls.file).parts
        if not parts:
            continue
        if parts[0] == "infrastructure":
            continue
        if "/".join(parts[:2]) in port_directories:
            continue
        objections.append(
            f"{slug}.{cls.name}: a {role} found in {cls.file}. The protocol "
            f"belongs in domain/{role.lower()}s/ and anything implementing "
            f"it in infrastructure/"
        )
    return objections

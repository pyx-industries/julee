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
        wanted = " nor ".join(f"*{role}" for role in roles)
        objections.append(
            f"{found.bounded_context}.{found.artifact.name}: in "
            f"domain/{directory}/ but named neither {wanted}. Rename it if "
            f"it is one of those; if it is neither, it belongs in another "
            f"of ADR 016's directories"
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

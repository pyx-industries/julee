"""What the handler and repository protocol rules object to.

Both are about protocols keeping to one job, and both read ClassInfo and
a little about where the file sits. Nothing here imports or reads a file.
"""

import re
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath

from julee.core.entities.code_info import ClassInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

__all__ = [
    "base_entity_type",
    "handler_methods_not_returning_Acknowledgement",
    "handler_protocols_outside_singular_files",
    "handlers_outside_infrastructure_handlers",
    "repositories_referencing_several_entities",
]

_BASE_ENTITY = re.compile(
    r"(?:RepositoryOf|BaseRepository)\[([A-Za-z_][A-Za-z0-9_]*)\]"
)
"""Either way of declaring the entity a repository is bound to.

Both spellings are read rather than one, because julee-viewpoints and
other kits carry a BaseRepository of their own and their existing
declarations should keep working unchanged.
"""


_PARAMETERISED = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\[([A-Za-z_][A-Za-z0-9_]*)\]")
"""Any base of the form Name[Param], for following a declaration up."""


def base_entity_type(
    protocol: ClassInfo,
    protocols_by_name: Mapping[str, ClassInfo] | None = None,
) -> str | None:
    """The entity a repository declares, however it declares it.

    RepositoryOf[T] says which entity and nothing else; BaseRepository[T]
    says the same and adds async CRUD. A repository that is not CRUD can
    declare its entity with the first and still be checked.

    A kit whose repositories share behaviour puts a protocol of its own
    in between — ``AppRepository(HcdRepository[App])``, where
    ``HcdRepository[T]`` inherits ``BaseRepository[T]``. That declares
    the entity perfectly well to a reader and to mypy, and reading only
    the direct bases missed all seven of hcd's (#231). So a base that is
    itself a repository declaring an entity is followed, and the entity
    taken from the parameter the subclass supplied.

    Following happens by name rather than by matching ``*Repository``,
    so a kit that calls its shared protocol something else is read too.

    Args:
        protocol: The repository protocol to read
        protocols_by_name: The other repository protocols in the
            codebase, for following an indirect declaration. Without it
            only a direct declaration is read.

    Returns:
        The entity's name, or None if the protocol does not declare one
    """
    return _declared_entity(protocol, protocols_by_name or {}, frozenset())


def _declared_entity(
    protocol: ClassInfo,
    protocols_by_name: Mapping[str, ClassInfo],
    seen: frozenset[str],
) -> str | None:
    """Walk the bases, following one repository protocol into the next.

    `seen` stops a cycle. Inheritance should not contain one, but
    doctrine reads text rather than an import graph, and a rule that
    hangs is worse than one that misses something.
    """
    for base in protocol.bases:
        if match := _BASE_ENTITY.search(base):
            return match.group(1)

    for base in protocol.bases:
        match = _PARAMETERISED.search(base)
        if match is None:
            continue
        name, parameter = match.group(1), match.group(2)
        if name in seen:
            continue
        parent = protocols_by_name.get(name)
        if parent is None:
            continue
        if _declared_entity(parent, protocols_by_name, seen | {name}) is not None:
            return parameter
    return None


def handler_methods_not_returning_Acknowledgement(
    handlers: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Handler methods that return something other than an acknowledgement.

    A handler is a dispatcher (ADR 003). Returning Acknowledgement gives
    the use case a uniform answer about whether the handoff was accepted,
    without it needing to know what the handler does.

    Args:
        handlers: The handler protocols a codebase has

    Returns:
        One sentence per method returning the wrong thing
    """
    return [
        f"{found.bounded_context}.{found.artifact.name}.{method.name}(): "
        f"return type is '{method.return_type}', expected 'Acknowledgement'"
        for found in handlers
        for method in found.artifact.methods
        if method.return_type != "Acknowledgement"
    ]


def handler_protocols_outside_singular_files(
    handlers: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Handler protocols not in a file named for the one handler in it.

    One protocol per file, named for its role. The singular says the file
    defines a handler rather than collecting several unrelated ones.

    Args:
        handlers: The handler protocols a codebase has

    Returns:
        One sentence per protocol in the wrong file
    """
    return [
        f"{found.bounded_context}.{found.artifact.name}: defined in "
        f"'{found.artifact.file}', expected a file named '*_handler.py'"
        for found in handlers
        if not found.artifact.file.endswith("_handler.py")
    ]


def handlers_outside_infrastructure_handlers(
    found: Iterable[tuple[str, ClassInfo]],
) -> list[str]:
    """Handler implementations filed somewhere other than handlers/.

    Keeping them together makes them findable and keeps them apart from
    the other things infrastructure holds. Temporal's layer wrappers are
    exempt: they follow the three-layer pattern for workflows.

    Args:
        found: Classes under infrastructure/, paired with their context

    Returns:
        One sentence per handler in the wrong place
    """
    objections = []
    for slug, cls in found:
        if not cls.name.endswith("Handler"):
            continue
        parts = PurePosixPath(cls.file).parts
        if not parts or parts[0] in {"temporal", "handlers"}:
            continue
        objections.append(
            f"{slug}.{cls.name}: found in infrastructure/{cls.file}, "
            f"expected infrastructure/handlers/"
        )
    return objections


def repositories_referencing_several_entities(
    repositories: Iterable[CodeArtifactWithContext],
    entity_names_by_context: dict[str, set[str]],
) -> list[str]:
    """Repositories doing the work of two.

    A repository protocol covers one aggregate. Naming another context
    entity in its signatures blurs the boundary and couples two things
    that should be able to change apart.

    A protocol declaring neither RepositoryOf[T] nor BaseRepository[T],
    directly or through another repository protocol, is exempt: its
    primary entity cannot be told structurally. Declaring the entity and
    offering CRUD were the same thing until RepositoryOf split them, so
    a repository that is not CRUD can say what it holds and be checked
    rather than skipped (#179).

    The entity names a context offers include the kernel's own, because
    a kit builds on ``BoundedContextInfo``, ``ClassInfo`` and
    ``Accelerator`` and there are kit repositories over all three. Left
    out, a repository bound to one of those scored zero, which is
    indistinguishable from a protocol holding nothing at all (#237).

    Args:
        repositories: The repository protocols a codebase has
        entity_names_by_context: Entity names, by bounded context slug,
            each already carrying the kernel's

    Returns:
        One sentence per repository covering more than one entity
    """
    repositories = list(repositories)
    # A kit's shared base — hcd's HcdRepository[T] — is itself in this
    # list, which is what lets an indirect declaration be followed.
    protocols_by_name = {found.artifact.name: found.artifact for found in repositories}

    objections = []
    for found in repositories:
        protocol = found.artifact
        primary = base_entity_type(protocol, protocols_by_name)
        if primary is None:
            continue
        known = entity_names_by_context.get(found.bounded_context, set())
        foreign = (protocol.referenced_types & known) - {primary}
        if foreign:
            objections.append(
                f"{found.bounded_context}.{protocol.name}: primary entity "
                f"'{primary}' but also references {sorted(foreign)}"
            )
    return objections

"""What the handler and repository protocol rules object to.

Both are about protocols keeping to one job, and both read ClassInfo and
a little about where the file sits. Nothing here imports or reads a file.
"""

import re
from collections.abc import Iterable
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

_BASE_ENTITY = re.compile(r"BaseRepository\[([A-Za-z_][A-Za-z0-9_]*)\]")


def base_entity_type(protocol: ClassInfo) -> str | None:
    """The entity a repository declares through BaseRepository[T].

    Args:
        protocol: The repository protocol to read

    Returns:
        The entity's name, or None if the protocol does not declare one
    """
    for base in protocol.bases:
        match = _BASE_ENTITY.search(base)
        if match:
            return match.group(1)
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

    A protocol that does not declare BaseRepository[T] is exempt: its
    primary entity cannot be told structurally.

    Args:
        repositories: The repository protocols a codebase has
        entity_names_by_context: Entity names, by bounded context slug

    Returns:
        One sentence per repository covering more than one entity
    """
    objections = []
    for found in repositories:
        protocol = found.artifact
        primary = base_entity_type(protocol)
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

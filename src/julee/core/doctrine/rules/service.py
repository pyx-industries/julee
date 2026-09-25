"""What the service protocol rules object to.

A service protocol is found by the directory it sits in, not by its name,
so a class that does not follow the convention is read and objected to
rather than dropped. ADR 002 puts service protocols in ``domain/services/``
and their implementations in ``infrastructure/``.

Each rule takes what a codebase has and returns its objections. Nothing
here reads a file or imports a module.
"""

from collections.abc import Iterable

from julee.core.doctrine_constants import HANDLER_SUFFIX, SERVICE_SUFFIX
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

__all__ = [
    "contexts_whose_services_doctrine_cannot_see",
    "services_not_named_for_their_role",
]


def services_not_named_for_their_role(
    services: Iterable[CodeArtifactWithContext],
) -> list[str]:
    """Protocols in domain/services/ that say nothing about what they are.

    A name is a claim, and doctrine checks claims. ``PollerService`` says
    it is a service and is held to what a service is; ``EpicCreatedHandler``
    says it is a handler and is held to ADR 003. A protocol that claims
    neither is asked why, because there are only two good answers and both
    want acting on: the name drifted and should be corrected, or the
    protocol is not a service and does not belong in this directory.

    The second answer is the interesting one. The first protocol this rule
    found — polling's ``NewDataAnalyzer``, ``(bytes | None, bytes) ->
    list[str]`` — references no entity of its context at all, which is the
    shape #233 is about. Nobody had named it ``NewDataAnalyzerService``
    because it does not feel like a service, and that instinct is the
    signal this rule harvests.

    Args:
        services: The service protocols a codebase has

    Returns:
        One sentence per protocol whose name claims nothing
    """
    return [
        f"{found.bounded_context}.{found.artifact.name}: in domain/services/ "
        f"but named neither *{SERVICE_SUFFIX} nor *{HANDLER_SUFFIX}. Rename "
        f"it if it is one of those; if it is neither, it does not belong here"
        for found in services
        if not found.artifact.name.endswith((SERVICE_SUFFIX, HANDLER_SUFFIX))
    ]


def contexts_whose_services_doctrine_cannot_see(
    contexts_with_services: Iterable[tuple[str, int]],
) -> list[str]:
    """Contexts with a services package doctrine reads nothing out of.

    The canary. A rule that finds nothing passes, and a rule that finds
    nothing because it was looking wrongly passes just as quietly — which
    is how a downstream solution ran doctrine over twenty service
    protocols and was told it had none (#175), and how seven hcd
    repositories went unchecked for months (#231).

    So a bounded context that has a ``domain/services/`` package with
    something in it, and out of which doctrine reads neither a service nor
    a handler, says so instead of passing.

    Args:
        contexts_with_services: Context slug paired with the number of
            protocols read out of its services package, for each context
            whose package holds at least one module

    Returns:
        One sentence per context doctrine is blind to
    """
    return [
        f"{slug}: has a domain/services/ package with modules in it, but "
        f"doctrine read no service or handler protocol out of it"
        for slug, found in contexts_with_services
        if found == 0
    ]

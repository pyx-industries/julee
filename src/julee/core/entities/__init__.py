"""Domain models for the shared (core) accelerator.

These models represent the foundational code concepts that julee is built on.
Viewpoint accelerators (HCD, C4) project onto these concepts.

Meta-entities (Entity, UseCase, etc.) define what Clean Architecture artifacts
ARE - their docstrings serve as definitions for doctrine documentation.

Import directly from submodules:
    from julee.core.entities.bounded_context import BoundedContext
    from julee.core.entities.pipeline import Pipeline
"""

import pkgutil
from importlib import import_module

from pydantic import BaseModel

__all__ = ["kernel_entity_names"]


def kernel_entity_names() -> frozenset[str]:
    """Every entity the kernel offers, by name.

    Discovered rather than listed. A hand-written set of the ones anybody
    had thought of is how ``READ_DOMAIN_PACKAGES`` came to raise a false
    objection on ``domain/oracles/`` (#260), and the cost of being wrong
    here is the same shape: a rule that reads an arity gets the wrong
    number and says nothing about it.

    A kit builds on these legitimately — ``BoundedContextInfo``,
    ``ClassInfo`` and ``Accelerator`` all have kit repositories over them
    — so they must count toward what a protocol is bound to, exactly as
    the kit's own entities do (#237).

    ``Entity`` itself is left out: it is the base every entity inherits,
    not one of them. ``ContentStream`` is not here because it is not a
    record — it is a stream a repository hands back, and binding to one
    is not what this counts.

    Returns:
        The names, for intersecting with a protocol's referenced types
    """
    names = set()
    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith("_") or module.name == "tests":
            continue
        imported = import_module(f"{__name__}.{module.name}")
        for name, obj in vars(imported).items():
            if not isinstance(obj, type) or not issubclass(obj, BaseModel):
                continue
            if obj.__module__ != imported.__name__ or name == "Entity":
                continue
            names.add(name)
    return frozenset(names)

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


def kernel_classes() -> dict[str, type]:
    """Every class the kernel's entity modules define, whatever it is.

    Deliberately unfiltered. ``kernel_entity_names`` keeps only what
    is a ``BaseModel``, which is the right question for arity and the
    wrong one for anything that asks what these classes *should* be:
    as they become frozen dataclasses they would drop out of that set
    one by one, and a rule reading it would go quiet rather than
    green.

    ``Entity`` is left out. It is the base an entity inherits, not one
    of them.

    Returns:
        Each class by name, for a caller that judges them
    """
    found: dict[str, type] = {}
    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith("_") or module.name == "tests":
            continue
        imported = import_module(f"{__name__}.{module.name}")
        for name, obj in vars(imported).items():
            if not isinstance(obj, type) or obj.__module__ != imported.__name__:
                continue
            if name == "Entity" or name.startswith("_"):
                continue
            found[name] = obj
    return found


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
    not one of them. ``ContentStream`` and ``Acknowledgement`` are not
    here because neither is a record — one is a stream a repository
    hands back, the other is a handler's answer — and binding is about
    records. Both are excluded by being no kind of ``BaseModel``, which
    is a thin thread to hang a decision on, so both are asserted absent
    in ``test_kernel_entities`` and ``test_acknowledgement``.

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

"""Domain models for the shared (core) accelerator.

These models represent the foundational code concepts that julee is built on.
Viewpoint accelerators (HCD, C4) project onto these concepts.

Meta-entities (Entity, UseCase, etc.) define what Clean Architecture artifacts
ARE - their docstrings serve as definitions for doctrine documentation.

Import directly from submodules:
    from julee.core.entities.bounded_context import BoundedContext
    from julee.core.entities.pipeline import Pipeline
"""

import dataclasses
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


NOT_RECORDS = frozenset({"Entity", "ContentStream", "Acknowledgement"})
"""Kernel classes that are not entities, so nothing binds to them.

``Entity`` is the base an entity inherits, not one of them.
``ContentStream`` is a stream a repository hands back, and
``Acknowledgement`` is a handler's answer. Binding is about records,
and none of these is one.

Named here rather than inferred. All three used to fall out of
:func:`kernel_entity_names` for not being a ``BaseModel``, which said
nothing about what they are and stopped being true of
``Acknowledgement`` the day it became a frozen dataclass.
"""


def _is_a_record(obj: type) -> bool:
    """Whether a class is the kind of thing a repository keeps.

    A value object is not: ``Slug`` is a str and ``ClaimKind`` an enum,
    and neither is stored under an id.

    Args:
        obj: A class defined in one of the entity modules

    Returns:
        True for a pydantic model or a dataclass
    """
    return issubclass(obj, BaseModel) or dataclasses.is_dataclass(obj)


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

    What counts is being a record: a pydantic model or a dataclass. It
    used to be ``BaseModel`` alone, and that thread snapped the moment
    an entity became a frozen dataclass — ``Accelerator`` simply left
    the set, and the rules that read it went quiet rather than wrong,
    which is worse.

    ``NOT_RECORDS`` says which kernel classes are left out and why,
    rather than leaving it to what they happen to inherit.

    Returns:
        The names, for intersecting with a protocol's referenced types
    """
    names = set()
    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith("_") or module.name == "tests":
            continue
        imported = import_module(f"{__name__}.{module.name}")
        for name, obj in vars(imported).items():
            if not isinstance(obj, type) or not _is_a_record(obj):
                continue
            if obj.__module__ != imported.__name__ or name in NOT_RECORDS:
                continue
            names.add(name)
    return frozenset(names)

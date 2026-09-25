"""Deprecated aliases for the two witnesses.

``ClockService`` and ``ExecutionService`` were named before ADR 016 had a
word for what they are. They are witnesses: bound to no entity, safe to
call from workflow code, and never to be wrapped in an activity, because
the runtime records what they said. Neither was ever a service under ADR
009's own rule, which binds a service to two or more entity types.

They moved to :mod:`julee.core.witnesses`. This module keeps the old
names working for one release, because every solution built on julee
injects them and a straight cut would break each one at once.

This module defines no names statically — ClockService,
SystemClockService, ExecutionService and DefaultExecutionService are
served by ``__getattr__``, so asking for one warns. Import from
``julee.core.witnesses`` instead::

    from julee.core.witnesses import ClockWitness, SystemClockWitness
"""

import warnings
from typing import Any

from julee.core.witnesses.clock import ClockWitness, SystemClockWitness
from julee.core.witnesses.execution import DefaultExecutionWitness, ExecutionWitness

_RENAMED: dict[str, tuple[str, Any]] = {
    "ClockService": ("ClockWitness", ClockWitness),
    "SystemClockService": ("SystemClockWitness", SystemClockWitness),
    "ExecutionService": ("ExecutionWitness", ExecutionWitness),
    "DefaultExecutionService": ("DefaultExecutionWitness", DefaultExecutionWitness),
}


def __getattr__(name: str) -> Any:
    """Return the renamed object, warning once per name.

    Done through module ``__getattr__`` rather than plain assignment so
    that the warning names what the caller asked for and what to ask for
    instead. A plain alias would be silent, and a warning at import time
    would fire for anything that merely touches the package.
    """
    renamed = _RENAMED.get(name)
    if renamed is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    new_name, obj = renamed
    warnings.warn(
        f"julee.core.services.{name} is deprecated and will be removed: "
        f"it is a witness, not a service (ADR 016). Import "
        f"julee.core.witnesses.{new_name} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return obj

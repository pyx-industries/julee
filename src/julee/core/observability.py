"""How an adapter finds out which execution it is serving.

A use case does not log (ADR 017). An adapter does, and a log with no
thread through it is twelve unrelated lines where there was one run. The
thread is the execution identifier a use case already has, reaching the
adapter without passing through any port signature.

Ambient, because the alternative was widening every driven port that
logs — ``save(entity, run=run)`` — and a port's signature is the
domain's sentence about what it needs. It does not need a log
correlation id; the thing on the other side does.

A ``ContextVar`` is also what OpenTelemetry and Temporal's interceptors
already propagate, so a span processor or an interceptor can read this
without knowing julee exists.

Nothing in the domain ring imports this module. A use case neither sets
nor reads the identifier, which is what keeps ambient state out of the
part of the code that has to be reasoned about.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from julee.core.witnesses.execution import ExecutionWitness

_execution_id: ContextVar[str] = ContextVar("julee_execution_id", default="")
"""The execution an adapter is serving, or "" when nothing said."""


def execution_id() -> str:
    """Which execution this call belongs to.

    Returns:
        The identifier, or "" if nothing set one. An adapter with no
        identifier logs without one: a missing thread is a worse log, not
        a broken run.
    """
    return _execution_id.get()


@contextmanager
def serving(witness: ExecutionWitness) -> Iterator[str]:
    """Mark this block as serving one execution.

    The composition root wraps a run in this, so every adapter called
    inside it can say which execution it was for. The witness is asked
    once, here, rather than by each adapter — an adapter has no business
    holding a driven port of the use case's.

    Args:
        witness: The execution witness the composition root injected

    Yields:
        The identifier that is now current
    """
    identifier = witness.get_execution_id()
    token = _execution_id.set(identifier)
    try:
        yield identifier
    finally:
        _execution_id.reset(token)


def log_extra(**fields: Any) -> dict[str, Any]:
    """Log fields for an adapter, with the execution identifier added.

    Written as a helper so an adapter cannot forget the thread while
    remembering the rest::

        self.logger.debug("Content stored", extra=log_extra(size=len(raw)))

    Args:
        **fields: What this event is about

    Returns:
        Those fields, plus execution_id when one is set
    """
    identifier = execution_id()
    return {**fields, "execution_id": identifier} if identifier else dict(fields)


class ExecutionIdFilter(logging.Filter):
    """Puts the execution identifier on every record.

    For a solution that formats its logs rather than reading ``extra``
    programmatically. Attached to a handler, ``%(execution_id)s`` then
    works in a format string, and a record from outside any execution
    carries "" rather than blowing up the formatter.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add execution_id to the record.

        Args:
            record: The record being emitted

        Returns:
            True. This filter adds a field rather than excluding a record
        """
        record.execution_id = execution_id()
        return True

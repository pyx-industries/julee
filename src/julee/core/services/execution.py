"""Deprecated alias module for :mod:`julee.core.witnesses.execution`.

Kept so that ``from julee.core.services.execution import ...`` keeps working
for one release: it answers for ExecutionService and DefaultExecutionService.
See :mod:`julee.core.services` for why the name changed.

No ``__all__`` here, because nothing is defined statically — the names
are served by ``__getattr__`` so that asking for one warns.
"""

from typing import Any

from julee.core.services import __getattr__ as _renamed


def __getattr__(name: str) -> Any:
    """Defer to the package shim, so the warning is worded once."""
    return _renamed(name)

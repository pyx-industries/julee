"""Clock service protocol.

Defines the interface for services that provide current time.
Use cases inject ClockService to avoid direct datetime.now() calls,
enabling deterministic testing and execution-context-agnostic code.

Why ClockService exists:
    Use cases often need timestamps for domain state (entity created_at,
    updated_at, etc.). Direct datetime.now() calls create two problems:

    1. Non-deterministic tests - tests produce different results each run
    2. Execution context coupling - some contexts (like Temporal workflows)
       require special time handling for deterministic replay

ClockService abstracts time access so use cases don't know or care whether
they're running in tests, direct execution, or orchestration frameworks.

Scope:
    ClockService is injected into USE CASES ONLY. Service implementations
    (repositories, external service adapters) MAY use datetime.now() for
    operational timestamps - these are infrastructure concerns.

    The distinction:
    - Domain state timestamps (entity created_at) → ClockService
    - Operational timestamps (when API called) → Implementation detail

See ADR 004: Execution-Agnostic Use Cases for design rationale.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class ClockService(Protocol):
    """Service protocol for obtaining current time.

    All timestamps returned are timezone-aware UTC datetimes.
    """

    def now(self) -> datetime:
        """Return current time as timezone-aware datetime (UTC)."""
        ...

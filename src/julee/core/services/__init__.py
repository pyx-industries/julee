"""Core service protocols for execution-agnostic use cases.

Provides ClockService and ExecutionService protocols so use cases can obtain
the current time and execution identity without coupling to a specific
execution framework.

See ADR 004: Execution-Agnostic Use Cases.
"""

from julee.core.services.clock import ClockService, SystemClockService
from julee.core.services.execution import DefaultExecutionService, ExecutionService

__all__ = [
    "ClockService",
    "SystemClockService",
    "ExecutionService",
    "DefaultExecutionService",
]

"""Execution service protocol.

Defines the interface for services that provide execution context identity.
Use cases inject ExecutionService to obtain execution IDs without coupling
to specific orchestration frameworks.

Why ExecutionService exists:
    Use cases that create traceable entities need execution identifiers
    (for correlation, debugging, audit trails). Different execution contexts
    provide these differently:

    - Temporal: workflow_id from workflow.info()
    - Prefect: flow_run_id
    - Direct execution: generated UUID
    - Tests: deterministic ID

ExecutionService abstracts this so use cases don't know or care about
the execution framework.

Scope:
    ExecutionService is injected into use cases that need execution identity
    for entity creation. Not all use cases need this - only inject where
    the entity requires an execution_id field.

See ADR 004: Execution-Agnostic Use Cases for design rationale.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ExecutionService(Protocol):
    """Service protocol for execution context identity.

    Provides unique identifiers for the current execution context,
    enabling traceability across distributed systems.
    """

    def get_execution_id(self) -> str:
        """Return unique identifier for this execution.

        The ID is stable within a single execution - multiple calls
        return the same value.
        """
        ...

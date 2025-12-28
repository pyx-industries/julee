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

import uuid
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


class DefaultExecutionService:
    """ExecutionService implementation using UUIDs.

    Generates a UUID at construction time and returns it for all calls.

    Use this for:
    - Production non-workflow code
    - CLI tools
    - Simple async execution
    - When you need to provide a specific ID

    For Temporal workflows, use TemporalExecutionService instead.
    """

    def __init__(self, execution_id: str | None = None) -> None:
        """Initialize with optional specific ID.

        Args:
            execution_id: Specific ID to use. If None, generates UUID.
        """
        self._execution_id = execution_id or str(uuid.uuid4())

    def get_execution_id(self) -> str:
        """Return the execution ID."""
        return self._execution_id


class FixedExecutionService:
    """ExecutionService implementation returning a fixed ID.

    Use this for:
    - Deterministic tests
    - Reproducing specific scenarios

    This is functionally identical to DefaultExecutionService with
    a provided ID, but the name makes test intent clearer.
    """

    def __init__(self, execution_id: str) -> None:
        """Initialize with a fixed execution ID.

        Args:
            execution_id: The ID to always return.
        """
        self._execution_id = execution_id

    def get_execution_id(self) -> str:
        """Return the fixed execution ID."""
        return self._execution_id

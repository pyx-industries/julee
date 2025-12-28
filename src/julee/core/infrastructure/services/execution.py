"""ExecutionService implementations for non-Temporal contexts.

For Temporal workflows, use TemporalExecutionService from infrastructure/temporal/.
"""

from __future__ import annotations

import uuid


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

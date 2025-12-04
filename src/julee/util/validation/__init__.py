"""
Validation utilities for type checking and debugging serialization issues.

This module provides utilities for validating runtime types against expected
types, with special focus on debugging common serialization issues in
Temporal workflows where Pydantic models get deserialized as dictionaries.
"""

from .repository import (
    RepositoryValidationError,
    ensure_repository_protocol,
    validate_repository_protocol,
)
from .type_guards import (
    TypeValidationError,
    guard_check,
    validate_parameter_types,
    validate_type,
)

__all__ = [
    "TypeValidationError",
    "validate_type",
    "validate_parameter_types",
    "guard_check",
    "RepositoryValidationError",
    "validate_repository_protocol",
    "ensure_repository_protocol",
]

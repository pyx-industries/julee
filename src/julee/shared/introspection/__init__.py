"""Introspection utilities for Python code analysis.

Provides reflection and AST-based analysis of Python classes,
particularly use cases following clean architecture patterns.
"""

from .usecase import (
    RepositoryCall,
    UseCaseMetadata,
    introspect_use_case,
    resolve_use_case_class,
)

__all__ = [
    "UseCaseMetadata",
    "RepositoryCall",
    "introspect_use_case",
    "resolve_use_case_class",
]

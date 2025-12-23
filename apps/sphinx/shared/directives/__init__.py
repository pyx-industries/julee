"""Shared Sphinx directives.

Domain-agnostic directives that can be used by multiple Sphinx extensions.
"""

from .usecase_ssd import UseCaseSSDDirective

__all__ = [
    "UseCaseSSDDirective",
]

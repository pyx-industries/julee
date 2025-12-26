"""
API services package for the julee CEAP system.

This package contains application-layer components that orchestrate use cases
and coordinate startup/runtime concerns. Components in this package
act as facades between the API layer and the domain layer, coordinating
multiple use cases and handling cross-cutting concerns.

Note: These are application-layer orchestrators, not domain services.
Domain services (which transform between 2+ entity types) live in
{bc}/services/ directories within bounded contexts.
"""

from .system_initialization import SystemInitializer

__all__ = [
    "SystemInitializer",
]

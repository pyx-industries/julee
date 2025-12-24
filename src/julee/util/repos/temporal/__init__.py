"""
Temporal repository utilities.

This module provides utilities for working with Temporal repositories,
including the temporal_activity_registration decorator for automatically
wrapping repository methods as Temporal activities.
"""

from julee.core.infrastructure.temporal.decorators import temporal_activity_registration

__all__ = ["temporal_activity_registration"]

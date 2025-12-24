"""Code introspection domain models.

Re-exports from julee.shared.domain.models.code_info for backward compatibility.
These models are core concepts of Clean Architecture and live in shared/.
"""

from julee.shared.domain.models.code_info import (
    BoundedContextInfo,
    ClassInfo,
    FieldInfo,
)

__all__ = [
    "BoundedContextInfo",
    "ClassInfo",
    "FieldInfo",
]

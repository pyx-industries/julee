"""In-memory repository support.

Every solution's tests need in-memory repositories, so the mixin they are
built from is part of the kernel. The repositories themselves belong to
whichever bounded context owns the entity.
"""

from .base import MemoryRepositoryMixin

__all__ = ["MemoryRepositoryMixin"]

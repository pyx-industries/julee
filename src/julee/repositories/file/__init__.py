"""Repositories backed by files.

Every solution's tests need in-memory repositories; a solution whose
records are files — features, documents, manifests — needs these.
"""

from .base import FileRepositoryMixin

__all__ = ["FileRepositoryMixin"]

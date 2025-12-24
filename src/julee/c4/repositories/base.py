"""Base repository protocol for C4.

Re-exports BaseRepository from shared for consistency across accelerators.
"""

from julee.shared.domain.repositories.base import BaseRepository

__all__ = ["BaseRepository"]

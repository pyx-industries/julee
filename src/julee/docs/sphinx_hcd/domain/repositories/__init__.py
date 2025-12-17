"""Repository protocols for sphinx_hcd.

Defines async repository interfaces following julee patterns.
Implementations live in the repositories/ directory.
"""

from .base import BaseRepository
from .story import StoryRepository

__all__ = ["BaseRepository", "StoryRepository"]

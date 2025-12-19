"""Base repository protocol for sphinx_c4.

Re-exports BaseRepository from sphinx_hcd for consistency.
"""

from julee.docs.sphinx_hcd.domain.repositories.base import BaseRepository

__all__ = ["BaseRepository"]

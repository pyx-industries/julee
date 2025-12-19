"""Utilities for sphinx_c4.

Re-exports common utilities from sphinx_hcd for consistency.
"""

from julee.docs.sphinx_hcd.utils import normalize_name, slugify

__all__ = ["normalize_name", "slugify"]

"""HCD Sphinx utilities.

Re-exports utilities needed by HCD Sphinx directives.
"""

# Domain utilities from HCD accelerator
from julee.hcd.utils import (
    kebab_to_snake,
    normalize_name,
    parse_csv_option,
    parse_integration_options,
    parse_list_option,
    slugify,
)

# Sphinx-specific utilities from shared
from apps.sphinx.shared import (
    make_internal_link,
    make_reference,
    path_to_root,
)

__all__ = [
    "normalize_name",
    "slugify",
    "kebab_to_snake",
    "parse_list_option",
    "parse_csv_option",
    "parse_integration_options",
    "path_to_root",
    "make_reference",
    "make_internal_link",
]

"""Text helpers shared across bounded contexts.

Slugs and normalised names are how entities refer to each other across a
solution: a story names its app by slug, a journey names its epics. The
rules have to be the same everywhere or the references stop matching,
which is why these live in the kernel rather than in each kit.
"""

import re

__all__ = ["kebab_to_snake", "normalize_name", "slugify"]


def normalize_name(name: str) -> str:
    """Normalise a name for comparison.

    Lowercases, and treats hyphens and underscores as spaces, so that
    "Data Steward", "data-steward" and "data_steward" compare equal.

    Args:
        name: Name to normalise

    Returns:
        Normalised lowercase name with consistent spacing
    """
    return name.lower().replace("-", " ").replace("_", " ").strip()


def slugify(text: str) -> str:
    """Make a URL-safe slug from text.

    Args:
        text: Text to slugify

    Returns:
        Lowercase, hyphen-separated slug with no punctuation
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def kebab_to_snake(name: str) -> str:
    """Convert a kebab-case name to snake_case, for Python module names.

    Args:
        name: Kebab-case name, for example "audit-analysis"

    Returns:
        Snake_case name, for example "audit_analysis"
    """
    return name.replace("-", "_")

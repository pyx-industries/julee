"""What is said about an accelerator, and what it points at.

Neither is an accelerator. A validation issue is a finding about one, and
an integration reference names something an accelerator reads from or
writes to — a pair of strings, not an aggregate. Both sat beside
``Accelerator`` and were counted as entities for it (ADR 018).
"""

from dataclasses import dataclass


def checked_slug(slug: str) -> str:
    """The slug to keep, or a refusal.

    This was a ``field_validator`` in ``mode="before"`` on two entities.
    It both refused an empty slug and returned a stripped one, so it
    decided what the field holds rather than only checking it, and the
    stripping has to survive or an accelerator read from a padded
    manifest stops matching its own references.

    Args:
        slug: What the caller supplied

    Returns:
        The slug with surrounding whitespace removed

    Raises:
        ValueError: If the slug is empty or only whitespace
    """
    if not slug or not slug.strip():
        raise ValueError("slug cannot be empty")
    return slug.strip()


@dataclass(frozen=True)
class AcceleratorValidationIssue:
    """Something wrong with one accelerator, found by comparing it to code.

    Validation reads what the documentation claims and what the code
    contains, and reports where they disagree: an accelerator with no
    code, code with no accelerator, or a mismatch between them.
    """

    slug: str
    """The accelerator the issue is about."""

    issue_type: str
    """One of "undocumented", "no_code" or "mismatch"."""

    message: str
    """What is wrong, in a sentence."""


@dataclass(frozen=True)
class IntegrationReference:
    """Reference to an integration with optional description.

    Used for sources_from and publishes_to relationships where
    an accelerator may specify what data it sources or publishes.
    """

    slug: str
    """Integration slug (e.g., "pilot-data-collection")."""

    description: str = ""
    """What is sourced/published (e.g., "Scheme documentation")."""

    def __post_init__(self) -> None:
        """Check the slug and trim it.

        Raises:
            ValueError: If the slug is empty or only whitespace
        """
        object.__setattr__(self, "slug", checked_slug(self.slug))

    @classmethod
    def from_dict(cls, data: dict | str) -> "IntegrationReference":
        """Create from dict or string.

        Args:
            data: Either a dict with slug/description or a plain string slug

        Returns:
            IntegrationReference instance
        """
        if isinstance(data, str):
            return cls(slug=data)
        return cls(slug=data.get("slug", ""), description=data.get("description", ""))

"""Shared utilities for julee accelerators.

Common functions used across multiple accelerator domains.
"""

import re


def normalize_name(name: str) -> str:
    """Normalize a name for comparison (lowercase, hyphens to spaces).

    Args:
        name: Name to normalize

    Returns:
        Normalized lowercase name with consistent spacing
    """
    return name.lower().replace("-", " ").replace("_", " ").strip()


def slugify(text: str) -> str:
    """Create a URL-safe slug from text.

    Args:
        text: Text to slugify

    Returns:
        URL-safe slug string
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def kebab_to_snake(name: str) -> str:
    """Convert kebab-case to snake_case for Python module names.

    Args:
        name: Kebab-case name (e.g., 'audit-analysis')

    Returns:
        Snake_case name (e.g., 'audit_analysis')
    """
    return name.replace("-", "_")


def parse_list_option(value: str) -> list[str]:
    """Parse a newline-separated list option with optional bullet prefixes.

    Handles RST-style lists like:
        - First item
        - Second item with (commas, inside)

    Does NOT split on commas to preserve items containing parenthetical lists.

    Args:
        value: Raw option string

    Returns:
        List of stripped item strings
    """
    if not value:
        return []
    items = []
    for line in value.strip().split("\n"):
        item = line.strip().lstrip("- ")
        if item:
            items.append(item)
    return items


def parse_csv_option(value: str) -> list[str]:
    """Parse a comma-separated list option.

    Args:
        value: Raw option string

    Returns:
        List of stripped item strings
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_integration_options(value: str) -> list[dict]:
    """Parse integration options with optional descriptions.

    Supports format: integration-slug (description of data)
    Example: pilot-data-collection (CMA documents, audit reports)

    Args:
        value: Raw option string

    Returns:
        List of dicts with 'slug' and 'description' keys
    """
    if not value:
        return []

    items = []
    for line in value.strip().split("\n"):
        line = line.strip().lstrip("- ")
        if not line:
            continue

        # Parse: slug (description) or just slug
        match = re.match(r"^([a-z0-9-]+)\s*(?:\(([^)]+)\))?$", line.strip())
        if match:
            items.append(
                {
                    "slug": match.group(1),
                    "description": match.group(2).strip() if match.group(2) else None,
                }
            )
        else:
            # Fallback: treat whole line as slug
            items.append(
                {
                    "slug": line.strip(),
                    "description": None,
                }
            )

    return items

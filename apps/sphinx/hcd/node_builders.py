"""Common node builders for sphinx_hcd directives.

DRYs up repeated docutils node construction patterns across directive files.
All functions return docutils nodes ready for insertion into the doctree.
"""

from collections.abc import Callable
from typing import Any

from docutils import nodes


def make_link(path: str, text: str) -> nodes.reference:
    """Create a reference node linking to a path.

    Args:
        path: URI or relative path to link to
        text: Display text for the link

    Returns:
        Reference node containing the text
    """
    ref = nodes.reference("", "", refuri=path)
    ref += nodes.Text(text)
    return ref


def make_strong_link(path: str, text: str) -> nodes.reference:
    """Create a reference node with bold text.

    Args:
        path: URI or relative path to link to
        text: Display text for the link (will be bold)

    Returns:
        Reference node containing strong text
    """
    ref = nodes.reference("", "", refuri=path)
    ref += nodes.strong(text=text)
    return ref


def metadata_paragraph(label: str, value: str) -> nodes.paragraph:
    """Create a 'Label: value' paragraph with bold label.

    Args:
        label: The label text (will be bold, colon added automatically)
        value: The value text

    Returns:
        Paragraph node like "**Label:** value"

    Example:
        >>> node = metadata_paragraph("Status", "active")
        # Renders as: **Status:** active
    """
    para = nodes.paragraph()
    para += nodes.strong(text=f"{label}: ")
    para += nodes.Text(value)
    return para


def link_list_paragraph(
    label: str,
    items: list[Any],
    link_fn: Callable[[Any], tuple[str, str]],
) -> nodes.paragraph:
    """Create a 'Label: link1, link2, link3' paragraph with bold label.

    Args:
        label: The label text (will be bold, colon added automatically)
        items: List of items to create links for
        link_fn: Function that takes an item and returns (path, display_text)

    Returns:
        Paragraph node with comma-separated links

    Example:
        >>> apps = [app1, app2]
        >>> node = link_list_paragraph(
        ...     "Apps",
        ...     apps,
        ...     lambda a: (f"apps/{a.slug}.html", a.name)
        ... )
        # Renders as: **Apps:** App One, App Two
    """
    para = nodes.paragraph()
    para += nodes.strong(text=f"{label}: ")

    for i, item in enumerate(items):
        path, text = link_fn(item)
        ref = nodes.reference("", "", refuri=path)
        ref += nodes.Text(text)
        para += ref
        if i < len(items) - 1:
            para += nodes.Text(", ")

    return para


def entity_bullet_list(
    entities: list[Any],
    link_fn: Callable[[Any], tuple[str, str]],
    suffix_fn: Callable[[Any], str] | None = None,
    desc_fn: Callable[[Any], str] | None = None,
) -> nodes.bullet_list:
    """Create a bullet list of entity links.

    Args:
        entities: List of entities to list
        link_fn: Function that takes an entity and returns (path, display_text)
        suffix_fn: Optional function returning text to append inline (e.g., " (3 stories)")
        desc_fn: Optional function returning description for a sub-paragraph

    Returns:
        Bullet list node with linked items

    Example:
        >>> epics = [epic1, epic2]
        >>> node = entity_bullet_list(
        ...     epics,
        ...     link_fn=lambda e: (f"{e.slug}.html", e.slug.replace("-", " ").title()),
        ...     suffix_fn=lambda e: f" ({len(e.story_refs)} stories)",
        ... )
    """
    bullet_list = nodes.bullet_list()

    for entity in entities:
        item = nodes.list_item()
        para = nodes.paragraph()

        path, text = link_fn(entity)
        ref = nodes.reference("", "", refuri=path)
        ref += nodes.Text(text)
        para += ref

        if suffix_fn:
            suffix = suffix_fn(entity)
            if suffix:
                para += nodes.Text(suffix)

        item += para

        if desc_fn:
            desc = desc_fn(entity)
            if desc:
                desc_para = nodes.paragraph()
                desc_para += nodes.Text(desc)
                item += desc_para

        bullet_list += item

    return bullet_list


def titled_bullet_list(
    title: str,
    items: list[str],
    title_suffix: str = ":",
) -> list[nodes.Node]:
    """Create a titled section with a bullet list.

    Args:
        title: Section title (will be bold)
        items: List of text items
        title_suffix: Suffix after title (default ":")

    Returns:
        List containing title paragraph and bullet list nodes

    Example:
        >>> nodes = titled_bullet_list("Goals", ["Be fast", "Be reliable"])
        # Renders as:
        # **Goals:**
        # - Be fast
        # - Be reliable
    """
    result = []

    title_para = nodes.paragraph()
    title_para += nodes.strong(text=f"{title}{title_suffix}")
    result.append(title_para)

    bullet_list = nodes.bullet_list()
    for item in items:
        list_item = nodes.list_item()
        para = nodes.paragraph()
        para += nodes.Text(item)
        list_item += para
        bullet_list += list_item
    result.append(bullet_list)

    return result


def empty_result_paragraph(message: str) -> nodes.paragraph:
    """Create an emphasized 'not found' message paragraph.

    Args:
        message: The message to display (will be italic)

    Returns:
        Paragraph node with emphasized text

    Example:
        >>> node = empty_result_paragraph("No accelerators defined")
    """
    para = nodes.paragraph()
    para += nodes.emphasis(text=message)
    return para


def problematic_paragraph(message: str) -> nodes.paragraph:
    """Create a problematic message paragraph for errors.

    Args:
        message: The error message

    Returns:
        Paragraph node with problematic styling

    Example:
        >>> node = problematic_paragraph("App 'foo' not found")
    """
    para = nodes.paragraph()
    para += nodes.problematic(text=message)
    return para


def grouped_bullet_lists(
    groups: dict[str, list[Any]],
    group_order: list[tuple[str, str]],
    link_fn: Callable[[Any], tuple[str, str]],
    suffix_fn: Callable[[Any], str] | None = None,
    desc_fn: Callable[[Any], str] | None = None,
) -> list[nodes.Node]:
    """Create multiple titled bullet lists grouped by category.

    Args:
        groups: Dict mapping group keys to lists of entities
        group_order: List of (group_key, display_label) tuples defining order
        link_fn: Function that takes an entity and returns (path, display_text)
        suffix_fn: Optional function returning text to append inline
        desc_fn: Optional function returning description for a sub-paragraph

    Returns:
        List of nodes with headings and bullet lists

    Example:
        >>> by_status = {"active": [a1, a2], "draft": [a3]}
        >>> order = [("active", "Active"), ("draft", "Draft")]
        >>> nodes = grouped_bullet_lists(
        ...     by_status,
        ...     order,
        ...     link_fn=lambda a: (f"{a.slug}.html", a.name),
        ... )
    """
    result = []

    for group_key, group_label in group_order:
        entities = groups.get(group_key, [])
        if not entities:
            continue

        # Group heading
        heading = nodes.paragraph()
        heading += nodes.strong(text=group_label)
        result.append(heading)

        # Entity list
        bullet_list = entity_bullet_list(
            entities,
            link_fn=link_fn,
            suffix_fn=suffix_fn,
            desc_fn=desc_fn,
        )
        result.append(bullet_list)

    return result

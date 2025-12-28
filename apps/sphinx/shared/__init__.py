"""Shared Sphinx utilities.

Common utilities used by both HCD and C4 Sphinx extensions.
"""

from docutils import nodes


def path_to_root(docname: str) -> str:
    """Calculate relative path from a document to the docs root.

    Args:
        docname: Document name (e.g., 'users/journeys/build-vocabulary')

    Returns:
        Relative path prefix (e.g., '../../')
    """
    depth = docname.count("/")
    return "../" * depth


def make_reference(uri: str, text: str, is_code: bool = False) -> nodes.reference:
    """Create a reference node.

    Args:
        uri: Target URI
        text: Link text
        is_code: If True, render text as code/literal

    Returns:
        docutils reference node
    """
    ref = nodes.reference("", "", refuri=uri)
    if is_code:
        ref += nodes.literal(text=text)
    else:
        ref += nodes.Text(text)
    return ref


def make_internal_link(
    docname: str,
    target_doc: str,
    text: str,
    anchor: str | None = None,
) -> nodes.reference:
    """Create an internal document link with proper relative path.

    Args:
        docname: Current document name
        target_doc: Target document path (e.g., 'applications/staff-portal')
        text: Link text
        anchor: Optional anchor within target page

    Returns:
        docutils reference node
    """
    prefix = path_to_root(docname)
    uri = f"{prefix}{target_doc}.html"
    if anchor:
        uri = f"{uri}#{anchor}"
    return make_reference(uri, text)


def build_relative_uri(
    from_docname: str,
    target_doc: str,
    anchor: str | None = None,
) -> str:
    """Build a relative URI from one document to another.

    Calculates the optimal relative path by finding the common prefix
    between source and target document paths.

    Args:
        from_docname: Source document name (e.g., 'users/journeys/build-vocab')
        target_doc: Target document path (e.g., 'hcd/stories/staff-portal')
        anchor: Optional anchor within target page

    Returns:
        Relative URI string (e.g., '../../hcd/stories/staff-portal.html#anchor')
    """
    from_parts = from_docname.split("/")
    target_parts = target_doc.split("/")

    # Find common prefix length
    common = 0
    for i in range(min(len(from_parts), len(target_parts))):
        if from_parts[i] == target_parts[i]:
            common += 1
        else:
            break

    # Build relative path
    up_levels = len(from_parts) - common - 1
    down_path = "/".join(target_parts[common:])

    if up_levels > 0:
        rel_path = "../" * up_levels + down_path + ".html"
    else:
        rel_path = down_path + ".html"

    if anchor:
        return f"{rel_path}#{anchor}"
    return rel_path


from .roles import (
    EntityRefRole,
    make_anchor_role,
    make_autoapi_role,
    make_conditional_role,
    make_page_role,
)

__all__ = [
    "path_to_root",
    "make_reference",
    "make_internal_link",
    "build_relative_uri",
    "EntityRefRole",
    "make_autoapi_role",
    "make_page_role",
    "make_anchor_role",
    "make_conditional_role",
]

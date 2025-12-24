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


__all__ = [
    "path_to_root",
    "make_reference",
    "make_internal_link",
]

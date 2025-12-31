"""Generated Supply Chain directives using the directive factory.

Creates directives for Accelerator entity by combining:
- Build functions from directives module
- directive_factory for boilerplate reduction

IMPORTANT: Placeholder classes MUST be defined at module level for Sphinx
to pickle them correctly during incremental builds.
"""

from docutils import nodes

from apps.sphinx.directive_factory import generate_index_directive_from_build_fn
from apps.sphinx.hcd.context import get_hcd_context


# =============================================================================
# Placeholder Classes (must be module-level for pickle serialization)
# =============================================================================


class GeneratedAcceleratorIndexPlaceholder(nodes.General, nodes.Element):
    """Placeholder for accelerator-index directive."""

    pass


# =============================================================================
# Generated Accelerator Directives (build-function-based)
# =============================================================================


def _build_accelerator_index_wrapper(docname, ctx, **options):
    """Wrap build_accelerator_index for factory compatibility.

    Note: Uses HCD context for cross-entity queries (apps, integrations).
    """
    from .directives.accelerator import build_accelerator_index

    return build_accelerator_index(docname, ctx)


GeneratedAcceleratorIndexDirective = generate_index_directive_from_build_fn(
    entity_name="Accelerator",
    build_function=_build_accelerator_index_wrapper,
    context_getter=get_hcd_context,  # HCD context needed for apps/integrations
    placeholder_class=GeneratedAcceleratorIndexPlaceholder,
)

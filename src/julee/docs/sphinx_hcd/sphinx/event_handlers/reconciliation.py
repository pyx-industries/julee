"""Persona reconciliation for sphinx_hcd.

Emits Sphinx warnings when stories reference undefined personas.
"""

from sphinx.util import logging

from ...utils import normalize_name
from ..context import get_hcd_context

logger = logging.getLogger(__name__)


def check_persona_reconciliation(app) -> None:
    """Check that story personas match defined personas.

    Emits Sphinx warnings for stories that reference personas
    that haven't been formally defined via define-persona directive.

    This should be called once after all documents have been read
    (at doctree-resolved time).

    Args:
        app: Sphinx application instance
    """
    # Avoid running multiple times per build
    if not hasattr(app.env, "_hcd_persona_reconciliation_done"):
        app.env._hcd_persona_reconciliation_done = False

    if app.env._hcd_persona_reconciliation_done:
        return

    app.env._hcd_persona_reconciliation_done = True

    context = get_hcd_context(app)

    # Get all defined personas
    defined_personas = context.persona_repo.list_all()
    defined_names = {p.normalized_name for p in defined_personas}

    # Skip reconciliation if no personas are defined
    # (backwards compatibility - don't warn if user isn't using define-persona)
    if not defined_names:
        return

    # Get all stories
    stories = context.story_repo.list_all()

    # Find stories with undefined personas
    undefined_personas = {}  # persona_name -> list of story titles
    for story in stories:
        if story.persona_normalized == "unknown":
            continue  # This gets a different warning
        if story.persona_normalized not in defined_names:
            if story.persona not in undefined_personas:
                undefined_personas[story.persona] = []
            undefined_personas[story.persona].append(story.feature_title)

    # Emit warnings
    for persona_name, story_titles in sorted(undefined_personas.items()):
        count = len(story_titles)
        if count == 1:
            logger.warning(
                f"Story '{story_titles[0]}' references undefined persona "
                f"'{persona_name}'. Consider adding a define-persona directive."
            )
        else:
            examples = ", ".join(f"'{t}'" for t in story_titles[:3])
            if count > 3:
                examples += f" and {count - 3} more"
            logger.warning(
                f"{count} stories reference undefined persona '{persona_name}' "
                f"({examples}). Consider adding a define-persona directive."
            )

    # Also check for defined personas without stories
    story_personas = {s.persona_normalized for s in stories if s.persona_normalized != "unknown"}
    for persona in defined_personas:
        if persona.normalized_name not in story_personas:
            logger.warning(
                f"Defined persona '{persona.name}' (slug: {persona.slug}) "
                f"has no stories referencing them."
            )

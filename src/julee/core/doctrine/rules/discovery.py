"""What the discovery rule objects to.

Every other rule takes the bounded contexts as given and checks what is
inside them. This one checks the search itself: that what doctrine found
under ``search_root`` is what the codebase says is there.

Nothing here imports or reads a file.
"""

from collections.abc import Iterable

__all__ = [
    "NONE_DECLARED",
    "contexts_found_disagreeing_with_declaration",
]

NONE_DECLARED = "none"
"""The only value ``[tool.julee] bounded_contexts`` accepts.

A count would go stale the day a context is added, and nobody would
notice, because a stale count fails loudly only in the direction that
was already checked. "none" is the single statement worth writing down,
because it is the one reality doctrine cannot tell apart from silence.
"""


def contexts_found_disagreeing_with_declaration(
    search_root: str,
    context_slugs: Iterable[str],
    declaration: str | None,
) -> list[str]:
    """Objections where the census and the declaration do not match.

    Three ways to disagree:

    A codebase that found nothing and said nothing. This is the case the
    rule exists for. Every rule that iterates contexts passed, and the
    run is indistinguishable from one over a codebase that complies.

    A codebase that declared none and has some. The declaration was true
    when written and has been overtaken; leaving it would suppress the
    check for every context added after it.

    A declaration of something other than "none". Nothing else is
    meaningful, and a misspelling would otherwise read as no declaration
    at all — which is the silence this rule is about.

    Args:
        search_root: Where the codebase says its source lives
        context_slugs: The bounded contexts discovery found under it
        declaration: ``[tool.julee] bounded_contexts``, or None if absent

    Returns:
        One sentence per disagreement
    """
    found = sorted(context_slugs)

    if declaration is not None and declaration != NONE_DECLARED:
        return [
            f'[tool.julee] bounded_contexts = "{declaration}" means nothing. '
            f'The only value it takes is "{NONE_DECLARED}", which says this '
            f"codebase deliberately has no bounded contexts. Remove the line "
            f"or correct it."
        ]

    if declaration == NONE_DECLARED and found:
        return [
            f'[tool.julee] bounded_contexts = "{NONE_DECLARED}" is out of '
            f"date: {len(found)} found under {search_root} "
            f"({', '.join(found)}). Remove the line, so that these are "
            f"checked."
        ]

    if declaration is None and not found:
        return [
            f"No bounded context found under {search_root}, and nothing "
            f"says that is intended. Every rule that iterates contexts has "
            f"just passed by having no subject. Either search_root is "
            f"pointing at the wrong place, or this codebase has no domain "
            f"code — in which case say so with bounded_contexts = "
            f'"{NONE_DECLARED}" in [tool.julee], and say why.'
        ]

    return []

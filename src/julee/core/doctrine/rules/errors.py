"""Objections about the exceptions a domain declares."""

from collections.abc import Iterable

from julee.core.doctrine.resolution import Verdict

__all__ = ["classes_in_errors_that_are_not_exceptions"]


def classes_in_errors_that_are_not_exceptions(verdicts: Iterable[Verdict]) -> list[str]:
    """Classes in a domain's errors that are not exceptions.

    ``errors`` is where a bounded context declares its exceptions, as a
    directory or a module under ``domain/`` (ADR 024), and every class
    there is found by where it sits. The verdicts come from
    :func:`julee.core.doctrine.resolution.error_verdicts`, which imports
    each class rather than reading its bases, so an exception built on a
    base of the context's own is known to be one.

    Args:
        verdicts: One per class declared in errors, from error_verdicts

    Returns:
        One sentence per class that does not belong there
    """
    return [
        f"{verdict.bounded_context}.{verdict.name}: a class in the domain's "
        f"errors is an exception, but {verdict.reason}"
        for verdict in verdicts
        if verdict.reason is not None
    ]

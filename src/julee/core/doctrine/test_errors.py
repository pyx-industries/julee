"""Doctrine about errors: the exceptions a bounded context's domain declares."""

from pathlib import Path

from julee.core.doctrine.resolution import error_verdicts
from julee.core.doctrine.rules.errors import classes_in_errors_that_are_not_exceptions
from julee.core.parsers.ast import parse_bounded_context


class TestWhatErrorsHolds:
    """Doctrine about the classes in a bounded context's errors."""

    def test_every_class_in_errors_MUST_be_an_exception(self, repo) -> None:
        """A class in the domain's errors MUST be an exception.

        A bounded context declares its exceptions in ``errors`` under
        ``domain/``: a directory or a module of that name, directly
        under ``domain/`` or in an area (ADR 024). They are in the
        domain because every ring may import it. A use case raises one,
        an adapter raises one when what it wraps refuses, and an
        application catches one, with no further permission to import.

        A class there is found by where it sits, so one that is not an
        exception is something else in the wrong place, and no other
        rule would read it.

        An exception declared among the entities is objected to by the
        entity rules, which say where it belongs.
        """
        verdicts = []
        for context in repo.discover_all():
            info = parse_bounded_context(Path(context.path))
            if info is None:
                continue
            verdicts.extend(
                error_verdicts(
                    context.slug,
                    Path(context.path),
                    [found.name for found in info.errors],
                )
            )

        violations = classes_in_errors_that_are_not_exceptions(verdicts)

        assert not violations, "\n".join(violations)

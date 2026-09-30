"""An ``__init__.py`` imports nothing it does not use (ADR 019).

Walks the target's search root rather than its bounded contexts. A
facade is a property of a package, not of a context — and julee itself
has no bounded contexts, so a rule that iterated them would leave the
kernel's own facades unread.
"""

from pathlib import Path

from julee.core.doctrine.rules.facade import (
    SKIPPED_DIRECTORIES,
    facades,
    re_exports_in,
)


class TestInitModules:
    """Every ``__init__.py`` under the search root."""

    def test_an_init_MUST_NOT_re_export(
        self, project_root: Path, search_root: str
    ) -> None:
        """A name is imported from the module that defines it.

        Objects to each ``__init__.py`` that imports a name and does
        nothing with it but list it in ``__all__``. A module that uses
        what it imports — a function defined there, a Sphinx ``setup()``
        registering directives — is not a facade and is not reported.
        """
        root = project_root / search_root
        found = []
        for init in sorted(root.rglob("__init__.py")):
            if SKIPPED_DIRECTORIES & set(init.relative_to(root).parts):
                continue
            names = re_exports_in(init.read_text())
            if names:
                found.append((str(init.relative_to(project_root)), tuple(names)))

        violations = facades(found)

        assert not violations, "__init__.py files that re-export:\n" + "\n".join(
            violations
        )

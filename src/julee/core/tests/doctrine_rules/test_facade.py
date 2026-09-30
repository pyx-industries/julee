"""Tests for the facade rule: what counts as a re-export."""

import pytest

from julee.core.doctrine.rules.facade import facades, re_exports_in

pytestmark = pytest.mark.unit


class TestWhatIsARexport:
    """Use, not shape."""

    def test_a_name_imported_and_only_listed_in_all_is_one(self) -> None:
        """The facade in its purest form."""
        source = 'from .base import Mixin\n\n__all__ = ["Mixin"]\n'

        assert re_exports_in(source) == ["Mixin"]

    def test_a_name_imported_and_never_mentioned_is_one(self) -> None:
        """__all__ is not required for a re-export to be one."""
        assert re_exports_in("from .base import Mixin\n") == ["Mixin"]

    def test_a_name_the_module_uses_is_not(self) -> None:
        """julee/core/entities/__init__.py defines kernel_entity_names()."""
        source = (
            "import pkgutil\n"
            "from .base import Kernel\n\n"
            "def names():\n"
            "    return [m.name for m in pkgutil.iter_modules(Kernel.__path__)]\n\n"
            '__all__ = ["names"]\n'
        )

        assert re_exports_in(source) == []

    def test_registering_a_directive_is_using_it(self) -> None:
        """A Sphinx extension's __init__ needs no exception written."""
        source = (
            "from .directives import DefineApp\n\n"
            "def setup(app):\n"
            '    app.add_directive("define-app", DefineApp)\n'
        )

        assert re_exports_in(source) == []

    def test_a_star_import_re_exports_everything(self) -> None:
        """There is nothing to name, so it is named as itself."""
        assert re_exports_in("from .base import *\n") == ["*"]

    def test_an_alias_is_judged_by_the_name_it_binds(self) -> None:
        """import x as y binds y; y used is not a re-export, y unused is."""
        assert (
            re_exports_in("import json as j\n\ndef f():\n    return j.dumps({})\n")
            == []
        )
        assert re_exports_in("import json as j\n") == ["j"]

    def test_a_docstring_alone_is_nothing(self) -> None:
        """What every __init__.py should be."""
        assert re_exports_in('"""Stories."""\n') == []

    def test_the_order_is_the_import_order(self) -> None:
        """So the objection reads like the file."""
        source = "from .b import B\nfrom .a import A\n"

        assert re_exports_in(source) == ["B", "A"]


class TestTheObjection:
    """One sentence per file, naming the names."""

    def test_it_names_the_file_and_the_names(self) -> None:
        """A reader should be able to go straight to the line."""
        [objection] = facades([("src/acme/usecases/__init__.py", ("A", "B"))])

        assert objection.startswith("src/acme/usecases/__init__.py re-exports A, B")
        assert "ADR 019" in objection

    def test_nothing_found_is_nothing_said(self) -> None:
        assert facades([]) == []

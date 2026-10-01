"""Tests for reading what a module declares."""

import pytest

from julee.core.parsers.declarations import (
    BINDING,
    CLASS,
    FUNCTION,
    Found,
    declarations_in,
)

pytestmark = pytest.mark.unit


def names(source: str) -> list[str]:
    return [found.name for found in declarations_in(source)]


class TestWhatIsADeclaration:
    def test_a_class_is(self) -> None:
        assert declarations_in("class Story:\n    pass\n") == [Found("Story", CLASS, 1)]

    def test_a_function_is(self) -> None:
        assert declarations_in("def plan():\n    pass\n") == [
            Found("plan", FUNCTION, 1)
        ]

    def test_an_async_function_is(self) -> None:
        assert declarations_in("async def plan():\n    pass\n") == [
            Found("plan", FUNCTION, 1)
        ]

    def test_a_name_assigned_a_call_is(self) -> None:
        """An identity made with NewType, or a registry built by a call."""
        assert declarations_in('StoryId = NewType("StoryId", str)\n') == [
            Found("StoryId", BINDING, 1)
        ]

    def test_an_annotated_name_assigned_a_call_is(self) -> None:
        assert declarations_in("RULES: Rules = Rules()\n") == [
            Found("RULES", BINDING, 1)
        ]

    def test_several_in_one_module_stay_distinct(self) -> None:
        source = "class A:\n    pass\n\n\nclass B:\n    pass\n\n\ndef c():\n    pass\n"

        assert declarations_in(source) == [
            Found("A", CLASS, 1),
            Found("B", CLASS, 5),
            Found("c", FUNCTION, 9),
        ]


class TestWhatIsNot:
    def test_a_constant_is_not(self) -> None:
        assert names("LIMIT = 10\nNAME = 'x'\n") == []

    def test_a_plain_alias_is_not(self) -> None:
        assert names("Story = Tale\n") == []

    def test_an_imported_name_is_not(self) -> None:
        """It is declared where it was imported from."""
        assert names("from acme.dtos import StoryRequest\nimport os\n") == []

    def test_an_annotation_without_a_value_is_not(self) -> None:
        assert names("limit: int\n") == []

    def test_a_call_assigned_to_several_names_is_not(self) -> None:
        assert names("a = b = make()\n") == []

    def test_a_call_unpacked_into_names_is_not(self) -> None:
        assert names("a, b = make()\n") == []

    def test_a_call_assigned_to_an_attribute_is_not(self) -> None:
        assert names("config.rules = Rules()\n") == []


class TestModuleLevel:
    def test_a_nested_class_is_not_reported(self) -> None:
        source = "class Outer:\n    class Inner:\n        pass\n"

        assert names(source) == ["Outer"]

    def test_a_method_is_not_reported(self) -> None:
        source = "class Story:\n    def plan(self):\n        pass\n"

        assert names(source) == ["Story"]

    def test_a_class_inside_a_function_is_not_reported(self) -> None:
        source = "def factory():\n    class Made:\n        pass\n    return Made\n"

        assert names(source) == ["factory"]

    def test_a_class_under_an_if_is_reported(self) -> None:
        """The class parser reads it as the module's, so this does too."""
        source = (
            "if TYPE_CHECKING:\n    class A:\n        pass\n"
            "else:\n    class B:\n        pass\n"
        )

        assert names(source) == ["A", "B"]

    def test_a_class_under_a_try_is_reported(self) -> None:
        source = (
            "try:\n    class A:\n        pass\n"
            "except ImportError:\n    class B:\n        pass\n"
            "else:\n    class C:\n        pass\n"
            "finally:\n    class D:\n        pass\n"
        )

        assert names(source) == ["A", "B", "C", "D"]

    def test_a_class_under_a_with_is_reported(self) -> None:
        assert names("with suppress():\n    class A:\n        pass\n") == ["A"]

    def test_blocks_inside_blocks_are_followed(self) -> None:
        source = "if A:\n    try:\n        class Deep:\n            pass\n    finally:\n        pass\n"

        assert names(source) == ["Deep"]

    def test_a_name_declared_in_two_branches_is_reported_twice(self) -> None:
        """Told apart by line."""
        source = "if A:\n    class Story:\n        pass\nelse:\n    class Story:\n        pass\n"

        assert declarations_in(source) == [
            Found("Story", CLASS, 2),
            Found("Story", CLASS, 5),
        ]


class TestSourceThatCannotBeRead:
    def test_a_syntax_error_is_raised(self) -> None:
        with pytest.raises(SyntaxError):
            declarations_in("def broken(:\n")

    def test_an_empty_module_declares_nothing(self) -> None:
        assert declarations_in("") == []

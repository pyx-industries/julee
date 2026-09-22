"""An acknowledgement says whether a handler will act, and may name the
execution that took the work."""

from julee.core.entities.acknowledgement import Acknowledgement


def test_wilco_unable_and_roger_keep_their_meaning() -> None:
    assert Acknowledgement.wilco().is_wilco
    assert Acknowledgement.unable().is_unable
    assert Acknowledgement.roger().is_roger


def test_a_handler_with_nothing_to_name_names_nothing() -> None:
    assert Acknowledgement.wilco().execution_id is None


def test_a_handler_that_started_an_execution_can_name_it() -> None:
    answer = Acknowledgement.wilco(execution_id="orphan-story/abc")

    assert answer.is_wilco
    assert answer.execution_id == "orphan-story/abc"


def test_the_execution_survives_serialisation() -> None:
    answer = Acknowledgement.wilco(execution_id="orphan-story/abc")

    assert Acknowledgement.model_validate_json(answer.model_dump_json()) == answer

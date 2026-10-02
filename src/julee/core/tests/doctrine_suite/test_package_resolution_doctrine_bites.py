"""Package declarations must be resolved as well as discovered."""

from pathlib import Path

import pytest

from .harness import assert_doctrine_ran, run_doctrine
from .test_name_filter_doctrine_bites import (
    A_FROZEN_ENTITY,
    A_USE_CASE,
    AN_ENTITY_THAT_CAN_BE_CHANGED,
    ENTITY_SELECTOR,
    ENTITY_TEST,
    USE_CASE_TEST,
    a_solution,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("frozen", [True, False])
def test_an_entity_in_a_package_init_obeys_the_entity_rules(
    tmp_path: Path, frozen: bool
) -> None:
    root = tmp_path / "init_entity"
    context = a_solution(root)
    source = A_FROZEN_ENTITY if frozen else AN_ENTITY_THAT_CAN_BE_CHANGED
    (context / "domain/models/__init__.py").write_text(source.format(name="Result"))
    result = run_doctrine(root, ENTITY_TEST, ENTITY_SELECTOR)
    assert_doctrine_ran(result, 1, ENTITY_SELECTOR)
    assert (result.returncode == 0) == frozen, result.stdout
    if not frozen:
        assert "stories.Result" in result.stdout
        assert "could not resolve" not in result.stdout


def test_a_use_case_in_a_package_init_resolves_its_messages(tmp_path: Path) -> None:
    root = tmp_path / "init_usecase"
    context = a_solution(root)
    (context / "usecases/plan_story.py").unlink()
    (context / "usecases/__init__.py").write_text(A_USE_CASE)
    selector = "matching_request or matching_response or pydantic_DTO"
    result = run_doctrine(root, USE_CASE_TEST, selector)
    assert_doctrine_ran(result, 6, selector)
    assert result.returncode == 0, result.stdout


def test_a_non_dto_request_declared_in_a_package_init_fails(tmp_path: Path) -> None:
    root = tmp_path / "init_request"
    context = a_solution(root)
    (context / "usecases/__init__.py").write_text("class OtherRequest: pass\n")
    selector = "every_request_MUST_be_a_pydantic_DTO"
    result = run_doctrine(root, USE_CASE_TEST, selector)
    assert_doctrine_ran(result, 1, selector)
    assert result.returncode != 0, result.stdout
    assert "OtherRequest" in result.stdout
    assert "could not resolve" not in result.stdout

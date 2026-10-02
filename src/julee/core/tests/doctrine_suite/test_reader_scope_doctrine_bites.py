"""Discovery and rules exclude the same test files."""

from pathlib import Path

import pytest

from julee.core.parsers.ast import parse_bounded_context

from .harness import assert_doctrine_ran, run_doctrine
from .test_name_filter_doctrine_bites import (
    ENTITY_SELECTOR,
    ENTITY_TEST,
    USE_CASE_TEST,
    a_solution,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("file", ["test_probe.py", "tests/probe.py"])
def test_test_only_imports_do_not_create_message_members(
    tmp_path: Path, file: str
) -> None:
    context = a_solution(tmp_path)
    target = context / "usecases" / file
    target.parent.mkdir(exist_ok=True)
    target.write_text("from elsewhere import GhostRequest, GhostResponse\n")
    info = parse_bounded_context(context)
    assert info is not None
    assert [member.name for member in info.requests] == ["PlanStoryRequest"]
    assert [member.name for member in info.responses] == ["PlanStoryResponse"]


@pytest.mark.parametrize("file", ["test_probe.py", "tests/probe.py"])
def test_runtime_resolution_does_not_import_test_files(
    tmp_path: Path, file: str
) -> None:
    context = a_solution(tmp_path)
    target = context / "domain/models" / file
    target.parent.mkdir(exist_ok=True)
    target.write_text('raise RuntimeError("test code must not be imported")\n')
    result = run_doctrine(tmp_path, ENTITY_TEST, ENTITY_SELECTOR)
    assert_doctrine_ran(result, 1, ENTITY_SELECTOR)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    "file,excluded", [("test_probe.py", True), ("probe.py", False)]
)
def test_file_rules_leave_test_files_out_without_hiding_source(
    tmp_path: Path, file: str, excluded: bool
) -> None:
    context = a_solution(tmp_path)
    (context / "usecases" / file).write_text(
        "from datetime import datetime\nimport temporalio\n"
        "from acme.stories.infrastructure import Driver\n"
        "observed = datetime.now()\n"
    )
    selector = "call_datetime_now or import_temporalio or import_only_inward"
    result = run_doctrine(tmp_path, USE_CASE_TEST, selector)
    assert_doctrine_ran(result, 3, selector)
    assert (result.returncode == 0) == excluded, result.stdout

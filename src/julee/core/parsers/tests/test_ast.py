"""Unit tests for the AST/griffe parser.

Exercises the public API of core/parsers/ast.py which underpins every
doctrine test. A false negative here means a doctrine violation slips
through silently.
"""

import pytest

from julee.core.parsers.ast import (
    _imported_class_names,
    parse_module_docstring,
    parse_pipelines_from_file,
    parse_python_classes,
    parse_python_classes_from_file,
)

pytestmark = pytest.mark.unit


# =============================================================================
# Helpers
# =============================================================================


def _write(path, content):
    path.write_text(content, encoding="utf-8")


def _make_package(tmp_path, name, source):
    """Create a Python package with a single module."""
    pkg = tmp_path / name
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    module = pkg / f"{name}.py"
    _write(module, source)
    return module


# =============================================================================
# parse_python_classes
# =============================================================================


class TestParsePythonClasses:
    """Tests for directory-level class extraction."""

    def test_finds_classes_in_directory(self, tmp_path):
        _write(
            tmp_path / "models.py",
            '''\
"""Models."""
from pydantic import BaseModel

class Foo(BaseModel):
    """A foo."""
    name: str

class Bar(BaseModel):
    """A bar."""
    value: int
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert names == ["Bar", "Foo"]

    def test_extracts_bases(self, tmp_path):
        _write(
            tmp_path / "entity.py",
            '''\
"""Entity."""
from pydantic import BaseModel

class MyEntity(BaseModel):
    """An entity."""
    name: str
''',
        )
        classes = parse_python_classes(tmp_path)
        assert len(classes) == 1
        assert "BaseModel" in classes[0].bases

    def test_extracts_fields_with_annotations(self, tmp_path):
        _write(
            tmp_path / "entity.py",
            '''\
"""Entity."""
from pydantic import BaseModel

class Thing(BaseModel):
    """A thing."""
    name: str
    count: int = 0
''',
        )
        classes = parse_python_classes(tmp_path)
        field_names = [f.name for f in classes[0].fields]
        assert "name" in field_names
        assert "count" in field_names

    def test_extracts_public_methods(self, tmp_path):
        _write(
            tmp_path / "uc.py",
            '''\
"""Use case."""

class MyUseCase:
    """A use case."""
    async def execute(self, request) -> None:
        """Run it."""
        pass

    def _private(self):
        pass
''',
        )
        classes = parse_python_classes(tmp_path)
        method_names = [m.name for m in classes[0].methods]
        assert "execute" in method_names
        assert "_private" not in method_names

    def test_extracts_docstrings(self, tmp_path):
        _write(
            tmp_path / "entity.py",
            '''\
"""Entity."""
from pydantic import BaseModel

class Documented(BaseModel):
    """This is the first line.

    More detail here.
    """
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        assert classes[0].docstring == "This is the first line."

    def test_returns_sorted_by_name(self, tmp_path):
        _write(
            tmp_path / "models.py",
            '''\
"""Models."""

class Zebra:
    """Z."""
    pass

class Alpha:
    """A."""
    pass

class Middle:
    """M."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert names == ["Alpha", "Middle", "Zebra"]

    def test_skips_underscore_prefixed_files(self, tmp_path):
        _write(
            tmp_path / "_internal.py",
            '''\
"""Internal."""

class Hidden:
    """Should not appear."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        assert classes == []

    def test_skips_test_files_by_default(self, tmp_path):
        _write(
            tmp_path / "test_models.py",
            '''\
"""Tests."""

class TestFoo:
    """A test."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        assert classes == []

    def test_includes_test_files_when_exclude_tests_false(self, tmp_path):
        _write(
            tmp_path / "test_models.py",
            '''\
"""Tests."""

class SomeHelper:
    """A helper in test file."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path, exclude_tests=False)
        names = [c.name for c in classes]
        assert "SomeHelper" in names

    def test_skips_files_in_tests_subdirectory(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write(
            tests_dir / "helpers.py",
            '''\
"""Helpers."""

class TestHelper:
    """A helper."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        assert classes == []

    def test_respects_exclude_files(self, tmp_path):
        _write(
            tmp_path / "requests.py",
            '''\
"""Requests."""

class FooRequest:
    """A request."""
    pass
''',
        )
        _write(
            tmp_path / "models.py",
            '''\
"""Models."""

class Bar:
    """A bar."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path, exclude_files=["requests.py"])
        names = [c.name for c in classes]
        assert "FooRequest" not in names
        assert "Bar" in names

    def test_nonrecursive_skips_subdirectories(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        _write(
            sub / "deep.py",
            '''\
"""Deep."""

class DeepClass:
    """Nested."""
    pass
''',
        )
        _write(
            tmp_path / "top.py",
            '''\
"""Top."""

class TopClass:
    """At the top."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path, recursive=False)
        names = [c.name for c in classes]
        assert "TopClass" in names
        assert "DeepClass" not in names

    def test_nonexistent_directory_returns_empty(self, tmp_path):
        classes = parse_python_classes(tmp_path / "does_not_exist")
        assert classes == []

    def test_empty_directory_returns_empty(self, tmp_path):
        classes = parse_python_classes(tmp_path)
        assert classes == []

    def test_syntax_error_file_is_skipped(self, tmp_path):
        _write(tmp_path / "broken.py", "class Broken(\n")
        _write(
            tmp_path / "good.py",
            '''\
"""Good."""

class Good:
    """Fine."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert "Good" in names
        assert "Broken" not in names


# =============================================================================
# parse_python_classes_from_file
# =============================================================================


class TestParsePythonClassesFromFile:
    """Tests for single-file class extraction."""

    def test_extracts_classes_from_single_file(self, tmp_path):
        f = tmp_path / "models.py"
        _write(
            f,
            '''\
"""Models."""
from pydantic import BaseModel

class Alpha(BaseModel):
    """A."""
    name: str

class Beta(BaseModel):
    """B."""
    value: int
''',
        )
        classes = parse_python_classes_from_file(f)
        names = [c.name for c in classes]
        assert names == ["Alpha", "Beta"]

    def test_nonexistent_file_returns_empty(self, tmp_path):
        classes = parse_python_classes_from_file(tmp_path / "missing.py")
        assert classes == []


# =============================================================================
# parse_module_docstring
# =============================================================================


class TestParseModuleDocstring:
    """Tests for module docstring extraction."""

    def test_extracts_first_line(self, tmp_path):
        f = tmp_path / "mod.py"
        _write(
            f,
            '''\
"""First line of docstring.

More detail here.
"""

x = 1
''',
        )
        first, full = parse_module_docstring(f)
        assert first == "First line of docstring."
        assert "More detail" in full

    def test_no_docstring_returns_none(self, tmp_path):
        f = tmp_path / "mod.py"
        _write(f, "x = 1\n")
        first, full = parse_module_docstring(f)
        assert first is None
        assert full is None

    def test_nonexistent_file_returns_none(self, tmp_path):
        first, full = parse_module_docstring(tmp_path / "missing.py")
        assert first is None
        assert full is None


# =============================================================================
# _imported_class_names
# =============================================================================


class TestImportedClassNames:
    """Tests for import scanning (used for generated Request/Response detection)."""

    def test_finds_imported_names(self, tmp_path):
        _write(
            tmp_path / "use_case.py",
            """\
from some.generated.module import CreateFooRequest, CreateFooResponse
from other import SomeUseCase
""",
        )
        names = _imported_class_names(tmp_path)
        assert "CreateFooRequest" in names
        assert "CreateFooResponse" in names
        assert "SomeUseCase" in names

    def test_handles_aliased_imports(self, tmp_path):
        _write(
            tmp_path / "uc.py",
            "from generated import CreateBarRequest as CBR\n",
        )
        names = _imported_class_names(tmp_path)
        assert "CBR" in names

    def test_skips_underscore_prefixed_files(self, tmp_path):
        _write(
            tmp_path / "_generated.py",
            "from module import HiddenRequest\n",
        )
        names = _imported_class_names(tmp_path)
        assert "HiddenRequest" not in names

    def test_empty_directory_returns_empty(self, tmp_path):
        names = _imported_class_names(tmp_path)
        assert names == set()

    def test_nonexistent_directory_returns_empty(self, tmp_path):
        names = _imported_class_names(tmp_path / "nope")
        assert names == set()

    def test_syntax_error_file_is_skipped(self, tmp_path):
        _write(tmp_path / "broken.py", "from import\n")
        _write(tmp_path / "good.py", "from module import GoodRequest\n")
        names = _imported_class_names(tmp_path)
        assert "GoodRequest" in names


# =============================================================================
# parse_pipelines_from_file
# =============================================================================


class TestParsePipelinesFromFile:
    """Tests for pipeline class detection."""

    def test_detects_pipeline_by_suffix(self, tmp_path):
        f = tmp_path / "pipelines.py"
        _write(
            f,
            '''\
"""Pipelines."""
from temporalio import workflow

@workflow.defn
class FooPipeline:
    """Foo pipeline."""
    @workflow.run
    async def run(self):
        pass
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert len(pipelines) == 1
        assert pipelines[0].name == "FooPipeline"
        assert pipelines[0].has_workflow_decorator is True
        assert pipelines[0].has_run_method is True
        assert pipelines[0].has_run_decorator is True

    def test_detects_pipeline_by_workflow_decorator(self, tmp_path):
        f = tmp_path / "workflows.py"
        _write(
            f,
            '''\
"""Workflows."""
from temporalio import workflow

@workflow.defn
class SomeWorkflow:
    """A workflow (not named Pipeline but has decorator)."""
    @workflow.run
    async def run(self):
        pass
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert len(pipelines) == 1

    def test_ignores_classes_without_pipeline_suffix_or_decorator(self, tmp_path):
        f = tmp_path / "models.py"
        _write(
            f,
            '''\
"""Models."""

class SomeHelper:
    """Just a class — no Pipeline suffix, no @workflow.defn."""
    pass
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert pipelines == []

    def test_detects_use_case_delegation(self, tmp_path):
        f = tmp_path / "pipelines.py"
        _write(
            f,
            '''\
"""Pipelines."""
from temporalio import workflow

@workflow.defn
class DoThingPipeline:
    """Does the thing."""
    @workflow.run
    async def run(self):
        uc = DoThingUseCase(self.repo)
        result = await uc.execute(request)
        return result
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert pipelines[0].delegates_to_use_case is True
        assert pipelines[0].wrapped_use_case == "DoThingUseCase"

    def test_detects_run_next_method(self, tmp_path):
        f = tmp_path / "pipelines.py"
        _write(
            f,
            '''\
"""Pipelines."""
from temporalio import workflow

@workflow.defn
class RoutingPipeline:
    """Routes to next step."""
    @workflow.run
    async def run(self):
        uc = RoutingUseCase(self.repo)
        result = await uc.execute(request)
        await self.run_next(result)
        return result

    async def run_next(self, result):
        pass
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert pipelines[0].has_run_next_method is True
        assert pipelines[0].run_calls_run_next is True

    def test_nonexistent_file_returns_empty(self, tmp_path):
        pipelines = parse_pipelines_from_file(tmp_path / "missing.py")
        assert pipelines == []

    def test_syntax_error_returns_empty(self, tmp_path):
        f = tmp_path / "broken.py"
        _write(f, "class Broken(\n")
        pipelines = parse_pipelines_from_file(f)
        assert pipelines == []

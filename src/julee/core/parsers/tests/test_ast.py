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

    def test_extracts_fields_with_type_annotations_and_defaults(self, tmp_path):
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
        fields = {f.name: f for f in classes[0].fields}
        assert "name" in fields
        assert "count" in fields
        assert "str" in fields["name"].type_annotation
        assert "int" in fields["count"].type_annotation
        assert fields["count"].default is not None
        assert "0" in fields["count"].default

    def test_extracts_method_details(self, tmp_path):
        _write(
            tmp_path / "uc.py",
            '''\
"""Use case."""

class MyUseCase:
    """A use case."""
    async def execute(self, request: str) -> bool:
        """Run it."""
        pass

    def sync_method(self, x: int) -> None:
        """Sync."""
        pass

    def _private(self):
        pass
''',
        )
        classes = parse_python_classes(tmp_path)
        methods = {m.name: m for m in classes[0].methods}
        # Private methods excluded
        assert "_private" not in methods
        # execute is async
        assert methods["execute"].is_async is True
        assert methods["sync_method"].is_async is False
        # Parameters extracted (excluding self)
        assert len(methods["execute"].parameters) == 1
        assert methods["execute"].parameters[0].name == "request"
        assert "str" in methods["execute"].parameters[0].type_annotation
        # Return types
        assert "bool" in methods["execute"].return_type
        # Docstrings
        assert methods["execute"].docstring == "Run it."
        assert methods["sync_method"].docstring == "Sync."

    def test_class_without_docstring_gets_empty_string(self, tmp_path):
        _write(
            tmp_path / "nodoc.py",
            '''\
"""Module."""

class NoDocs:
    name: str = "x"
''',
        )
        classes = parse_python_classes(tmp_path)
        assert classes[0].docstring == ""

    def test_extracts_multiline_docstring_first_line(self, tmp_path):
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

    def test_file_path_is_relative_to_directory(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        _write(
            sub / "models.py",
            '''\
"""Models."""

class InSub:
    """In sub."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        assert classes[0].file == "sub/models.py"

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
        _write(
            tmp_path / "visible.py",
            '''\
"""Visible."""

class Visible:
    """Should appear."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert "Hidden" not in names
        assert "Visible" in names

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
        _write(
            tmp_path / "models.py",
            '''\
"""Models."""

class RealModel:
    """A model."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert "TestFoo" not in names
        assert "RealModel" in names

    def test_skips_test_prefixed_classes_even_in_non_test_file(self, tmp_path):
        _write(
            tmp_path / "helpers.py",
            '''\
"""Helpers."""

class TestHelper:
    """Has Test prefix."""
    pass

class RealHelper:
    """No Test prefix."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert "TestHelper" not in names
        assert "RealHelper" in names

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

class SomeClass:
    """A class in tests dir."""
    pass
''',
        )
        _write(
            tmp_path / "real.py",
            '''\
"""Real."""

class RealClass:
    """Outside tests."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert "SomeClass" not in names
        assert "RealClass" in names

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

    def test_recursive_true_by_default_includes_subdirs(self, tmp_path):
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
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert "TopClass" in names
        assert "DeepClass" in names

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

    def test_syntax_error_file_is_skipped_others_survive(self, tmp_path):
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
        _write(
            tmp_path / "also_good.py",
            '''\
"""Also good."""

class AlsoGood:
    """Also fine."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert "Good" in names
        assert "AlsoGood" in names
        assert "Broken" not in names

    def test_multiple_files_all_scanned(self, tmp_path):
        """Ensures continue (not break) on skip conditions."""
        _write(
            tmp_path / "aaa.py",
            '''\
"""A."""

class FromA:
    """From A."""
    pass
''',
        )
        _write(
            tmp_path / "bbb.py",
            '''\
"""B."""

class FromB:
    """From B."""
    pass
''',
        )
        _write(
            tmp_path / "ccc.py",
            '''\
"""C."""

class FromC:
    """From C."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert len(names) == 3
        assert "FromA" in names
        assert "FromB" in names
        assert "FromC" in names


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
        assert full is not None
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

    def test_dotted_import_uses_last_component(self, tmp_path):
        _write(
            tmp_path / "uc.py",
            "from pkg.sub.module import SomeName\n",
        )
        names = _imported_class_names(tmp_path)
        assert "SomeName" in names

    def test_skips_underscore_prefixed_files(self, tmp_path):
        _write(
            tmp_path / "_generated.py",
            "from module import HiddenRequest\n",
        )
        names = _imported_class_names(tmp_path)
        assert "HiddenRequest" not in names

    def test_scans_multiple_files(self, tmp_path):
        """Ensures continue (not break) when iterating files."""
        _write(tmp_path / "aaa.py", "from mod import AlphaRequest\n")
        _write(tmp_path / "bbb.py", "from mod import BetaRequest\n")
        _write(tmp_path / "ccc.py", "from mod import GammaRequest\n")
        names = _imported_class_names(tmp_path)
        assert "AlphaRequest" in names
        assert "BetaRequest" in names
        assert "GammaRequest" in names

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

    def test_detects_pipeline_with_all_fields(self, tmp_path):
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
    async def run(self, request: str) -> bool:
        """Run the pipeline."""
        pass
''',
        )
        pipelines = parse_pipelines_from_file(f, bounded_context="billing")
        assert len(pipelines) == 1
        p = pipelines[0]
        assert p.name == "FooPipeline"
        assert p.docstring == "Foo pipeline."
        assert p.file == "pipelines.py"
        assert p.bounded_context == "billing"
        assert p.has_workflow_decorator is True
        assert p.has_run_method is True
        assert p.has_run_decorator is True
        assert p.delegates_to_use_case is False
        assert p.has_run_next_method is False
        assert p.run_next_has_workflow_decorator is False
        assert p.run_calls_run_next is False
        assert p.sets_dispatches_on_response is False
        # Method extraction
        run_methods = [m for m in p.methods if m.name == "run"]
        assert len(run_methods) == 1
        assert run_methods[0].is_async is True
        assert len(run_methods[0].parameters) == 1
        assert run_methods[0].parameters[0].name == "request"

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
        assert pipelines[0].name == "SomeWorkflow"

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

    def test_no_delegation_without_use_case(self, tmp_path):
        f = tmp_path / "pipelines.py"
        _write(
            f,
            '''\
"""Pipelines."""
from temporalio import workflow

@workflow.defn
class SimplePipeline:
    """No use case."""
    @workflow.run
    async def run(self):
        return "done"
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert pipelines[0].delegates_to_use_case is False
        assert pipelines[0].wrapped_use_case is None

    def test_detects_run_next_and_dispatches(self, tmp_path):
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
        result.dispatches = await self.run_next(result)
        return result

    async def run_next(self, result):
        return []
''',
        )
        pipelines = parse_pipelines_from_file(f)
        p = pipelines[0]
        assert p.has_run_next_method is True
        assert p.run_calls_run_next is True
        assert p.sets_dispatches_on_response is True
        assert p.run_next_has_workflow_decorator is False

    def test_run_next_with_workflow_run_detected(self, tmp_path):
        f = tmp_path / "pipelines.py"
        _write(
            f,
            '''\
"""Pipelines."""
from temporalio import workflow

@workflow.defn
class BadPipeline:
    """run_next should not have workflow.run."""
    @workflow.run
    async def run(self):
        await self.run_next()

    @workflow.run
    async def run_next(self):
        pass
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert pipelines[0].run_next_has_workflow_decorator is True

    def test_multiple_pipelines_returned_sorted(self, tmp_path):
        f = tmp_path / "pipelines.py"
        _write(
            f,
            '''\
"""Pipelines."""
from temporalio import workflow

@workflow.defn
class ZebraPipeline:
    """Z."""
    @workflow.run
    async def run(self):
        pass

@workflow.defn
class AlphaPipeline:
    """A."""
    @workflow.run
    async def run(self):
        pass
''',
        )
        pipelines = parse_pipelines_from_file(f)
        names = [p.name for p in pipelines]
        assert names == ["AlphaPipeline", "ZebraPipeline"]

    def test_default_bounded_context_is_empty(self, tmp_path):
        f = tmp_path / "pipelines.py"
        _write(
            f,
            '''\
"""Pipelines."""
from temporalio import workflow

@workflow.defn
class XPipeline:
    """X."""
    @workflow.run
    async def run(self):
        pass
''',
        )
        pipelines = parse_pipelines_from_file(f)
        assert pipelines[0].bounded_context == ""

    def test_nonexistent_file_returns_empty(self, tmp_path):
        pipelines = parse_pipelines_from_file(tmp_path / "missing.py")
        assert pipelines == []

    def test_syntax_error_returns_empty(self, tmp_path):
        f = tmp_path / "broken.py"
        _write(f, "class Broken(\n")
        pipelines = parse_pipelines_from_file(f)
        assert pipelines == []

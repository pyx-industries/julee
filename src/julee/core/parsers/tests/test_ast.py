"""Unit tests for the AST/griffe parser.

Exercises the public API of core/parsers/ast.py which underpins every
doctrine test. A false negative here means a doctrine violation slips
through silently.
"""

import pytest

from julee.core.parsers.ast import (
    _imported_class_names,
    parse_bounded_context,
    parse_module_docstring,
    parse_pipelines_from_file,
    parse_python_classes,
    parse_python_classes_from_file,
    unreadable_python_files,
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

    def test_reads_underscore_prefixed_files(self, tmp_path):
        """An underscore on a file name hides nothing (ADR 021)."""
        _write(
            tmp_path / "_internal.py",
            '''\
"""Internal."""

class Internal:
    """Should appear."""
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
        assert names == ["Internal", "Visible"]

    def test_reads_a_class_out_of_a_package_init(self, tmp_path):
        """No module is left out for what it is called (ADR 021)."""
        _write(tmp_path / "__init__.py", "class InThePackage:\n    pass\n")
        _write(tmp_path / "__main__.py", "class Runner:\n    pass\n")

        names = [c.name for c in parse_python_classes(tmp_path)]

        assert names == ["InThePackage", "Runner"]

    def test_a_class_a_package_init_imports_is_not_read_twice(self, tmp_path):
        """A re-export is an import. The class is declared where it is
        written, and read there once."""
        _write(tmp_path / "story.py", "class Story:\n    pass\n")
        _write(tmp_path / "__init__.py", "from .story import Story\n")

        classes = parse_python_classes(tmp_path)

        assert [(c.name, c.file) for c in classes] == [("Story", "story.py")]

    def test_a_broken_module_is_not_reported_against_its_package_init(self, tmp_path):
        """Each file is loaded alone, so each answers for itself."""
        _write(tmp_path / "__init__.py", '"""A package."""\n')
        _write(tmp_path / "broken.py", "class Broken(\n")

        found = unreadable_python_files(tmp_path)

        assert [f.file for f in found] == ["broken.py"]

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

    def test_reads_test_prefixed_classes_in_a_file_that_is_not_a_test(self, tmp_path):
        """A test is left out by its file. A name beginning Test is a name,
        and a domain can have a TestResult or a Testimonial (ADR 021)."""
        _write(
            tmp_path / "results.py",
            '''\
"""Results."""

class TestResult:
    """Has Test prefix."""
    pass

class Testimonial:
    """Only begins the same way."""
    pass

class ExamResult:
    """No Test prefix."""
    pass
''',
        )
        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert names == ["ExamResult", "TestResult", "Testimonial"]

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

    def test_reads_underscore_prefixed_files(self, tmp_path):
        """A use case in such a file is read, so its imports are too."""
        _write(
            tmp_path / "_generated.py",
            "from module import GeneratedRequest\n",
        )
        names = _imported_class_names(tmp_path)
        assert "GeneratedRequest" in names

    def test_reads_a_package_init(self, tmp_path):
        _write(tmp_path / "__init__.py", "from module import PackageRequest\n")
        names = _imported_class_names(tmp_path)
        assert "PackageRequest" in names

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


# =============================================================================
# Decorators
# =============================================================================


class TestDecorators:
    """Tests for the decorator paths a ClassInfo carries.

    Doctrine reads these to find classes marked by a decorator without
    importing the module that defines them, so what matters is that the
    import is followed: the same decorator spelled three ways must be
    recognisable as one decorator.
    """

    def test_an_undecorated_class_carries_no_decorators(self, tmp_path):
        _write(tmp_path / "m.py", "class Plain:\n    pass\n")

        (plain,) = parse_python_classes(tmp_path)

        assert plain.decorators == ()

    def test_a_decorator_is_recorded_by_its_resolved_path(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from julee.integrations.temporal.decorators import "
            "temporal_activity_registration\n"
            "\n"
            "@temporal_activity_registration\n"
            "class Repo:\n"
            "    pass\n",
        )

        (repo,) = parse_python_classes(tmp_path)

        assert repo.decorators == (
            "julee.integrations.temporal.decorators.temporal_activity_registration",
        )

    def test_a_called_decorator_resolves_to_the_same_path(self, tmp_path):
        """`@deco("x")` and `@deco` are the same decorator."""
        _write(
            tmp_path / "m.py",
            "from julee.integrations.temporal.decorators import "
            "temporal_activity_registration\n"
            "\n"
            '@temporal_activity_registration("util.file_storage.minio")\n'
            "class Repo:\n"
            "    pass\n",
        )

        (repo,) = parse_python_classes(tmp_path)

        assert repo.decorators == (
            "julee.integrations.temporal.decorators.temporal_activity_registration",
        )

    def test_an_attribute_decorator_resolves_through_the_module(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "import julee.integrations.temporal as t\n"
            "\n"
            "@t.temporal_activity_registration\n"
            "class Repo:\n"
            "    pass\n",
        )

        (repo,) = parse_python_classes(tmp_path)

        assert repo.decorated_with("temporal_activity_registration")

    def test_several_decorators_are_all_recorded_in_order(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from dataclasses import dataclass\n"
            "from typing import final\n"
            "\n"
            "@final\n"
            "@dataclass\n"
            "class Both:\n"
            "    pass\n",
        )

        (both,) = parse_python_classes(tmp_path)

        assert both.decorators == ("typing.final", "dataclasses.dataclass")

    def test_decorated_with_ignores_a_name_that_merely_ends_the_same(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from elsewhere import my_registration\n"
            "\n"
            "@my_registration\n"
            "class Repo:\n"
            "    pass\n",
        )

        (repo,) = parse_python_classes(tmp_path)

        assert not repo.decorated_with("registration")


class TestDecoratorArguments:
    """Tests for the keyword arguments a decorator was called with.

    Source text rather than values, because a class is read and not
    imported. Doctrine needs this to tell ``@dataclass(frozen=True)``
    from ``@dataclass``, which is the difference between an immutable
    entity and a mutable one (#142).
    """

    def test_a_bare_decorator_records_no_arguments(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from dataclasses import dataclass\n\n@dataclass\nclass Thing:\n    pass\n",
        )

        (thing,) = parse_python_classes(tmp_path)

        assert thing.decorator_arguments == {}
        assert thing.decorator_argument("dataclass", "frozen") is None

    def test_a_keyword_is_recorded_under_the_decorator_name(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from dataclasses import dataclass\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class Thing:\n"
            "    pass\n",
        )

        (thing,) = parse_python_classes(tmp_path)

        assert thing.decorator_arguments == {"dataclass": {"frozen": "True"}}
        assert thing.decorator_argument("dataclass", "frozen") == "True"

    def test_several_keywords_are_all_recorded(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from dataclasses import dataclass\n"
            "\n"
            "@dataclass(frozen=True, slots=True)\n"
            "class Thing:\n"
            "    pass\n",
        )

        (thing,) = parse_python_classes(tmp_path)

        assert thing.decorator_arguments["dataclass"] == {
            "frozen": "True",
            "slots": "True",
        }

    def test_an_argument_is_source_text_not_a_value(self, tmp_path):
        """A constant cannot be resolved without importing, so what comes
        back is what was written. A caller decides what to make of it."""
        _write(
            tmp_path / "m.py",
            "from dataclasses import dataclass\n"
            "\n"
            "FROZEN = True\n"
            "\n"
            "@dataclass(frozen=FROZEN)\n"
            "class Thing:\n"
            "    pass\n",
        )

        (thing,) = parse_python_classes(tmp_path)

        assert thing.decorator_argument("dataclass", "frozen") == "FROZEN"

    def test_a_positional_argument_is_not_a_keyword(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from julee.integrations.temporal.decorators import "
            "temporal_activity_registration\n"
            "\n"
            '@temporal_activity_registration("util.file_storage.minio")\n'
            "class Repo:\n"
            "    pass\n",
        )

        (repo,) = parse_python_classes(tmp_path)

        assert repo.decorator_arguments == {}

    def test_an_unasked_decorator_gives_nothing(self, tmp_path):
        _write(
            tmp_path / "m.py",
            "from dataclasses import dataclass\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class Thing:\n"
            "    pass\n",
        )

        (thing,) = parse_python_classes(tmp_path)

        assert thing.decorator_argument("attrs", "frozen") is None
        assert thing.decorator_argument("dataclass", "slots") is None


# =============================================================================
# unreadable_python_files
# =============================================================================


class TestUnreadablePythonFiles:
    """What parse_python_classes went to read and could not.

    parse_python_classes answers the same for a directory with a broken
    file as for one without it. This is the other half of that answer.
    """

    def test_a_directory_that_parses_has_none(self, tmp_path):
        _write(tmp_path / "good.py", "class Good:\n    pass\n")

        assert unreadable_python_files(tmp_path) == []

    def test_a_nonexistent_directory_has_none(self, tmp_path):
        assert unreadable_python_files(tmp_path / "does_not_exist") == []

    def test_a_file_that_does_not_parse_is_reported(self, tmp_path):
        _write(tmp_path / "good.py", "class Good:\n    pass\n")
        _write(tmp_path / "broken.py", "class Broken(\n")

        (found,) = unreadable_python_files(tmp_path)

        assert found.file == "broken.py"

    def test_the_problem_names_the_line(self, tmp_path):
        _write(tmp_path / "broken.py", "x = 1\n\ndef broken(:\n")

        (found,) = unreadable_python_files(tmp_path)

        assert "line 3" in found.problem

    def test_a_file_that_is_not_utf8_is_reported(self, tmp_path):
        (tmp_path / "latin.py").write_bytes(b'x = "\xff\xfe"\n')

        (found,) = unreadable_python_files(tmp_path)

        assert found.file == "latin.py"
        assert "UnicodeDecodeError" in found.problem

    def test_it_reports_exactly_what_parse_python_classes_lost(self, tmp_path):
        """The classes of the other files are still returned."""
        _write(tmp_path / "broken.py", "class Broken(\n")
        _write(tmp_path / "good.py", "class Good:\n    pass\n")

        assert [c.name for c in parse_python_classes(tmp_path)] == ["Good"]
        assert [f.file for f in unreadable_python_files(tmp_path)] == ["broken.py"]

    def test_a_broken_underscore_file_is_reported(self, tmp_path):
        """parse_python_classes reads it, so it is asked to parse."""
        _write(tmp_path / "_private.py", "class Broken(\n")

        (found,) = unreadable_python_files(tmp_path)

        assert found.file == "_private.py"

    def test_a_broken_package_init_is_reported(self, tmp_path):
        _write(tmp_path / "__init__.py", "class Broken(\n")

        (found,) = unreadable_python_files(tmp_path)

        assert found.file == "__init__.py"

    def test_a_broken_test_file_is_not_reported(self, tmp_path):
        _write(tmp_path / "test_thing.py", "class Broken(\n")
        (tmp_path / "tests").mkdir()
        _write(tmp_path / "tests" / "helper.py", "class Broken(\n")

        assert unreadable_python_files(tmp_path) == []

    def test_a_broken_test_file_is_reported_when_tests_are_read(self, tmp_path):
        _write(tmp_path / "test_thing.py", "class Broken(\n")

        (found,) = unreadable_python_files(tmp_path, exclude_tests=False)

        assert found.file == "test_thing.py"

    def test_an_excluded_file_is_not_reported(self, tmp_path):
        _write(tmp_path / "requests.py", "class Broken(\n")

        assert unreadable_python_files(tmp_path, exclude_files=["requests.py"]) == []

    def test_nonrecursive_does_not_report_subdirectories(self, tmp_path):
        (tmp_path / "sub").mkdir()
        _write(tmp_path / "sub" / "broken.py", "class Broken(\n")

        assert unreadable_python_files(tmp_path, recursive=False) == []

    def test_paths_are_relative_to_the_directory_by_default(self, tmp_path):
        (tmp_path / "sub").mkdir()
        _write(tmp_path / "sub" / "broken.py", "class Broken(\n")

        (found,) = unreadable_python_files(tmp_path)

        assert found.file == "sub/broken.py"

    def test_paths_can_be_reported_against_somewhere_else(self, tmp_path):
        context = tmp_path / "src" / "acme"
        context.mkdir(parents=True)
        _write(context / "broken.py", "class Broken(\n")

        (found,) = unreadable_python_files(context, relative_to=tmp_path)

        assert found.file == "src/acme/broken.py"

    def test_several_are_sorted_by_path(self, tmp_path):
        _write(tmp_path / "zebra.py", "class Broken(\n")
        _write(tmp_path / "alpha.py", "class Broken(\n")

        found = unreadable_python_files(tmp_path)

        assert [f.file for f in found] == ["alpha.py", "zebra.py"]


# =============================================================================
# parse_bounded_context: the use case family
# =============================================================================


class TestTheUseCaseFamily:
    """A class in usecases/ is a use case, whatever it is called (ADR 020)."""

    @staticmethod
    def _context(tmp_path, source):
        context = tmp_path / "stories"
        (context / "usecases").mkdir(parents=True)
        _write(context / "usecases" / "plan.py", source)
        return context

    @staticmethod
    def _use_cases(context):
        info = parse_bounded_context(context)
        assert info is not None
        return [found.name for found in info.use_cases]

    def test_a_class_named_UseCase_is_one(self, tmp_path):
        context = self._context(tmp_path, "class PlanStoryUseCase:\n    pass\n")

        assert self._use_cases(context) == ["PlanStoryUseCase"]

    def test_a_class_named_anything_else_is_one_too(self, tmp_path):
        """Found by the directory, so that its name can be objected to."""
        context = self._context(
            tmp_path,
            "class PlanStory:\n    pass\n\n\nclass StoryHelpers:\n    pass\n",
        )

        assert self._use_cases(context) == ["PlanStory", "StoryHelpers"]

    def test_a_class_without_execute_is_one_too(self, tmp_path):
        """Whether it can be executed is a rule, not the definition."""
        context = self._context(
            tmp_path,
            "class BaseUseCase:\n"
            "    def __init__(self, repo):\n"
            "        self.repo = repo\n",
        )

        assert self._use_cases(context) == ["BaseUseCase"]

    def test_a_request_and_a_response_are_messages_not_use_cases(self, tmp_path):
        context = self._context(
            tmp_path,
            "class PlanStoryRequest:\n    pass\n\n\n"
            "class PlanStoryResponse:\n    pass\n\n\n"
            "class PlanStoryUseCase:\n    pass\n",
        )
        info = parse_bounded_context(context)
        assert info is not None

        assert [found.name for found in info.use_cases] == ["PlanStoryUseCase"]
        assert [found.name for found in info.requests] == ["PlanStoryRequest"]
        assert [found.name for found in info.responses] == ["PlanStoryResponse"]

    def test_an_imported_class_is_not_one(self, tmp_path):
        """A use case is declared in usecases/, not merely named there."""
        context = self._context(
            tmp_path,
            "from acme.stories.domain.models.story import Story\n"
            "from ..dtos.plan import PlanStoryRequest\n\n\n"
            "class PlanStoryUseCase:\n    pass\n",
        )

        assert self._use_cases(context) == ["PlanStoryUseCase"]

    def test_a_class_in_a_subdirectory_is_one(self, tmp_path):
        context = self._context(tmp_path, "class PlanStoryUseCase:\n    pass\n")
        (context / "usecases" / "ports").mkdir()
        _write(context / "usecases" / "ports" / "clock.py", "class Clock:\n    pass\n")

        assert self._use_cases(context) == ["Clock", "PlanStoryUseCase"]

    def test_a_class_outside_usecases_is_not_one(self, tmp_path):
        context = self._context(tmp_path, "class PlanStoryUseCase:\n    pass\n")
        (context / "infrastructure").mkdir()
        _write(context / "infrastructure" / "memory.py", "class Memory:\n    pass\n")

        assert self._use_cases(context) == ["PlanStoryUseCase"]

    def test_no_name_keeps_a_class_out(self, tmp_path):
        """Not a name beginning Test, not an underscore on the module, and
        not a package's __init__.py (ADR 021)."""
        context = self._context(
            tmp_path,
            "class TestDouble:\n    pass\n\n\nclass PlanStoryUseCase:\n    pass\n",
        )
        _write(context / "usecases" / "_private.py", "class Private:\n    pass\n")
        _write(context / "usecases" / "__init__.py", "class InInit:\n    pass\n")

        assert self._use_cases(context) == [
            "InInit",
            "PlanStoryUseCase",
            "Private",
            "TestDouble",
        ]


# =============================================================================
# parse_bounded_context: areas under domain/
# =============================================================================


class TestAreasUnderDomain:
    """A directory under domain/ that is no kind's is an area (ADR 023)."""

    @staticmethod
    def _context(tmp_path, files):
        context = tmp_path / "ledger"
        for file, source in files.items():
            (context / file).parent.mkdir(parents=True, exist_ok=True)
            _write(context / file, source)
        return context

    @staticmethod
    def _family(context, family):
        info = parse_bounded_context(context)
        assert info is not None
        return [(found.name, found.file) for found in getattr(info, family)]

    def test_a_module_an_area_holds_is_read_as_entities(self, tmp_path):
        context = self._context(
            tmp_path, {"domain/billing/invoice.py": "class Invoice:\n    pass\n"}
        )

        assert self._family(context, "entities") == [("Invoice", "billing/invoice.py")]

    def test_a_kind_directory_in_an_area_is_read_as_that_kind(self, tmp_path):
        context = self._context(
            tmp_path,
            {
                "domain/billing/invoice.py": "class Invoice:\n    pass\n",
                "domain/billing/repositories/invoice.py": (
                    "class InvoiceRepository:\n    pass\n"
                ),
                "domain/billing/values/money.py": "class Money:\n    pass\n",
                "domain/billing/oracles/rates.py": "class RatesOracle:\n    pass\n",
            },
        )

        assert self._family(context, "entities") == [("Invoice", "billing/invoice.py")]
        assert self._family(context, "repository_protocols") == [
            ("InvoiceRepository", "billing/repositories/invoice.py")
        ]
        assert self._family(context, "values") == [("Money", "billing/values/money.py")]
        assert self._family(context, "oracle_protocols") == [
            ("RatesOracle", "billing/oracles/rates.py")
        ]

    def test_a_models_directory_in_an_area_holds_entities_too(self, tmp_path):
        context = self._context(
            tmp_path,
            {
                "domain/billing/invoice.py": "class Invoice:\n    pass\n",
                "domain/billing/models/refund.py": "class Refund:\n    pass\n",
            },
        )

        assert self._family(context, "entities") == [
            ("Invoice", "billing/invoice.py"),
            ("Refund", "billing/models/refund.py"),
        ]

    def test_areas_are_read_beside_the_layers_own_directories(self, tmp_path):
        context = self._context(
            tmp_path,
            {
                "domain/models/customer.py": "class Customer:\n    pass\n",
                "domain/repositories/customer.py": (
                    "class CustomerRepository:\n    pass\n"
                ),
                "domain/billing/invoice.py": "class Invoice:\n    pass\n",
                "domain/billing/repositories/invoice.py": (
                    "class InvoiceRepository:\n    pass\n"
                ),
            },
        )

        assert self._family(context, "entities") == [
            ("Customer", "customer.py"),
            ("Invoice", "billing/invoice.py"),
        ]
        assert self._family(context, "repository_protocols") == [
            ("CustomerRepository", "customer.py"),
            ("InvoiceRepository", "billing/repositories/invoice.py"),
        ]

    def test_an_area_inside_an_area_is_read_the_same_way(self, tmp_path):
        context = self._context(
            tmp_path,
            {
                "domain/billing/refunds/refund.py": "class Refund:\n    pass\n",
                "domain/billing/refunds/repositories/refund.py": (
                    "class RefundRepository:\n    pass\n"
                ),
            },
        )

        assert self._family(context, "entities") == [
            ("Refund", "billing/refunds/refund.py")
        ]
        assert self._family(context, "repository_protocols") == [
            ("RefundRepository", "billing/refunds/repositories/refund.py")
        ]

    def test_a_handler_in_an_areas_services_is_read_as_a_handler(self, tmp_path):
        """As one in domain/services/ is, while it waits to be moved."""
        context = self._context(
            tmp_path,
            {
                "domain/billing/services/billing.py": (
                    "class BillingService:\n    pass\n\n\n"
                    "class OverdueHandler:\n    pass\n"
                ),
                "domain/billing/handlers/paid_handler.py": (
                    "class PaidHandler:\n    pass\n"
                ),
            },
        )

        assert [name for name, _ in self._family(context, "service_protocols")] == [
            "BillingService"
        ]
        assert [name for name, _ in self._family(context, "handler_protocols")] == [
            "PaidHandler",
            "OverdueHandler",
        ]

    def test_a_class_under_a_kind_directory_is_read_once(self, tmp_path):
        """A subdirectory of domain/models/ is more models, not an area."""
        context = self._context(
            tmp_path,
            {"domain/models/billing/invoice.py": "class Invoice:\n    pass\n"},
        )

        assert self._family(context, "entities") == [("Invoice", "billing/invoice.py")]

    def test_a_module_directly_under_domain_is_read_by_no_family(self, tmp_path):
        context = self._context(
            tmp_path,
            {
                "domain/errors.py": "class NotFound(Exception):\n    pass\n",
                "domain/billing/invoice.py": "class Invoice:\n    pass\n",
            },
        )

        assert self._family(context, "entities") == [("Invoice", "billing/invoice.py")]

    def test_a_test_in_an_area_is_not_read(self, tmp_path):
        context = self._context(
            tmp_path,
            {
                "domain/billing/invoice.py": "class Invoice:\n    pass\n",
                "domain/billing/test_invoice.py": "class TestInvoice:\n    pass\n",
                "domain/billing/tests/factories.py": "class Factory:\n    pass\n",
            },
        )

        assert self._family(context, "entities") == [("Invoice", "billing/invoice.py")]


# =============================================================================
# Loading a file once
# =============================================================================


class TestAFileIsLoadedOnce:
    """Doctrine scans the same directories many times in one run."""

    def test_an_unchanged_file_is_not_loaded_again(self, tmp_path, monkeypatch):
        import griffe

        _write(tmp_path / "story.py", "class Story:\n    pass\n")
        loads = []
        load = griffe.load

        def counting(name, **keywords):
            loads.append(name)
            return load(name, **keywords)

        monkeypatch.setattr(griffe, "load", counting)

        first = parse_python_classes(tmp_path)
        second = parse_python_classes(tmp_path)

        assert [c.name for c in first] == [c.name for c in second] == ["Story"]
        assert loads == ["story"]

    def test_a_changed_file_is_loaded_again(self, tmp_path):
        """Or a scan would go on reporting what the file used to hold."""
        _write(tmp_path / "story.py", "class Story:\n    pass\n")
        assert [c.name for c in parse_python_classes(tmp_path)] == ["Story"]

        _write(
            tmp_path / "story.py", "class Story:\n    pass\n\n\nclass Tale:\n    pass\n"
        )

        assert [c.name for c in parse_python_classes(tmp_path)] == ["Story", "Tale"]

    def test_a_file_that_would_not_load_is_asked_again_once_it_changes(self, tmp_path):
        _write(tmp_path / "story.py", "class Story(\n")
        assert [f.file for f in unreadable_python_files(tmp_path)] == ["story.py"]

        _write(tmp_path / "story.py", "class Story:\n    pass\n")

        assert unreadable_python_files(tmp_path) == []
        assert [c.name for c in parse_python_classes(tmp_path)] == ["Story"]

    def test_a_package_init_is_read_without_the_rest_of_its_package(self, tmp_path):
        """Griffe reads an __init__.py as the package and would load every
        module under it. The docstring is the file's own, whatever state
        the modules beside it are in."""
        _write(tmp_path / "__init__.py", '"""A package."""\n')
        _write(tmp_path / "broken.py", "class Broken(\n")

        assert parse_module_docstring(tmp_path / "__init__.py") == (
            "A package.",
            "A package.",
        )

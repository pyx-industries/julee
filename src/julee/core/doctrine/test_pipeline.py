"""Pipeline doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

A Pipeline is a UseCase that has been appropriately treated (with decorators
and proxies) to run as a Temporal workflow. The pipeline delegates to the
use case - it does NOT contain business logic directly.

See: docs/architecture/solutions/pipelines.rst
"""

from pathlib import Path
from textwrap import dedent

from julee.core.parsers.ast import parse_pipelines_from_file


def create_pipeline_file(tmp_path: Path, content: str) -> Path:
    """Helper to create a temporary Python file with pipeline code."""
    file_path = tmp_path / "pipelines.py"
    file_path.write_text(dedent(content))
    return file_path


# =============================================================================
# DOCTRINE: Pipeline Naming
# =============================================================================


class TestPipelineNaming:
    """Doctrine about pipeline naming conventions."""

    def test_pipeline_MUST_end_with_Pipeline_suffix(self, tmp_path: Path):
        """A pipeline class name MUST end with 'Pipeline'."""
        content = '''
        from temporalio import workflow

        @workflow.defn
        class ExtractAssemblePipeline:
            """Pipeline that wraps ExtractAssembleUseCase."""

            @workflow.run
            async def run(self) -> None:
                pass
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].name.endswith("Pipeline")

    def test_pipeline_name_MUST_match_wrapped_use_case(self, tmp_path: Path):
        """A pipeline named {Prefix}Pipeline MUST wrap {Prefix}UseCase or {Prefix}DataUseCase.

        Example: ExtractAssemblePipeline wraps ExtractAssembleDataUseCase
        """
        content = '''
        from temporalio import workflow

        @workflow.defn
        class ExtractAssemblePipeline:
            """Pipeline that wraps ExtractAssembleDataUseCase."""

            @workflow.run
            async def run(self) -> None:
                use_case = ExtractAssembleDataUseCase()
                return await use_case.execute()
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        pipeline = pipelines[0]
        expected = pipeline.expected_use_case_name
        assert expected == "ExtractAssembleUseCase"


# =============================================================================
# DOCTRINE: Pipeline Decorators
# =============================================================================


class TestPipelineDecorators:
    """Doctrine about pipeline decorators."""

    def test_pipeline_MUST_have_workflow_defn_decorator(self, tmp_path: Path):
        """A pipeline class MUST be decorated with @workflow.defn."""
        content = '''
        from temporalio import workflow

        @workflow.defn
        class ValidPipeline:
            """Properly decorated pipeline."""

            @workflow.run
            async def run(self) -> None:
                pass
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].has_workflow_decorator is True

    def test_pipeline_run_method_MUST_have_workflow_run_decorator(self, tmp_path: Path):
        """A pipeline's run() method MUST be decorated with @workflow.run."""
        content = '''
        from temporalio import workflow

        @workflow.defn
        class ValidPipeline:
            """Pipeline with properly decorated run method."""

            @workflow.run
            async def run(self) -> None:
                pass
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].has_run_decorator is True


# =============================================================================
# DOCTRINE: Pipeline Delegation
# =============================================================================


class TestPipelineDelegation:
    """Doctrine about pipeline delegation to use cases."""

    def test_pipeline_MUST_delegate_to_use_case(self, tmp_path: Path):
        """A pipeline MUST delegate to a UseCase's execute() method.

        The pipeline should NOT contain business logic directly.
        It wraps a use case with Temporal workflow treatment.
        """
        content = '''
        from temporalio import workflow

        @workflow.defn
        class ExtractAssemblePipeline:
            """Pipeline that properly delegates to use case."""

            @workflow.run
            async def run(self, doc_id: str) -> dict:
                use_case = ExtractAssembleDataUseCase(
                    document_repo=WorkflowDocumentRepositoryProxy(),
                )
                return await use_case.execute(doc_id)
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        pipeline = pipelines[0]
        assert pipeline.delegates_to_use_case is True
        assert pipeline.wrapped_use_case == "ExtractAssembleDataUseCase"

    def test_pipeline_MUST_NOT_contain_business_logic(self, tmp_path: Path):
        """A pipeline MUST NOT contain business logic directly.

        If the run() method contains logic beyond use case instantiation
        and delegation, it violates the pipeline pattern.
        """
        # This pipeline contains business logic directly - BAD
        content = '''
        from temporalio import workflow

        @workflow.defn
        class BadPipeline:
            """Pipeline with business logic inside - VIOLATION."""

            @workflow.run
            async def run(self, config: dict) -> dict:
                # This is business logic that should be in a UseCase
                polling_service = WorkflowPollerServiceProxy()
                polling_result = await polling_service.poll_endpoint(config)
                current_hash = hashlib.sha256(polling_result.content).hexdigest()
                # ... more business logic ...
                return {"hash": current_hash}
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        pipeline = pipelines[0]
        # This should be detected as NOT delegating
        assert pipeline.delegates_to_use_case is False


# =============================================================================
# DOCTRINE: Pipeline Structure
# =============================================================================


class TestPipelineStructure:
    """Doctrine about pipeline structure."""

    def test_pipeline_MUST_have_run_method(self, tmp_path: Path):
        """A pipeline MUST have a run() method as the workflow entry point."""
        content = '''
        from temporalio import workflow

        @workflow.defn
        class ValidPipeline:
            """Pipeline with run method."""

            @workflow.run
            async def run(self) -> None:
                pass
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].has_run_method is True

    def test_pipeline_MUST_have_docstring(self, tmp_path: Path):
        """A pipeline class MUST have a docstring describing its purpose."""
        content = '''
        from temporalio import workflow

        @workflow.defn
        class DocumentedPipeline:
            """Pipeline that processes documents via Temporal.

            Wraps DocumentProcessingUseCase with durable execution guarantees.
            """

            @workflow.run
            async def run(self) -> None:
                pass
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].docstring != ""


# =============================================================================
# DOCTRINE: Pipeline run_next() Pattern
# =============================================================================


class TestPipelineRunNextPattern:
    """Doctrine about pipeline routing via run_next().

    A Pipeline MUST call run_next() to route responses to downstream pipelines.
    This pattern separates business logic (in UseCase) from routing logic.
    """

    def test_pipeline_MUST_have_run_next_method(self, tmp_path: Path):
        """A compliant pipeline MUST have a run_next() method."""
        content = '''
        from temporalio import workflow

        @workflow.defn
        class CompliantPipeline:
            """Pipeline with run_next method."""

            @workflow.run
            async def run(self, request: dict) -> dict:
                response = await SomeUseCase().execute(request)
                await self.run_next(response)
                return response

            async def run_next(self, response) -> list:
                return []
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].has_run_next_method is True

    def test_pipeline_run_next_MUST_NOT_have_workflow_run_decorator(
        self, tmp_path: Path
    ):
        """run_next() MUST NOT have @workflow.run decorator.

        Only run() is the entry point. run_next() is a helper method.
        """
        content = '''
        from temporalio import workflow

        @workflow.defn
        class ValidPipeline:
            """Pipeline with undecorated run_next."""

            @workflow.run
            async def run(self, request: dict) -> dict:
                response = await SomeUseCase().execute(request)
                await self.run_next(response)
                return response

            async def run_next(self, response) -> list:
                # No @workflow.run here - correct!
                return []
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].run_next_has_workflow_decorator is False

    def test_pipeline_run_MUST_call_run_next(self, tmp_path: Path):
        """Pipeline's run() method MUST call self.run_next()."""
        content = '''
        from temporalio import workflow

        @workflow.defn
        class CompliantPipeline:
            """Pipeline that calls run_next."""

            @workflow.run
            async def run(self, request: dict) -> dict:
                response = await SomeUseCase().execute(request)
                dispatches = await self.run_next(response)
                response.dispatches = dispatches
                return response

            async def run_next(self, response) -> list:
                return []
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        assert pipelines[0].run_calls_run_next is True

    def test_pipeline_response_MUST_include_dispatches(self, tmp_path: Path):
        """Pipeline response MUST include dispatches list from run_next()."""
        # This is a structural test - the response type should have dispatches
        content = '''
        from temporalio import workflow
        from julee.core.entities.pipeline_dispatch import PipelineDispatchItem

        @workflow.defn
        class CompliantPipeline:
            """Pipeline that includes dispatches in response."""

            @workflow.run
            async def run(self, request: dict) -> dict:
                response = await SomeUseCase().execute(request)
                dispatches = await self.run_next(response)
                response.dispatches = dispatches
                return response.model_dump()

            async def run_next(self, response) -> list[PipelineDispatchItem]:
                # Route via RouteResponseUseCase
                return []
        '''
        file_path = create_pipeline_file(tmp_path, content)
        pipelines = parse_pipelines_from_file(file_path)

        assert len(pipelines) == 1
        # The pipeline should set dispatches on response
        assert pipelines[0].sets_dispatches_on_response is True


# =============================================================================
# NOTE: Real Codebase Compliance Tests Moved to Policy
# =============================================================================
# The tests that verify pipelines in the actual codebase are now in the
# temporal-pipelines policy: julee.core.policies.temporal_pipelines
#
# This file contains only the unit tests that define what a Pipeline IS
# (axioms), not the compliance checks that verify existing pipelines.

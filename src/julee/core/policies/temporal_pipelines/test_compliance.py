"""Compliance tests for Temporal Pipelines policy.

These tests verify that Temporal workflows follow julee's pipeline patterns.
"""

import pytest

from julee.core.use_cases.code_artifact.list_pipelines import ListPipelinesUseCase
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest


class TestTemporalPipelinesCompliance:
    """Compliance tests for temporal-pipelines policy."""

    @pytest.mark.asyncio
    async def test_all_pipelines_MUST_have_workflow_decorator(self, repo):
        """All pipeline classes MUST be decorated with @workflow.defn."""
        use_case = ListPipelinesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Skip if no pipelines found
        if not response.pipelines:
            pytest.skip("No pipelines found in codebase")

        violations = []
        for pipeline in response.pipelines:
            if not pipeline.has_workflow_decorator:
                violations.append(
                    f"{pipeline.bounded_context}.{pipeline.name}: "
                    f"missing @workflow.defn decorator"
                )

        assert (
            not violations
        ), "Pipelines missing @workflow.defn decorator:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_pipelines_MUST_have_run_method(self, repo):
        """All pipeline classes MUST have a run() method."""
        use_case = ListPipelinesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        if not response.pipelines:
            pytest.skip("No pipelines found in codebase")

        violations = []
        for pipeline in response.pipelines:
            if not pipeline.has_run_method:
                violations.append(
                    f"{pipeline.bounded_context}.{pipeline.name}: "
                    f"missing run() method"
                )

        assert not violations, "Pipelines missing run() method:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_pipelines_MUST_have_run_decorator(self, repo):
        """All pipeline run() methods MUST be decorated with @workflow.run."""
        use_case = ListPipelinesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        if not response.pipelines:
            pytest.skip("No pipelines found in codebase")

        violations = []
        for pipeline in response.pipelines:
            if pipeline.has_run_method and not pipeline.has_run_decorator:
                violations.append(
                    f"{pipeline.bounded_context}.{pipeline.name}: "
                    f"run() method missing @workflow.run decorator"
                )

        assert (
            not violations
        ), "Pipeline run() methods missing @workflow.run decorator:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_pipelines_MUST_delegate_to_use_case(self, repo):
        """All pipelines MUST delegate to a UseCase's execute() method.

        A pipeline that contains business logic directly (instead of
        delegating to a UseCase) violates the pipeline pattern. The
        pipeline should only handle Temporal concerns, not business logic.
        """
        use_case = ListPipelinesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        if not response.pipelines:
            pytest.skip("No pipelines found in codebase")

        violations = []
        for pipeline in response.pipelines:
            if not pipeline.delegates_to_use_case:
                expected_uc = pipeline.expected_use_case_name or "{Prefix}UseCase"
                violations.append(
                    f"{pipeline.bounded_context}.{pipeline.name}: "
                    f"does NOT delegate to UseCase (expected: {expected_uc})"
                )

        assert not violations, (
            "Pipelines not delegating to UseCase (contain business logic):\n"
            + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_all_pipelines_MUST_be_compliant(self, repo):
        """All pipelines MUST satisfy all pipeline doctrine requirements.

        This is a comprehensive check that ensures:
        1. @workflow.defn decorator
        2. run() method with @workflow.run decorator
        3. Delegates to a UseCase (doesn't contain business logic)
        """
        use_case = ListPipelinesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        if not response.pipelines:
            pytest.skip("No pipelines found in codebase")

        non_compliant = []
        for pipeline in response.pipelines:
            if not pipeline.is_compliant:
                issues = []
                if not pipeline.has_workflow_decorator:
                    issues.append("missing @workflow.defn")
                if not pipeline.has_run_method:
                    issues.append("missing run() method")
                if not pipeline.has_run_decorator:
                    issues.append("missing @workflow.run")
                if not pipeline.delegates_to_use_case:
                    issues.append(
                        "contains business logic (should delegate to UseCase)"
                    )

                non_compliant.append(
                    f"{pipeline.bounded_context}.{pipeline.name}: {', '.join(issues)}"
                )

        assert not non_compliant, "Non-compliant pipelines found:\n" + "\n".join(
            non_compliant
        )

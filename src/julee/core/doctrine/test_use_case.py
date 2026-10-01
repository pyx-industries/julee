"""UseCase doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.resolution import (
    dto_verdicts,
    module_name_for,
    package_of,
)
from julee.core.doctrine.rules.dependency import (
    usecases_importing_outward,
)
from julee.core.doctrine.rules.use_case import (
    requests_that_are_not_pydantic,
    responses_that_are_not_pydantic,
    use_case_sources_mentioning,
    use_cases_defining_next_action,
    use_cases_not_named_UseCase,
    use_cases_whose_execute_returns_the_wrong_response,
    use_cases_whose_execute_takes_the_wrong_request,
    use_cases_without_docstring,
    use_cases_without_execute,
    use_cases_without_request,
    use_cases_without_response,
)
from julee.core.doctrine_constants import (
    USE_CASE_SUFFIX,
)
from julee.core.parsers.imports import ImportInfo, extract_imports
from julee.core.usecases.code_artifact.list_requests import ListRequestsUseCase
from julee.core.usecases.code_artifact.list_responses import ListResponsesUseCase
from julee.core.usecases.code_artifact.list_use_cases import ListUseCasesUseCase
from julee.core.usecases.code_artifact.uc_interfaces import ListCodeArtifactsRequest

# Generic/abstract base classes that don't require matching Request/Response
GENERIC_BASE_CLASSES = {
    "FilterableListUseCase",  # Generic base for list use cases with filtering
}


class TestUseCaseNaming:
    """Doctrine about use case naming conventions."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_end_with_UseCase(self, repo):
        """All use case class names MUST end with 'UseCase'.

        A class in usecases/ is a use case (ADR 020): doctrine finds it
        by where it sits, and this is where its name is checked. Only a
        request or a response, by its own suffix, is something else.

        So a helper, a shared base or a port written in usecases/ is
        objected to here. It is a use case that is not named like one,
        or it is not a use case and is in the wrong directory, and the
        answer to either is not to leave it where it is.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # A target with no bounded contexts has nothing to check: julee
        # itself is one, now that its domain code ships as kits. A target
        # that has contexts but no use cases in them is a broken detector,
        # so the canary still holds there.
        if not await repo.list_all():
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        assert len(response.artifacts) > 0, (
            "No use cases found - detector may be broken"
        )

        violations = use_cases_not_named_UseCase(response.artifacts)

        assert not violations, (
            f"Classes in usecases/ not ending with '{USE_CASE_SUFFIX}'. "
            f"Each is a use case to rename, or something else to move "
            f"out:\n" + "\n".join(violations)
        )


class TestUseCaseDocumentation:
    """Doctrine about use case documentation."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_docstring(self, repo):
        """All use case classes MUST have a docstring."""
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = use_cases_without_docstring(response.artifacts)

        assert not violations, "Use cases missing docstrings:\n" + "\n".join(violations)


class TestUseCaseStructure:
    """Doctrine about use case structure."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_execute_method(self, repo):
        """All use cases MUST have an execute() method.

        The execute() method is the single entry point for use case invocation.
        It accepts a Request and returns a Response.

        Uses runtime inspection (hasattr) to support inherited methods from
        generic base classes like generic_crud.GetUseCase.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = use_cases_without_execute(response.artifacts)

        assert not violations, "Use cases missing execute() method:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_matching_request(self, repo):
        """All use cases MUST have a matching {Prefix}Request class."""
        uc_response = await ListUseCasesUseCase(repo).execute(
            ListCodeArtifactsRequest()
        )
        req_response = await ListRequestsUseCase(repo).execute(
            ListCodeArtifactsRequest()
        )

        violations = use_cases_without_request(
            uc_response.artifacts, req_response.artifacts
        )

        assert not violations, "Use cases missing matching requests:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_matching_response(self, repo):
        """All use cases MUST have a matching {Prefix}Response class.

        Use cases that return data MUST have a corresponding Response class
        in the same bounded context.
        """
        uc_response = await ListUseCasesUseCase(repo).execute(
            ListCodeArtifactsRequest()
        )
        resp_response = await ListResponsesUseCase(repo).execute(
            ListCodeArtifactsRequest()
        )

        violations = use_cases_without_response(
            uc_response.artifacts, resp_response.artifacts
        )

        assert not violations, "Use cases missing matching responses:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_execute_MUST_accept_matching_request(self, repo):
        """execute() MUST declare its first parameter as {Prefix}Request.

        Ensures the request class is part of the method's contract, not
        just present in the module.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = use_cases_whose_execute_takes_the_wrong_request(response.artifacts)

        assert not violations, "Use cases with wrong request type:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_use_cases_MUST_NOT_define_next_action(self, repo):
        """Use case classes MUST NOT define a next_action() method.

        next_action() is the superseded orchestration pattern (pre-ADR 003).
        Use cases should hand off domain conditions to injected handler
        services instead of computing what happens next themselves.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = use_cases_defining_next_action(response.artifacts)

        assert not violations, (
            "Use cases defining forbidden next_action() method:\n"
            + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_execute_MUST_return_matching_response(self, repo):
        """execute() MUST declare its return type as {Prefix}Response.

        Ensures the response class is actually wired into execute(), not
        just present in the module.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = use_cases_whose_execute_returns_the_wrong_response(
            response.artifacts
        )

        assert not violations, "Use cases with wrong return type:\n" + "\n".join(
            violations
        )


class TestExecutionAgnosticism:
    """Doctrine about execution-agnosticism in use cases (ADR 004).

    Use cases must not couple to specific execution frameworks like Temporal.
    Time and execution identity must be injected via service protocols
    instead of being accessed directly.
    """

    @pytest.mark.asyncio
    async def test_use_case_files_MUST_NOT_call_datetime_now(self, repo):
        """Use case files MUST NOT call datetime.now(), datetime.utcnow(), or datetime.today().

        Use cases needing the current time MUST inject ClockWitness and
        call its now() instead. Direct datetime calls couple the use case
        to system time, making deterministic testing impossible and
        breaking Temporal's replay guarantee.

        A witness rather than a calculator (ADR 016): the time does not
        follow from any argument, and the runtime is what makes the
        answer replay-stable. Calling datetime.now() here is precisely
        the case where nothing records the answer.
        """
        sources = [
            (ctx.slug, str(py_file.relative_to(Path(ctx.path))), py_file.read_text())
            for ctx in await repo.list_all()
            for py_file in (Path(ctx.path) / "usecases").rglob("*.py")
            if "tests" not in py_file.parts
        ]

        violations = use_case_sources_mentioning(sources, "datetime.now")

        assert not violations, "Use case files calling datetime.now():\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_use_case_files_MUST_NOT_import_temporalio(self, repo):
        """Use case files MUST NOT import from temporalio.

        Temporal coupling belongs in the infrastructure layer (worker/pipelines),
        not use cases. Use cases must remain framework-agnostic so they can run
        in any execution context.
        """
        sources = [
            (ctx.slug, str(py_file.relative_to(Path(ctx.path))), py_file.read_text())
            for ctx in await repo.list_all()
            for py_file in (Path(ctx.path) / "usecases").rglob("*.py")
            if "tests" not in py_file.parts
        ]

        violations = use_case_sources_mentioning(sources, "temporalio")

        assert not violations, "Use case files importing temporalio:\n" + "\n".join(
            violations
        )


class TestDrivingPortMessages:
    """Doctrine about the messages a use case takes and returns.

    A request and a response are messages at the driving port, not
    domain objects. They cross a process boundary, so they are
    validated on the way in and serialised on the way out.

    Both tests resolve the class and ask Python rather than reading
    its bases, which cannot tell a local class called BaseModel from
    pydantic's.
    """

    @staticmethod
    async def _verdicts(repo, artifacts):
        """Resolve every artifact name, context by context."""
        by_context: dict[str, list[str]] = {}
        for found in artifacts:
            by_context.setdefault(found.bounded_context, []).append(found.artifact.name)

        verdicts = []
        for ctx in await repo.list_all():
            verdicts.extend(
                dto_verdicts(ctx.slug, Path(ctx.path), by_context.get(ctx.slug, []))
            )
        return verdicts

    @pytest.mark.asyncio
    async def test_every_request_MUST_be_a_pydantic_DTO(self, repo):
        """Use case requests MUST be pydantic models.

        A request arrives from outside as JSON, form fields or a queue
        payload. Pydantic is what validates it.
        """
        response = await ListRequestsUseCase(repo).execute(ListCodeArtifactsRequest())

        if not await repo.list_all():
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        assert len(response.artifacts) > 0, "No requests found - detector may be broken"

        verdicts = await self._verdicts(repo, response.artifacts)
        violations = requests_that_are_not_pydantic(verdicts)

        assert not violations, "Requests that are not pydantic DTOs:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_every_response_MUST_be_a_pydantic_DTO(self, repo):
        """Use case responses MUST be pydantic models.

        A response is what a driving adapter turns back into JSON, a
        template context or a CLI table.
        """
        response = await ListResponsesUseCase(repo).execute(ListCodeArtifactsRequest())

        if not await repo.list_all():
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        assert len(response.artifacts) > 0, (
            "No responses found - detector may be broken"
        )

        verdicts = await self._verdicts(repo, response.artifacts)
        violations = responses_that_are_not_pydantic(verdicts)

        assert not violations, "Responses that are not pydantic DTOs:\n" + "\n".join(
            violations
        )


class TestTheDependencyRule:
    """Doctrine about what a use case may reach for."""

    @pytest.mark.asyncio
    async def test_a_usecase_MUST_import_only_inward(self, repo, kits):
        """A use case MUST import only what points inward.

        Its own context's domain/ and usecases/, an adopted kit's same
        two, julee's entities, ports and use case bases, and the few
        standard library modules that are the language rather than the
        outside world.

        Imports anywhere in a file count, a deferred one inside a
        function included.
        """
        contexts = await repo.list_all()
        if not contexts:
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        kit_packages = [kit.package for kit in kits if getattr(kit, "package", None)]

        found: list[tuple[str, str, ImportInfo]] = []
        packages: dict[str, str] = {}
        for ctx in contexts:
            context_path = Path(ctx.path)
            packages[ctx.slug] = (
                module_name_for(context_path / "__init__.py") or ctx.slug
            )
            for py_file in sorted((context_path / "usecases").rglob("*.py")):
                if "tests" in py_file.parts:
                    continue
                package = package_of(py_file)
                found.extend(
                    (ctx.slug, package, info) for info in extract_imports(py_file)
                )

        if not found:
            pytest.skip("No use case imports in target codebase — nothing to check")

        violations = usecases_importing_outward(found, packages, kit_packages)

        assert not violations, "Use cases importing outward:\n" + "\n".join(violations)


class TestUseCasesDoNotCallUseCases:
    """Doctrine about coupling inside the use case ring."""

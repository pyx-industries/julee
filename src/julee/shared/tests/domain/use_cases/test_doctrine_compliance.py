"""Doctrine compliance tests.

These tests validate that the ACTUAL codebase complies with architectural doctrine.
Unlike doctrine definition tests (which use synthetic fixtures), these scan real code.

Run these to ensure the repository follows established doctrine rules.
"""

from pathlib import Path

import pytest

from julee.shared.domain.doctrine_constants import (
    ENTITY_FORBIDDEN_SUFFIXES,
    ITEM_SUFFIX,
    PROTOCOL_BASES,
    REPOSITORY_SUFFIX,
    REQUEST_BASE,
    REQUEST_SUFFIX,
    RESPONSE_BASE,
    RESPONSE_SUFFIX,
    SERVICE_SUFFIX,
    USE_CASE_SUFFIX,
)
from julee.shared.domain.use_cases import (
    ListCodeArtifactsRequest,
    ListEntitiesUseCase,
    ListRepositoryProtocolsUseCase,
    ListRequestsUseCase,
    ListResponsesUseCase,
    ListServiceProtocolsUseCase,
    ListUseCasesUseCase,
)
from julee.shared.repositories.introspection import FilesystemBoundedContextRepository

# Project root - find by looking for pyproject.toml
PROJECT_ROOT = Path(__file__).parent
while PROJECT_ROOT.parent != PROJECT_ROOT:
    if (PROJECT_ROOT / "pyproject.toml").exists():
        break
    PROJECT_ROOT = PROJECT_ROOT.parent


@pytest.fixture
def repo() -> FilesystemBoundedContextRepository:
    """Repository pointing at real codebase."""
    return FilesystemBoundedContextRepository(PROJECT_ROOT)


# =============================================================================
# ENTITY COMPLIANCE
# =============================================================================


class TestEntityCompliance:
    """Validate all entities in the repository comply with doctrine."""

    @pytest.mark.asyncio
    async def test_all_entities_MUST_be_PascalCase(self, repo):
        """All entity class names MUST be PascalCase."""
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning entities
        assert len(response.artifacts) > 0, "No entities found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            if not name[0].isupper():
                violations.append(
                    f"{artifact.bounded_context}.{name}: MUST start with uppercase"
                )
            if "_" in name:
                violations.append(
                    f"{artifact.bounded_context}.{name}: MUST NOT contain underscores"
                )

        assert not violations, "Entity naming violations:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_entities_MUST_NOT_have_reserved_suffixes(self, repo):
        """All entity class names MUST NOT end with UseCase, Request, or Response."""
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            for forbidden_suffix in ENTITY_FORBIDDEN_SUFFIXES:
                if name.endswith(forbidden_suffix):
                    violations.append(
                        f"{artifact.bounded_context}.{name}: "
                        f"MUST NOT end with '{forbidden_suffix}'"
                    )

        assert not violations, "Entity suffix violations:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_entities_MUST_have_docstring(self, repo):
        """All entity classes MUST have a docstring."""
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Entities missing docstrings:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_entity_fields_MUST_have_type_annotations(self, repo):
        """All entity fields MUST have type annotations."""
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            for field in artifact.artifact.fields:
                if not field.type_annotation:
                    violations.append(
                        f"{artifact.bounded_context}.{artifact.artifact.name}.{field.name}"
                    )

        assert not violations, "Entity fields missing type annotations:\n" + "\n".join(
            violations
        )


# =============================================================================
# USE CASE COMPLIANCE
# =============================================================================


class TestUseCaseCompliance:
    """Validate all use cases in the repository comply with doctrine."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_end_with_UseCase(self, repo):
        """All use case class names MUST end with 'UseCase'."""
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning use cases
        assert (
            len(response.artifacts) > 0
        ), "No use cases found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.name.endswith(USE_CASE_SUFFIX):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert (
            not violations
        ), f"Use cases not ending with '{USE_CASE_SUFFIX}':\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_docstring(self, repo):
        """All use case classes MUST have a docstring."""
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Use cases missing docstrings:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_matching_request(self, repo):
        """All use cases MUST have a matching {Prefix}Request class."""
        uc_use_case = ListUseCasesUseCase(repo)
        uc_response = await uc_use_case.execute(ListCodeArtifactsRequest())

        req_use_case = ListRequestsUseCase(repo)
        req_response = await req_use_case.execute(ListCodeArtifactsRequest())

        # Build set of available requests per context
        requests_by_context: dict[str, set[str]] = {}
        for artifact in req_response.artifacts:
            ctx = artifact.bounded_context
            if ctx not in requests_by_context:
                requests_by_context[ctx] = set()
            requests_by_context[ctx].add(artifact.artifact.name)

        violations = []
        suffix_len = len(USE_CASE_SUFFIX)
        for artifact in uc_response.artifacts:
            name = artifact.artifact.name
            ctx = artifact.bounded_context
            if name.endswith(USE_CASE_SUFFIX):
                prefix = name[:-suffix_len]
                expected_request = f"{prefix}{REQUEST_SUFFIX}"
                available = requests_by_context.get(ctx, set())
                if expected_request not in available:
                    violations.append(f"{ctx}.{name}: missing {expected_request}")

        assert not violations, "Use cases missing matching requests:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_have_execute_method(self, repo):
        """All use cases MUST have an execute() method.

        The execute() method is the single entry point for use case invocation.
        It accepts a Request and returns a Response.
        """
        use_case = ListUseCasesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            method_names = [m.name for m in artifact.artifact.methods]
            if "execute" not in method_names:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}: missing execute() method"
                )

        assert not violations, "Use cases missing execute() method:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_use_cases_SHOULD_have_matching_response(self, repo):
        """All use cases SHOULD have a matching {Prefix}Response class.

        Use cases that return data should have a corresponding Response class
        in the same bounded context.
        """
        uc_use_case = ListUseCasesUseCase(repo)
        uc_response = await uc_use_case.execute(ListCodeArtifactsRequest())

        resp_use_case = ListResponsesUseCase(repo)
        resp_response = await resp_use_case.execute(ListCodeArtifactsRequest())

        # Build set of available responses per context
        responses_by_context: dict[str, set[str]] = {}
        for artifact in resp_response.artifacts:
            ctx = artifact.bounded_context
            if ctx not in responses_by_context:
                responses_by_context[ctx] = set()
            responses_by_context[ctx].add(artifact.artifact.name)

        missing = []
        suffix_len = len(USE_CASE_SUFFIX)
        for artifact in uc_response.artifacts:
            name = artifact.artifact.name
            ctx = artifact.bounded_context
            if name.endswith(USE_CASE_SUFFIX):
                prefix = name[:-suffix_len]
                expected_response = f"{prefix}{RESPONSE_SUFFIX}"
                available = responses_by_context.get(ctx, set())
                if expected_response not in available:
                    missing.append(f"{ctx}.{name}: missing {expected_response}")

        # This is a SHOULD rule - log but don't fail
        # Uncomment the assertion below to enforce strictly
        # assert not missing, "Use cases missing matching responses:\n" + "\n".join(missing)
        if missing:
            import warnings

            warnings.warn(
                "Use cases missing matching Response classes (SHOULD have):\n"
                + "\n".join(missing),
                stacklevel=2,
            )


# =============================================================================
# REQUEST COMPLIANCE
#
# Naming conventions for classes in requests.py:
#   - *Request: Top-level use case input (e.g., CreateJourneyRequest)
#   - *Item: Nested compound type for complex attributes (e.g., JourneyStepItem)
#
# Item types are used for list attributes within requests that need their own
# validation and to_domain_model() conversion. They are NOT top-level requests.
# =============================================================================


class TestRequestCompliance:
    """Validate all requests in the repository comply with doctrine."""

    @pytest.mark.asyncio
    async def test_all_requests_MUST_end_with_Request_or_Item(self, repo):
        """All request class names MUST end with 'Request' or 'Item'.

        - *Request: Top-level use case input
        - *Item: Nested compound type for complex list attributes
        """
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning requests
        assert len(response.artifacts) > 0, "No requests found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            if not (name.endswith(REQUEST_SUFFIX) or name.endswith(ITEM_SUFFIX)):
                violations.append(f"{artifact.bounded_context}.{name}")

        assert not violations, (
            f"Classes in requests.py must end with '{REQUEST_SUFFIX}' or '{ITEM_SUFFIX}':\n"
            + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_all_requests_MUST_have_docstring(self, repo):
        """All request classes MUST have a docstring."""
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Requests missing docstrings:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_requests_MUST_inherit_from_BaseModel(self, repo):
        """All request classes MUST inherit from BaseModel."""
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if REQUEST_BASE not in artifact.artifact.bases:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), f"Requests not inheriting from {REQUEST_BASE}:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_request_fields_MUST_have_type_annotations(self, repo):
        """All request fields MUST have type annotations."""
        use_case = ListRequestsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            for field in artifact.artifact.fields:
                if not field.type_annotation:
                    violations.append(
                        f"{artifact.bounded_context}.{artifact.artifact.name}.{field.name}"
                    )

        assert not violations, "Request fields missing type annotations:\n" + "\n".join(
            violations
        )


# =============================================================================
# RESPONSE COMPLIANCE
# =============================================================================


class TestResponseCompliance:
    """Validate all responses in the repository comply with doctrine."""

    @pytest.mark.asyncio
    async def test_all_responses_MUST_end_with_Response_or_Item(self, repo):
        """All response class names MUST end with 'Response' or 'Item'."""
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning responses
        assert (
            len(response.artifacts) > 0
        ), "No responses found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            if not (name.endswith(RESPONSE_SUFFIX) or name.endswith(ITEM_SUFFIX)):
                violations.append(f"{artifact.bounded_context}.{name}")

        assert not violations, (
            f"Classes in responses.py must end with '{RESPONSE_SUFFIX}' or '{ITEM_SUFFIX}':\n"
            + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_all_responses_MUST_have_docstring(self, repo):
        """All response classes MUST have a docstring."""
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Responses missing docstrings:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_responses_MUST_inherit_from_BaseModel(self, repo):
        """All response classes MUST inherit from BaseModel."""
        use_case = ListResponsesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if RESPONSE_BASE not in artifact.artifact.bases:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), f"Responses not inheriting from {RESPONSE_BASE}:\n" + "\n".join(violations)


# =============================================================================
# REPOSITORY PROTOCOL COMPLIANCE
# =============================================================================


class TestRepositoryProtocolCompliance:
    """Validate all repository protocols in the repository comply with doctrine."""

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_end_with_Repository(self, repo):
        """All repository protocol names MUST end with 'Repository'."""
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning repository protocols
        assert (
            len(response.artifacts) > 0
        ), "No repository protocols found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.name.endswith(REPOSITORY_SUFFIX):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, (
            f"Repository protocols not ending with '{REPOSITORY_SUFFIX}':\n"
            + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_have_docstring(self, repo):
        """All repository protocol classes MUST have a docstring."""
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Repository protocols missing docstrings:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_inherit_from_Protocol(self, repo):
        """All repository protocols MUST inherit from Protocol."""
        use_case = ListRepositoryProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            # Explicit check for Protocol or Protocol[T] generic
            has_protocol = any(
                base in PROTOCOL_BASES for base in artifact.artifact.bases
            )
            if not has_protocol:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), "Repository protocols not inheriting from Protocol:\n" + "\n".join(
            violations
        )


# =============================================================================
# SERVICE PROTOCOL COMPLIANCE
# =============================================================================


class TestServiceProtocolCompliance:
    """Validate all service protocols in the repository comply with doctrine."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_end_with_Service(self, repo):
        """All service protocol names MUST end with 'Service'."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning service protocols
        assert (
            len(response.artifacts) > 0
        ), "No service protocols found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.name.endswith(SERVICE_SUFFIX):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert (
            not violations
        ), f"Service protocols not ending with '{SERVICE_SUFFIX}':\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_have_docstring(self, repo):
        """All service protocol classes MUST have a docstring."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Service protocols missing docstrings:\n" + "\n".join(
            violations
        )

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_inherit_from_Protocol(self, repo):
        """All service protocols MUST inherit from Protocol."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            # Explicit check for Protocol or Protocol[T] generic
            has_protocol = any(
                base in PROTOCOL_BASES for base in artifact.artifact.bases
            )
            if not has_protocol:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), "Service protocols not inheriting from Protocol:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_service_protocol_methods_MUST_have_matching_request(self, repo):
        """All service protocol methods MUST have a matching {MethodName}Request class.

        For each public method in a service protocol, there must be a corresponding
        Request class in the same bounded context's requests.py.

        Example: method `evaluate_docstring_quality` -> `EvaluateDocstringQualityRequest`
        """
        from pathlib import Path

        from julee.shared.parsers.ast import parse_python_classes

        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        req_use_case = ListRequestsUseCase(repo)
        req_response = await req_use_case.execute(ListCodeArtifactsRequest())

        # Also check shared bounded context (which is reserved but still has services)
        shared_services_dir = (
            Path(PROJECT_ROOT) / "src" / "julee" / "shared" / "domain" / "services"
        )
        shared_requests_dir = (
            Path(PROJECT_ROOT) / "src" / "julee" / "shared" / "domain" / "use_cases"
        )

        # Create artifact-like structures for shared services
        class ArtifactLike:
            def __init__(self, artifact, bounded_context):
                self.artifact = artifact
                self.bounded_context = bounded_context

        shared_services = (
            parse_python_classes(shared_services_dir)
            if shared_services_dir.exists()
            else []
        )
        shared_requests = (
            parse_python_classes(shared_requests_dir, exclude_files=["responses.py"])
            if shared_requests_dir.exists()
            else []
        )

        # Add shared artifacts to the response
        all_service_artifacts = list(response.artifacts) + [
            ArtifactLike(svc, "shared")
            for svc in shared_services
            if svc.name.endswith("Service")
        ]
        all_request_artifacts = list(req_response.artifacts) + [
            ArtifactLike(req, "shared")
            for req in shared_requests
            if req.name.endswith("Request")
        ]

        # Build set of available requests per context
        requests_by_context: dict[str, set[str]] = {}
        for artifact in all_request_artifacts:
            ctx = artifact.bounded_context
            if ctx not in requests_by_context:
                requests_by_context[ctx] = set()
            requests_by_context[ctx].add(artifact.artifact.name)

        def snake_to_pascal(name: str) -> str:
            """Convert snake_case to PascalCase."""
            return "".join(word.capitalize() for word in name.split("_"))

        violations = []
        for artifact in all_service_artifacts:
            service_name = artifact.artifact.name
            ctx = artifact.bounded_context
            available = requests_by_context.get(ctx, set())

            for method in artifact.artifact.methods:
                expected_request = f"{snake_to_pascal(method.name)}Request"
                if expected_request not in available:
                    violations.append(
                        f"{ctx}.{service_name}.{method.name}(): missing {expected_request}"
                    )

        assert (
            not violations
        ), "Service protocol methods missing matching Request classes:\n" + "\n".join(
            violations
        )


# =============================================================================
# DEPENDENCY RULE COMPLIANCE
# =============================================================================


class TestDependencyRuleCompliance:
    """Validate all code in the repository complies with the dependency rule.

    The dependency rule is Clean Architecture's central invariant:
    Dependencies must point inward. Outer layers depend on inner layers,
    never the reverse.

    Layer hierarchy (outer to inner):
        infrastructure/ -> use_cases/ -> models/
    """

    @pytest.mark.asyncio
    async def test_all_entities_MUST_NOT_import_outward(self, repo):
        """All entity files MUST NOT import from outer layers.

        Entities (domain/models/) are innermost and cannot depend on:
        - use_cases/
        - repositories/
        - services/
        - infrastructure/
        - apps/
        - deployment/
        """
        from pathlib import Path

        from julee.shared.parsers.imports import classify_import_layer, extract_imports

        # Get all bounded contexts
        contexts = await repo.list_all()

        violations = []
        forbidden_layers = {
            "use_cases",
            "repositories",
            "services",
            "infrastructure",
            "apps",
            "deployment",
        }

        for ctx in contexts:
            models_dir = Path(ctx.path) / "domain" / "models"
            if not models_dir.exists():
                continue

            for py_file in models_dir.glob("**/*.py"):
                if py_file.name.startswith("_"):
                    continue

                imports = extract_imports(py_file)
                for imp in imports:
                    layer = classify_import_layer(imp.module)
                    if layer in forbidden_layers:
                        violations.append(
                            f"{ctx.slug}/domain/models/{py_file.name}: "
                            f"imports from {layer} ({imp.module})"
                        )

        assert (
            not violations
        ), "Entity files importing from outer layers:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_NOT_import_from_infrastructure(self, repo):
        """All use case files MUST NOT import from infrastructure/.

        Use cases orchestrate business logic through protocols (abstractions),
        never concrete infrastructure implementations.
        """
        from pathlib import Path

        from julee.shared.parsers.imports import classify_import_layer, extract_imports

        contexts = await repo.list_all()

        violations = []
        forbidden_layers = {"infrastructure", "apps", "deployment"}

        for ctx in contexts:
            use_cases_dir = Path(ctx.path) / "domain" / "use_cases"
            if not use_cases_dir.exists():
                continue

            for py_file in use_cases_dir.glob("**/*.py"):
                if py_file.name.startswith("_"):
                    continue

                imports = extract_imports(py_file)
                for imp in imports:
                    layer = classify_import_layer(imp.module)
                    if layer in forbidden_layers:
                        violations.append(
                            f"{ctx.slug}/domain/use_cases/{py_file.name}: "
                            f"imports from {layer} ({imp.module})"
                        )

        assert (
            not violations
        ), "Use case files importing from outer layers:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_NOT_import_from_infrastructure(
        self, repo
    ):
        """All repository protocol files MUST NOT import from infrastructure/.

        Repository protocols define abstractions; they cannot reference
        concrete implementations.
        """
        from pathlib import Path

        from julee.shared.parsers.imports import classify_import_layer, extract_imports

        contexts = await repo.list_all()

        violations = []
        forbidden_layers = {"infrastructure", "apps", "deployment"}

        for ctx in contexts:
            repos_dir = Path(ctx.path) / "domain" / "repositories"
            if not repos_dir.exists():
                continue

            for py_file in repos_dir.glob("**/*.py"):
                if py_file.name.startswith("_"):
                    continue

                imports = extract_imports(py_file)
                for imp in imports:
                    layer = classify_import_layer(imp.module)
                    if layer in forbidden_layers:
                        violations.append(
                            f"{ctx.slug}/domain/repositories/{py_file.name}: "
                            f"imports from {layer} ({imp.module})"
                        )

        assert (
            not violations
        ), "Repository protocols importing from outer layers:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_NOT_import_from_infrastructure(
        self, repo
    ):
        """All service protocol files MUST NOT import from infrastructure/.

        Service protocols define abstractions; they cannot reference
        concrete implementations.
        """
        from pathlib import Path

        from julee.shared.parsers.imports import classify_import_layer, extract_imports

        contexts = await repo.list_all()

        violations = []
        forbidden_layers = {"infrastructure", "apps", "deployment"}

        for ctx in contexts:
            services_dir = Path(ctx.path) / "domain" / "services"
            if not services_dir.exists():
                continue

            for py_file in services_dir.glob("**/*.py"):
                if py_file.name.startswith("_"):
                    continue

                imports = extract_imports(py_file)
                for imp in imports:
                    layer = classify_import_layer(imp.module)
                    if layer in forbidden_layers:
                        violations.append(
                            f"{ctx.slug}/domain/services/{py_file.name}: "
                            f"imports from {layer} ({imp.module})"
                        )

        assert (
            not violations
        ), "Service protocols importing from outer layers:\n" + "\n".join(violations)


# =============================================================================
# PIPELINE COMPLIANCE
# =============================================================================


class TestPipelineCompliance:
    """Validate all pipelines in the repository comply with doctrine.

    A pipeline is a UseCase that has been appropriately treated (with
    decorators and proxies) to run as a Temporal workflow. Pipelines
    MUST delegate to use cases - they MUST NOT contain business logic.
    """

    @pytest.mark.asyncio
    async def test_all_pipelines_MUST_have_workflow_decorator(self, repo):
        """All pipeline classes MUST be decorated with @workflow.defn."""
        from julee.shared.domain.use_cases import (
            ListCodeArtifactsRequest,
            ListPipelinesUseCase,
        )

        use_case = ListPipelinesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Skip test if no pipelines found
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
        from julee.shared.domain.use_cases import (
            ListCodeArtifactsRequest,
            ListPipelinesUseCase,
        )

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
        from julee.shared.domain.use_cases import (
            ListCodeArtifactsRequest,
            ListPipelinesUseCase,
        )

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
        from julee.shared.domain.use_cases import (
            ListCodeArtifactsRequest,
            ListPipelinesUseCase,
        )

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
        from julee.shared.domain.use_cases import (
            ListCodeArtifactsRequest,
            ListPipelinesUseCase,
        )

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

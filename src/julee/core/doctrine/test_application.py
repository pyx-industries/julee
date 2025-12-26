"""Application doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

Applications are deployable/runnable compositions that depend on one or more
bounded contexts. They live in {solution}/apps/ and are classified by type:
REST-API, MCP, SPHINX-EXTENSION, TEMPORAL-WORKER, CLI.

App Type Doctrine (applies to all apps of a given type):
- REST-API: All endpoints MUST map to exactly one use case
- REST-API: Endpoints MUST use Request/Response objects of their use case
- CLI: CLI apps MUST have a commands/ directory
- CLI: CLI apps MUST use Click for command definitions
- MCP: MCP apps MUST have a tools/ directory
- TEMPORAL-WORKER: Worker apps MUST have pipelines

App Instance Doctrine lives in apps/{app}/doctrine/ and is additive.
"""

import ast
from pathlib import Path

import pytest

from julee.core.doctrine_constants import USE_CASE_SUFFIX
from julee.core.entities.application import AppType
from julee.core.infrastructure.repositories.introspection import (
    FilesystemApplicationRepository,
    FilesystemSolutionRepository,
)


def _find_router_files(app_path: Path) -> list[Path]:
    """Find all router files in an application.

    Searches for files in routers/ directories, including BC-organized subdirs.
    """
    router_files = []

    # Direct routers/ directory
    routers_dir = app_path / "routers"
    if routers_dir.exists():
        for f in routers_dir.glob("*.py"):
            if not f.name.startswith("_"):
                router_files.append(f)

    # BC-organized subdirs (e.g., apps/api/ceap/routers/)
    for subdir in app_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith(("_", ".")):
            if subdir.name not in ("shared", "tests", "__pycache__"):
                nested_routers = subdir / "routers"
                if nested_routers.exists():
                    for f in nested_routers.glob("*.py"):
                        if not f.name.startswith("_"):
                            router_files.append(f)

    return router_files


def _extract_endpoints(file_path: Path) -> list[dict]:
    """Extract endpoint information from a router file using AST.

    Detects UseCase usage via two patterns:
    1. DI pattern: `use_case: SomeUseCase = Depends(...)` (type annotation)
    2. Inline instantiation: `SomeUseCase(repo).execute(...)` (function call)

    Returns list of dicts with:
    - name: function name
    - method: HTTP method (get, post, put, delete, patch)
    - line: line number
    - has_usecase: whether endpoint references a UseCase
    - usecase_names: list of UseCase class names found
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    endpoints = []
    route_decorators = {"get", "post", "put", "delete", "patch", "head", "options"}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # Check if decorated with route decorator
            http_method = None
            for decorator in node.decorator_list:
                # Handle @router.get, @router.post, etc.
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr in route_decorators:
                            http_method = decorator.func.attr
                            break
                # Handle @app.get, @app.post, etc.
                elif isinstance(decorator, ast.Attribute):
                    if decorator.attr in route_decorators:
                        http_method = decorator.attr
                        break

            if http_method:
                usecase_names = []

                # Pattern 1: DI via type annotation (use_case: SomeUseCase = Depends)
                for arg in node.args.args:
                    if arg.annotation:
                        # Use ast.unparse to get annotation as string
                        ann_str = ast.unparse(arg.annotation)
                        if USE_CASE_SUFFIX in ann_str:
                            # Extract just the UseCase name from annotation
                            # Handles both "SomeUseCase" and "module.SomeUseCase"
                            for part in ann_str.replace(".", " ").split():
                                if part.endswith(USE_CASE_SUFFIX):
                                    usecase_names.append(part)

                # Pattern 2: Inline instantiation (SomeUseCase(repo))
                for body_node in ast.walk(node):
                    if isinstance(body_node, ast.Call):
                        # Check for UseCase() instantiation
                        if isinstance(body_node.func, ast.Name):
                            if body_node.func.id.endswith(USE_CASE_SUFFIX):
                                if body_node.func.id not in usecase_names:
                                    usecase_names.append(body_node.func.id)
                        # Check for module.UseCase() instantiation
                        elif isinstance(body_node.func, ast.Attribute):
                            if body_node.func.attr.endswith(USE_CASE_SUFFIX):
                                if body_node.func.attr not in usecase_names:
                                    usecase_names.append(body_node.func.attr)

                endpoints.append(
                    {
                        "name": node.name,
                        "method": http_method.upper(),
                        "line": node.lineno,
                        "has_usecase": len(usecase_names) > 0,
                        "usecase_names": usecase_names,
                    }
                )

    return endpoints


class TestRestApiEndpointUseCaseMapping:
    """Doctrine about REST endpoint to use case mapping."""

    @pytest.mark.asyncio
    async def test_rest_api_apps_exist(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """REST-API applications MUST be discoverable."""
        apps = await app_repo.list_by_type(AppType.REST_API)

        assert len(apps) > 0, "No REST-API applications found - detector may be broken"

    @pytest.mark.asyncio
    async def test_rest_api_apps_have_routers(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """REST-API applications MUST have routers."""
        apps = await app_repo.list_by_type(AppType.REST_API)

        for app in apps:
            assert (
                app.markers.has_routers
            ), f"REST-API application '{app.slug}' has no routers"

    @pytest.mark.asyncio
    async def test_all_endpoints_MUST_map_to_exactly_one_usecase(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """All REST endpoints MUST map to exactly one use case.

        Doctrine: REST operations are thin adapters over use cases. Each endpoint
        MUST instantiate exactly one UseCase class and delegate to its execute()
        method. Endpoints MUST NOT contain business logic directly.

        This ensures:
        - Clear separation between HTTP layer and business logic
        - Use cases are reusable across different interfaces (REST, MCP, CLI)
        - Consistent request/response patterns across the API
        """
        apps = await app_repo.list_by_type(AppType.REST_API)

        violations = []

        for app in apps:
            router_files = _find_router_files(Path(app.path))

            for router_file in router_files:
                endpoints = _extract_endpoints(router_file)

                for endpoint in endpoints:
                    if not endpoint["has_usecase"]:
                        violations.append(
                            f"{router_file.relative_to(Path(app.path))}:"
                            f"{endpoint['line']} "
                            f"{endpoint['method']} {endpoint['name']} - "
                            f"no UseCase found"
                        )
                    elif len(endpoint["usecase_names"]) > 1:
                        violations.append(
                            f"{router_file.relative_to(Path(app.path))}:"
                            f"{endpoint['line']} "
                            f"{endpoint['method']} {endpoint['name']} - "
                            f"multiple UseCases: {endpoint['usecase_names']}"
                        )

        assert (
            not violations
        ), "REST endpoints not mapping to exactly one UseCase:\n" + "\n".join(
            f"  - {v}" for v in violations
        )


class TestRestApiEndpointRequestResponse:
    """Doctrine about REST endpoint request/response usage."""

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Doctrine under development - requires request/response pairing analysis"
    )
    async def test_endpoints_MUST_use_usecase_request_response(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """REST endpoints MUST use the Request/Response objects of their use case.

        Doctrine: The HTTP request body SHOULD deserialize directly into the
        UseCase's Request class. The endpoint SHOULD return the UseCase's
        Response (or a field from it).

        This ensures:
        - API contract is defined by the use case, not the router
        - Changes to business logic automatically update the API schema
        - No redundant DTO mapping between HTTP and use case layers
        """
        # Implementation requires analyzing:
        # 1. The type annotation of the request body parameter
        # 2. The UseCase's Request class
        # 3. Whether they match (or one wraps the other)
        pass


# =============================================================================
# CLI APP TYPE DOCTRINE
# =============================================================================


class TestCliAppStructure:
    """Doctrine about CLI application structure."""

    @pytest.mark.asyncio
    async def test_cli_apps_exist(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """CLI applications MUST be discoverable."""
        apps = await app_repo.list_by_type(AppType.CLI)

        assert len(apps) > 0, "No CLI applications found - detector may be broken"

    @pytest.mark.asyncio
    async def test_cli_apps_MUST_have_commands_directory(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """CLI applications MUST have a commands/ directory.

        Doctrine: CLI apps organize their commands in a commands/ subdirectory.
        Each command module defines Click commands that expose use cases.
        """
        apps = await app_repo.list_by_type(AppType.CLI)

        for app in apps:
            assert (
                app.markers.has_commands
            ), f"CLI application '{app.slug}' MUST have commands/ directory"


# =============================================================================
# MCP APP TYPE DOCTRINE
# =============================================================================


class TestMcpAppStructure:
    """Doctrine about MCP application structure."""

    @pytest.mark.asyncio
    async def test_mcp_apps_exist(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST be discoverable."""
        apps = await app_repo.list_by_type(AppType.MCP)

        assert len(apps) > 0, "No MCP applications found - detector may be broken"

    @pytest.mark.asyncio
    async def test_mcp_apps_MUST_have_tools_directory(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """MCP applications MUST have a tools/ directory.

        Doctrine: MCP apps expose their capabilities through tools/ which
        define the MCP tool interface for AI assistants.
        """
        apps = await app_repo.list_by_type(AppType.MCP)

        for app in apps:
            assert (
                app.markers.has_tools
            ), f"MCP application '{app.slug}' MUST have tools/ directory"


# =============================================================================
# TEMPORAL WORKER APP TYPE DOCTRINE
# =============================================================================


class TestTemporalWorkerAppStructure:
    """Doctrine about Temporal Worker application structure."""

    @pytest.mark.asyncio
    async def test_temporal_worker_apps_exist(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """Temporal Worker applications MUST be discoverable."""
        apps = await app_repo.list_by_type(AppType.TEMPORAL_WORKER)

        assert (
            len(apps) > 0
        ), "No Temporal Worker applications found - detector may be broken"

    @pytest.mark.asyncio
    async def test_temporal_worker_apps_with_pipelines_MUST_have_marker(
        self, solution_repo: FilesystemSolutionRepository
    ) -> None:
        """Temporal Worker applications with local pipelines MUST have the marker.

        Doctrine: Worker apps that define their own pipelines (not composite
        workers) MUST have has_pipelines=True. This verifies the marker
        detection is working correctly for apps with pipelines/ or pipelines.py.

        Composite workers (that import pipelines from other TEMPORAL-WORKER apps)
        MAY have has_pipelines=False - they are detected via temporalio imports.
        """
        solution = await solution_repo.get()
        worker_apps = [
            app
            for app in solution.all_applications
            if app.app_type == AppType.TEMPORAL_WORKER
        ]

        # At least one worker should have local pipelines
        apps_with_pipelines = [app for app in worker_apps if app.markers.has_pipelines]

        assert len(apps_with_pipelines) > 0, (
            "At least one TEMPORAL-WORKER app MUST have local pipelines. "
            "Found workers: "
            + ", ".join(f"{app.slug}@{app.path}" for app in worker_apps)
        )

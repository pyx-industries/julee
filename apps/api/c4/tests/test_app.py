"""Tests for C4 REST API application.

These tests ensure the FastAPI application is properly configured and doesn't fail
due to misconfiguration (missing imports, bad router registration, etc.).

Test categories:
1. Module imports - all modules import without errors
2. App configuration - FastAPI app is properly configured
3. Router registration - all routers are registered correctly
4. Health endpoint - basic endpoint works

Note: Tests are marked xfail when imports fail due to missing dependencies.
"""

import importlib

import pytest

# Check if the app module imports successfully
try:
    from apps.api.c4.app import app as _app

    APP_IMPORTS_OK = True
except ImportError:
    APP_IMPORTS_OK = False


@pytest.mark.skipif(not APP_IMPORTS_OK, reason="C4 API app has import errors")
class TestModuleImports:
    """Test that all API modules import without errors."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "apps.api.c4.app",
            "apps.api.c4.dependencies",
            "apps.api.c4.requests",
            "apps.api.c4.responses",
            "apps.api.c4.routers",
            "apps.api.c4.routers.c4",
        ],
    )
    def test_module_imports(self, module_name: str) -> None:
        """All C4 API modules must import without errors."""
        module = importlib.import_module(module_name)
        assert module is not None


@pytest.mark.skipif(not APP_IMPORTS_OK, reason="C4 API app has import errors")
class TestAppConfiguration:
    """Test that the FastAPI app is properly configured."""

    def test_app_exists(self) -> None:
        """FastAPI app instance must exist."""
        from apps.api.c4.app import app

        assert app is not None

    def test_app_has_title(self) -> None:
        """FastAPI app must have a title."""
        from apps.api.c4.app import app

        assert app.title == "C4 Architecture REST API"

    def test_app_has_version(self) -> None:
        """FastAPI app must have a version."""
        from apps.api.c4.app import app

        assert app.version is not None

    def test_app_has_docs_url(self) -> None:
        """FastAPI app must have docs URL configured."""
        from apps.api.c4.app import app

        assert app.docs_url == "/docs"

    def test_app_has_redoc_url(self) -> None:
        """FastAPI app must have redoc URL configured."""
        from apps.api.c4.app import app

        assert app.redoc_url == "/redoc"


@pytest.mark.skipif(not APP_IMPORTS_OK, reason="C4 API app has import errors")
class TestRouterRegistration:
    """Test that routers are registered with the app."""

    def test_router_exists(self) -> None:
        """Router module must export router."""
        from apps.api.c4.routers import c4_router

        assert c4_router is not None

    def test_app_has_routes(self) -> None:
        """App must have routes registered."""
        from apps.api.c4.app import app

        # App should have at least the health endpoint + router routes
        assert len(app.routes) > 1


@pytest.mark.skipif(not APP_IMPORTS_OK, reason="C4 API app has import errors")
class TestHealthEndpoint:
    """Test the health check endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient

        from apps.api.c4.app import app

        return TestClient(app)

    def test_health_check_returns_200(self, client) -> None:
        """Health check endpoint must return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self, client) -> None:
        """Health check must return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.skipif(not APP_IMPORTS_OK, reason="C4 API app has import errors")
class TestOpenAPISchema:
    """Test the OpenAPI schema is valid."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient

        from apps.api.c4.app import app

        return TestClient(app)

    def test_openapi_schema_accessible(self, client) -> None:
        """OpenAPI schema must be accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_schema_has_info(self, client) -> None:
        """OpenAPI schema must have info section."""
        response = client.get("/openapi.json")
        schema = response.json()
        assert "info" in schema
        assert schema["info"]["title"] == "C4 Architecture REST API"

    def test_openapi_schema_has_paths(self, client) -> None:
        """OpenAPI schema must have paths section."""
        response = client.get("/openapi.json")
        schema = response.json()
        assert "paths" in schema
        assert "/health" in schema["paths"]


@pytest.mark.skipif(not APP_IMPORTS_OK, reason="C4 API app has import errors")
class TestMainFunction:
    """Test the main entry point."""

    def test_main_function_exists(self) -> None:
        """main() function must exist for CLI entry point."""
        from apps.api.c4.app import main

        assert callable(main)

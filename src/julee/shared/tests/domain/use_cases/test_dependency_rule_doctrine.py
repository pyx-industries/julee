"""Dependency Rule doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

The Dependency Rule is the central rule of Clean Architecture:
**Dependencies must point inward.**

Layer hierarchy (outer to inner):
    deployment/ -> apps/ -> infrastructure/ -> use_cases/ -> models/

Protocols (repositories/, services/) sit at the same level as use_cases,
defining abstractions that use_cases depend on. Infrastructure implements
these protocols but use_cases never imports infrastructure directly.
"""

from pathlib import Path

import pytest

from julee.shared.parsers.imports import classify_import_layer, extract_imports


def create_bounded_context(base_path: Path, name: str) -> Path:
    """Helper to create a bounded context directory structure."""
    ctx_path = base_path / name
    ctx_path.mkdir(parents=True)
    (ctx_path / "__init__.py").touch()
    for layer in ["models", "use_cases", "repositories", "services"]:
        layer_path = ctx_path / "domain" / layer
        layer_path.mkdir(parents=True)
        (layer_path / "__init__.py").touch()
    return ctx_path


def write_python_file(path: Path, content: str) -> Path:
    """Write a Python file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# =============================================================================
# DOCTRINE: Layer Classification
# =============================================================================


class TestLayerClassification:
    """Doctrine about identifying architectural layers in imports."""

    def test_models_layer_MUST_be_identified(self):
        """An import path containing 'models' MUST classify as models layer."""
        assert classify_import_layer("julee.hcd.domain.models") == "models"
        assert classify_import_layer("julee.hcd.domain.models.story") == "models"

    def test_use_cases_layer_MUST_be_identified(self):
        """An import path containing 'use_cases' MUST classify as use_cases layer."""
        assert classify_import_layer("julee.hcd.domain.use_cases") == "use_cases"
        assert classify_import_layer("julee.shared.domain.use_cases") == "use_cases"

    def test_repositories_layer_MUST_be_identified(self):
        """An import path containing 'repositories' MUST classify as repositories layer."""
        assert classify_import_layer("julee.hcd.domain.repositories") == "repositories"

    def test_services_layer_MUST_be_identified(self):
        """An import path containing 'services' MUST classify as services layer."""
        assert classify_import_layer("julee.hcd.domain.services") == "services"

    def test_infrastructure_layer_MUST_be_identified(self):
        """An import path containing 'infrastructure' MUST classify as infrastructure layer."""
        assert classify_import_layer("julee.hcd.infrastructure") == "infrastructure"

    def test_apps_layer_MUST_be_identified(self):
        """An import path containing 'apps' MUST classify as apps layer."""
        assert classify_import_layer("apps.api.hcd") == "apps"
        assert classify_import_layer("apps.mcp.c4.server") == "apps"

    def test_deployment_layer_MUST_be_identified(self):
        """An import path containing 'deployment' MUST classify as deployment layer."""
        assert classify_import_layer("deployment.docker") == "deployment"
        assert classify_import_layer("deployment.kubernetes") == "deployment"

    def test_external_imports_MUST_return_None(self):
        """An import from outside the domain MUST return None."""
        assert classify_import_layer("pydantic") is None
        assert classify_import_layer("typing") is None
        assert classify_import_layer("pathlib") is None


# =============================================================================
# DOCTRINE: Dependency Rule - Inner Layers
# =============================================================================


class TestDependencyRuleInnerLayers:
    """The Dependency Rule for domain models (innermost layer).

    Entities are the innermost layer and MUST NOT import from any outer layer:
    - use_cases/
    - repositories/
    - services/
    - infrastructure/
    - apps/
    - deployment/
    """

    @pytest.mark.asyncio
    async def test_entities_MUST_NOT_import_from_use_cases(self, tmp_path: Path):
        """Domain models MUST NOT import from use_cases/.

        The entities layer is innermost and must not depend on outer layers.
        This ensures business rules don't depend on application workflow.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        # Write a models file that violates the rule
        write_python_file(
            ctx / "domain" / "models" / "invoice.py",
            '''"""Invoice entity."""
from julee.billing.domain.use_cases import CreateInvoiceUseCase

class Invoice:
    """An invoice entity."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "models" / "invoice.py")
        violations = [
            imp for imp in imports if classify_import_layer(imp.module) == "use_cases"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_entities_MUST_NOT_import_from_repositories(self, tmp_path: Path):
        """Domain models MUST NOT import from repositories/.

        Entities define business rules independent of persistence.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "models" / "invoice.py",
            '''"""Invoice entity."""
from julee.billing.domain.repositories import InvoiceRepository

class Invoice:
    """An invoice entity."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "models" / "invoice.py")
        violations = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "repositories"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_entities_MUST_NOT_import_from_services(self, tmp_path: Path):
        """Domain models MUST NOT import from services/.

        Entities define business rules independent of external services.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "models" / "invoice.py",
            '''"""Invoice entity."""
from julee.billing.domain.services import PaymentService

class Invoice:
    """An invoice entity."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "models" / "invoice.py")
        violations = [
            imp for imp in imports if classify_import_layer(imp.module) == "services"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_entities_MUST_NOT_import_from_infrastructure(self, tmp_path: Path):
        """Domain models MUST NOT import from infrastructure/.

        Entities must be completely independent of infrastructure concerns.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "models" / "invoice.py",
            '''"""Invoice entity."""
from julee.billing.infrastructure import DatabaseConnection

class Invoice:
    """An invoice entity."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "models" / "invoice.py")
        violations = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "infrastructure"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_entities_MUST_NOT_import_from_apps(self, tmp_path: Path):
        """Domain models MUST NOT import from apps/.

        Entities are framework-agnostic and cannot depend on application layer.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "models" / "invoice.py",
            '''"""Invoice entity."""
from apps.api.billing import router

class Invoice:
    """An invoice entity."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "models" / "invoice.py")
        violations = [
            imp for imp in imports if classify_import_layer(imp.module) == "apps"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_entities_MAY_import_from_other_entities(self, tmp_path: Path):
        """Domain models MAY import from other models in the same layer.

        Entities can compose with other entities at the same level.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "models" / "invoice.py",
            '''"""Invoice entity."""
from julee.billing.domain.models.line_item import LineItem

class Invoice:
    """An invoice entity."""
    items: list[LineItem]
''',
        )

        imports = extract_imports(ctx / "domain" / "models" / "invoice.py")
        model_imports = [
            imp for imp in imports if classify_import_layer(imp.module) == "models"
        ]
        # This is allowed - entities can import other entities
        assert len(model_imports) == 1


# =============================================================================
# DOCTRINE: Dependency Rule - Middle Layers
# =============================================================================


class TestDependencyRuleMiddleLayers:
    """The Dependency Rule for use cases (middle layer).

    Use cases MUST NOT import from outer layers:
    - infrastructure/
    - apps/
    - deployment/

    Use cases MAY import from:
    - models/ (inward dependency)
    - repositories/ (same level - protocols)
    - services/ (same level - protocols)
    """

    @pytest.mark.asyncio
    async def test_use_cases_MUST_NOT_import_from_infrastructure(self, tmp_path: Path):
        """Use cases MUST NOT import from infrastructure/.

        Use cases orchestrate business logic through protocols, never concrete
        implementations. Infrastructure is injected at composition root.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "use_cases" / "create_invoice.py",
            '''"""Create invoice use case."""
from julee.billing.infrastructure.postgres import PostgresInvoiceRepository

class CreateInvoiceUseCase:
    """Create a new invoice."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "use_cases" / "create_invoice.py")
        violations = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "infrastructure"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_use_cases_MUST_NOT_import_from_apps(self, tmp_path: Path):
        """Use cases MUST NOT import from apps/.

        Use cases are application-framework-agnostic. They orchestrate domain
        logic without knowing about FastAPI, MCP, CLI, or any other delivery mechanism.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "use_cases" / "create_invoice.py",
            '''"""Create invoice use case."""
from apps.api.billing.router import get_current_user

class CreateInvoiceUseCase:
    """Create a new invoice."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "use_cases" / "create_invoice.py")
        violations = [
            imp for imp in imports if classify_import_layer(imp.module) == "apps"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_use_cases_MAY_import_from_entities(self, tmp_path: Path):
        """Use cases MAY import from entities (inward dependency).

        Use cases depend on domain models to implement business workflows.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "use_cases" / "create_invoice.py",
            '''"""Create invoice use case."""
from julee.billing.domain.models import Invoice

class CreateInvoiceUseCase:
    """Create a new invoice."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "use_cases" / "create_invoice.py")
        model_imports = [
            imp for imp in imports if classify_import_layer(imp.module) == "models"
        ]
        # This is allowed - use cases can import entities
        assert len(model_imports) == 1

    @pytest.mark.asyncio
    async def test_use_cases_MAY_import_from_repositories(self, tmp_path: Path):
        """Use cases MAY import repository protocols (at same level).

        Repository protocols define persistence abstractions used by use cases.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "use_cases" / "create_invoice.py",
            '''"""Create invoice use case."""
from julee.billing.domain.repositories import InvoiceRepository

class CreateInvoiceUseCase:
    """Create a new invoice."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "use_cases" / "create_invoice.py")
        repo_imports = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "repositories"
        ]
        # This is allowed - use cases use repository protocols
        assert len(repo_imports) == 1

    @pytest.mark.asyncio
    async def test_use_cases_MAY_import_from_services(self, tmp_path: Path):
        """Use cases MAY import service protocols (at same level).

        Service protocols define external service abstractions used by use cases.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "use_cases" / "create_invoice.py",
            '''"""Create invoice use case."""
from julee.billing.domain.services import PaymentService

class CreateInvoiceUseCase:
    """Create a new invoice."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "use_cases" / "create_invoice.py")
        service_imports = [
            imp for imp in imports if classify_import_layer(imp.module) == "services"
        ]
        # This is allowed - use cases use service protocols
        assert len(service_imports) == 1


# =============================================================================
# DOCTRINE: Dependency Rule - Protocols
# =============================================================================


class TestDependencyRuleProtocols:
    """The Dependency Rule for protocol layers."""

    @pytest.mark.asyncio
    async def test_repositories_MUST_NOT_import_from_infrastructure(
        self, tmp_path: Path
    ):
        """Repository protocols MUST NOT import from infrastructure/.

        Protocols define abstractions; they cannot depend on implementations.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "repositories" / "invoice.py",
            '''"""Invoice repository protocol."""
from typing import Protocol
from julee.billing.infrastructure.postgres import PostgresConnection

class InvoiceRepository(Protocol):
    """Repository for invoice persistence."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "repositories" / "invoice.py")
        violations = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "infrastructure"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

    @pytest.mark.asyncio
    async def test_repositories_MAY_import_from_entities(self, tmp_path: Path):
        """Repository protocols MAY import from entities (inward dependency).

        Protocols reference domain models in their method signatures.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "repositories" / "invoice.py",
            '''"""Invoice repository protocol."""
from typing import Protocol
from julee.billing.domain.models import Invoice

class InvoiceRepository(Protocol):
    """Repository for invoice persistence."""
    async def save(self, invoice: Invoice) -> None: ...
''',
        )

        imports = extract_imports(ctx / "domain" / "repositories" / "invoice.py")
        model_imports = [
            imp for imp in imports if classify_import_layer(imp.module) == "models"
        ]
        # This is allowed - protocols reference entities
        assert len(model_imports) == 1

    @pytest.mark.asyncio
    async def test_services_MUST_NOT_import_from_infrastructure(self, tmp_path: Path):
        """Service protocols MUST NOT import from infrastructure/.

        Protocols define abstractions; they cannot depend on implementations.
        """
        ctx = create_bounded_context(tmp_path / "src" / "julee", "billing")

        write_python_file(
            ctx / "domain" / "services" / "payment.py",
            '''"""Payment service protocol."""
from typing import Protocol
from julee.billing.infrastructure.stripe import StripeClient

class PaymentService(Protocol):
    """Service for payment processing."""
    pass
''',
        )

        imports = extract_imports(ctx / "domain" / "services" / "payment.py")
        violations = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "infrastructure"
        ]
        assert len(violations) > 0, "Test fixture should have violations"

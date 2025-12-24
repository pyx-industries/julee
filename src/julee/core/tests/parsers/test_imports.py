"""Unit tests for import parsing and layer classification.

These tests verify the import analysis machinery works correctly.
They use synthetic fixtures to test detection capabilities.

The actual doctrine enforcement happens in test_doctrine_compliance.py,
which runs these tools against the real codebase.
"""

from pathlib import Path

import pytest

from julee.core.parsers.imports import classify_import_layer, extract_imports


def write_python_file(path: Path, content: str) -> Path:
    """Write a Python file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# =============================================================================
# Layer Classification Tests
# =============================================================================


class TestClassifyImportLayer:
    """Unit tests for classify_import_layer function."""

    def test_entities_layer_identified(self):
        """Import paths containing 'entities' or 'models' classify as entities layer."""
        # New flattened path
        assert classify_import_layer("julee.hcd.entities") == "entities"
        assert classify_import_layer("julee.hcd.entities.story") == "entities"
        # Legacy path (models maps to entities layer)
        assert classify_import_layer("julee.hcd.domain.models") == "entities"
        assert classify_import_layer("julee.hcd.domain.models.story") == "entities"

    def test_use_cases_layer_identified(self):
        """Import paths containing 'use_cases' classify as use_cases layer."""
        assert classify_import_layer("julee.hcd.domain.use_cases") == "use_cases"
        assert classify_import_layer("julee.core.domain.use_cases") == "use_cases"

    def test_repositories_layer_identified(self):
        """Import paths containing 'repositories' classify as repositories layer."""
        assert classify_import_layer("julee.hcd.domain.repositories") == "repositories"

    def test_services_layer_identified(self):
        """Import paths containing 'services' classify as services layer."""
        assert classify_import_layer("julee.hcd.domain.services") == "services"

    def test_infrastructure_layer_identified(self):
        """Import paths containing 'infrastructure' classify as infrastructure layer."""
        assert classify_import_layer("julee.hcd.infrastructure") == "infrastructure"

    def test_apps_layer_identified(self):
        """Import paths containing 'apps' classify as apps layer."""
        assert classify_import_layer("apps.api.hcd") == "apps"
        assert classify_import_layer("apps.mcp.c4.server") == "apps"

    def test_deployment_layer_identified(self):
        """Import paths containing 'deployment' classify as deployment layer."""
        assert classify_import_layer("deployment.docker") == "deployment"
        assert classify_import_layer("deployment.kubernetes") == "deployment"

    def test_external_imports_return_none(self):
        """Imports from outside the domain return None."""
        assert classify_import_layer("pydantic") is None
        assert classify_import_layer("typing") is None
        assert classify_import_layer("pathlib") is None


# =============================================================================
# Import Extraction Tests
# =============================================================================


class TestExtractImports:
    """Unit tests for extract_imports function."""

    @pytest.mark.asyncio
    async def test_detects_use_cases_import(self, tmp_path: Path):
        """Detector finds imports from use_cases layer."""
        py_file = write_python_file(
            tmp_path / "test_file.py",
            '''"""Test file."""
from julee.billing.domain.use_cases import CreateInvoiceUseCase

class Invoice:
    pass
''',
        )

        imports = extract_imports(py_file)
        violations = [
            imp for imp in imports if classify_import_layer(imp.module) == "use_cases"
        ]
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_detects_repositories_import(self, tmp_path: Path):
        """Detector finds imports from repositories layer."""
        py_file = write_python_file(
            tmp_path / "test_file.py",
            '''"""Test file."""
from julee.billing.domain.repositories import InvoiceRepository

class Invoice:
    pass
''',
        )

        imports = extract_imports(py_file)
        violations = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "repositories"
        ]
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_detects_services_import(self, tmp_path: Path):
        """Detector finds imports from services layer."""
        py_file = write_python_file(
            tmp_path / "test_file.py",
            '''"""Test file."""
from julee.billing.domain.services import PaymentService

class Invoice:
    pass
''',
        )

        imports = extract_imports(py_file)
        violations = [
            imp for imp in imports if classify_import_layer(imp.module) == "services"
        ]
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_detects_infrastructure_import(self, tmp_path: Path):
        """Detector finds imports from infrastructure layer."""
        py_file = write_python_file(
            tmp_path / "test_file.py",
            '''"""Test file."""
from julee.billing.infrastructure import DatabaseConnection

class Invoice:
    pass
''',
        )

        imports = extract_imports(py_file)
        violations = [
            imp
            for imp in imports
            if classify_import_layer(imp.module) == "infrastructure"
        ]
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_detects_apps_import(self, tmp_path: Path):
        """Detector finds imports from apps layer."""
        py_file = write_python_file(
            tmp_path / "test_file.py",
            '''"""Test file."""
from apps.api.billing import router

class Invoice:
    pass
''',
        )

        imports = extract_imports(py_file)
        violations = [
            imp for imp in imports if classify_import_layer(imp.module) == "apps"
        ]
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_detects_entities_import(self, tmp_path: Path):
        """Detector finds imports from entities layer."""
        py_file = write_python_file(
            tmp_path / "test_file.py",
            '''"""Test file."""
from julee.billing.entities.line_item import LineItem

class Invoice:
    items: list[LineItem]
''',
        )

        imports = extract_imports(py_file)
        entity_imports = [
            imp for imp in imports if classify_import_layer(imp.module) == "entities"
        ]
        assert len(entity_imports) == 1

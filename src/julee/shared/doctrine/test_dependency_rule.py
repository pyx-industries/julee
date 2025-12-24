"""DependencyRule doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

The dependency rule is Clean Architecture's central invariant:
Dependencies must point inward. Outer layers depend on inner layers,
never the reverse.
"""

from pathlib import Path

import pytest

from julee.shared.parsers.imports import classify_import_layer, extract_imports


class TestEntityDependencies:
    """Doctrine about entity layer dependencies."""

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


class TestUseCaseDependencies:
    """Doctrine about use case layer dependencies."""

    @pytest.mark.asyncio
    async def test_all_use_cases_MUST_NOT_import_from_infrastructure(self, repo):
        """All use case files MUST NOT import from infrastructure/.

        Use cases orchestrate business logic through protocols (abstractions),
        never concrete infrastructure implementations.
        """
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


class TestRepositoryProtocolDependencies:
    """Doctrine about repository protocol layer dependencies."""

    @pytest.mark.asyncio
    async def test_all_repository_protocols_MUST_NOT_import_from_infrastructure(
        self, repo
    ):
        """All repository protocol files MUST NOT import from infrastructure/.

        Repository protocols define abstractions; they cannot reference
        concrete implementations.
        """
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


class TestServiceProtocolDependencies:
    """Doctrine about service protocol layer dependencies."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_NOT_import_from_infrastructure(
        self, repo
    ):
        """All service protocol files MUST NOT import from infrastructure/.

        Service protocols define abstractions; they cannot reference
        concrete implementations.
        """
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

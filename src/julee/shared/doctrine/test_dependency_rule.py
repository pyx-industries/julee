"""DependencyRule doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

The dependency rule is Clean Architecture's central invariant:
Dependencies must point inward. Outer layers depend on inner layers,
never the reverse.
"""

from pathlib import Path

import pytest

from julee.shared.domain.doctrine_constants import (
    ENTITIES_PATH,
    REPOSITORIES_PATH,
    SERVICES_PATH,
    USE_CASES_PATH,
)
from julee.shared.parsers.imports import classify_import_layer, extract_imports


def _path_tuple_to_str(path_tuple: tuple[str, ...]) -> str:
    """Convert path tuple to slash-separated string."""
    return "/".join(path_tuple)


class TestEntityDependencies:
    """Doctrine about entity layer dependencies."""

    @pytest.mark.asyncio
    async def test_all_entities_MUST_NOT_import_outward(self, repo):
        """All entity files MUST NOT import from outer layers.

        Entities are innermost and cannot depend on:
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
            entities_dir = Path(ctx.path)
            for part in ENTITIES_PATH:
                entities_dir = entities_dir / part
            if not entities_dir.exists():
                continue

            for py_file in entities_dir.glob("**/*.py"):
                if py_file.name.startswith("_"):
                    continue

                imports = extract_imports(py_file)
                for imp in imports:
                    layer = classify_import_layer(imp.module)
                    if layer in forbidden_layers:
                        violations.append(
                            f"{ctx.slug}/{_path_tuple_to_str(ENTITIES_PATH)}/{py_file.name}: "
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
            use_cases_dir = Path(ctx.path)
            for part in USE_CASES_PATH:
                use_cases_dir = use_cases_dir / part
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
                            f"{ctx.slug}/{_path_tuple_to_str(USE_CASES_PATH)}/{py_file.name}: "
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
            repos_dir = Path(ctx.path)
            for part in REPOSITORIES_PATH:
                repos_dir = repos_dir / part
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
                            f"{ctx.slug}/{_path_tuple_to_str(REPOSITORIES_PATH)}/{py_file.name}: "
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
            services_dir = Path(ctx.path)
            for part in SERVICES_PATH:
                services_dir = services_dir / part
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
                            f"{ctx.slug}/{_path_tuple_to_str(SERVICES_PATH)}/{py_file.name}: "
                            f"imports from {layer} ({imp.module})"
                        )

        assert (
            not violations
        ), "Service protocols importing from outer layers:\n" + "\n".join(violations)

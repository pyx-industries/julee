"""Sphinx Extension doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

SPHINX-EXTENSION applications provide Sphinx directives that render
domain entities into documentation. Like REST-API endpoints, directives
are thin adapters over use cases.

Doctrine (axioms - what Sphinx Extensions ARE):
- Directives MUST access domain logic through use cases, not repositories
- Placeholder node classes MUST be module-level for pickle serialization
- Generated directives replace manual ones - no duplicates allowed
"""

import ast
import re
from pathlib import Path

import pytest

from julee.core.entities.application import AppType
from julee.core.infrastructure.repositories.introspection.application import (
    FilesystemApplicationRepository,
)


def _find_directive_files(app_path: Path) -> list[Path]:
    """Find all directive files in a Sphinx extension.

    Searches for files in directives/ directories.
    """
    directive_files = []

    # Direct directives/ directory
    directives_dir = app_path / "directives"
    if directives_dir.exists():
        for f in directives_dir.glob("*.py"):
            if not f.name.startswith("_"):
                directive_files.append(f)

    # BC-organized subdirs (e.g., apps/sphinx/hcd/directives/)
    for subdir in app_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith(("_", ".")):
            if subdir.name not in ("shared", "tests", "__pycache__", "templates"):
                nested_directives = subdir / "directives"
                if nested_directives.exists():
                    for f in nested_directives.glob("*.py"):
                        if not f.name.startswith("_"):
                            directive_files.append(f)

    return directive_files


def _find_generated_directive_files(app_path: Path) -> list[Path]:
    """Find generated_directives.py files in a Sphinx extension."""
    generated_files = []

    # Direct generated_directives.py
    direct = app_path / "generated_directives.py"
    if direct.exists():
        generated_files.append(direct)

    # BC-organized (e.g., apps/sphinx/hcd/generated_directives.py)
    for subdir in app_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith(("_", ".")):
            nested = subdir / "generated_directives.py"
            if nested.exists():
                generated_files.append(nested)

    return generated_files


def _extract_direct_repo_access(file_path: Path) -> list[dict]:
    """Extract direct repository access patterns from a file.

    Detects patterns like:
    - repo.get(), repo.list(), repo.create()
    - *_repo.get(), *_repo.list()
    - repository.*, async_repo.*

    Does NOT flag:
    - use_case.execute_sync(), hcd_context.list_*.execute_sync()
    - Imports of repo classes (for type hints)
    - clear_by_docname() calls (infrastructure cleanup, not business logic)
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    violations = []
    # Business operations that should go through use cases
    repo_method_pattern = re.compile(
        r"(repo|repository|async_repo)\.(get|list|create|update|delete)"
    )
    # Infrastructure operations that are acceptable (Sphinx lifecycle)
    infrastructure_pattern = re.compile(r"clear_by_docname|clear_all")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for attribute calls like repo.get(), *_repo.list()
            if isinstance(node.func, ast.Attribute):
                # Get the full attribute chain as string
                try:
                    call_str = ast.unparse(node.func)
                except Exception:
                    continue

                # Check if it matches repo access pattern
                if repo_method_pattern.search(call_str):
                    # Exclude use case execute patterns
                    if ".execute_sync" in call_str or ".execute_async" in call_str:
                        continue
                    # Exclude infrastructure cleanup operations
                    if infrastructure_pattern.search(call_str):
                        continue

                    violations.append(
                        {
                            "line": node.lineno,
                            "call": call_str,
                        }
                    )

    return violations


def _extract_dynamic_class_creation(file_path: Path) -> list[dict]:
    """Find dynamically created classes using type().

    Placeholder classes created with type() fail pickle serialization
    because they can't be imported by qualified name.
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for type("ClassName", bases, dict) pattern
            if isinstance(node.func, ast.Name) and node.func.id == "type":
                if len(node.args) >= 3:
                    # This is a class creation, not a type check
                    class_name = None
                    if isinstance(node.args[0], ast.Constant):
                        class_name = node.args[0].value

                    violations.append(
                        {
                            "line": node.lineno,
                            "class_name": class_name or "<dynamic>",
                        }
                    )

    return violations


def _extract_placeholder_classes(file_path: Path) -> list[str]:
    """Extract placeholder class names from a file.

    Looks for classes ending in 'Placeholder' that inherit from nodes.Element.
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    placeholders = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if "Placeholder" in node.name:
                placeholders.append(node.name)

    return placeholders


def _extract_directive_classes(file_path: Path) -> list[str]:
    """Extract directive class names from a file.

    Looks for classes ending in 'Directive'.
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    directives = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name.endswith("Directive"):
                directives.append(node.name)

    return directives


# =============================================================================
# DOCTRINE: Use Case Access Pattern
# =============================================================================


class TestSphinxDirectiveUseCasePattern:
    """Doctrine about Sphinx directive use case access."""

    @pytest.mark.asyncio
    async def test_sphinx_extension_apps_exist(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """SPHINX-EXTENSION applications MUST be discoverable."""
        apps = await app_repo.list_by_type(AppType.SPHINX_EXTENSION)

        if len(apps) == 0:
            pytest.skip("No SPHINX-EXTENSION applications in this solution")

    @pytest.mark.asyncio
    async def test_directives_MUST_NOT_access_repositories_directly(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """Directive files MUST NOT access repositories directly.

        Doctrine: Sphinx directives are thin adapters over use cases, just like
        REST endpoints. They MUST call use_case.execute_sync() or access domain
        logic through a context object that exposes use cases.

        Direct repository access (repo.get(), repo.list(), etc.) bypasses the
        use case layer and violates Clean Architecture.

        Acceptable patterns:
        - hcd_context.list_stories.execute_sync(request)
        - use_case.execute_sync(request)

        Forbidden patterns:
        - repo.get(), repo.list(), repo.create()
        - hcd_context.story_repo.get()
        """
        apps = await app_repo.list_by_type(AppType.SPHINX_EXTENSION)

        violations = []

        for app in apps:
            directive_files = _find_directive_files(Path(app.path))

            for directive_file in directive_files:
                # Skip base.py - it may have helper utilities
                if directive_file.name == "base.py":
                    continue

                repo_accesses = _extract_direct_repo_access(directive_file)

                for access in repo_accesses:
                    violations.append(
                        f"{directive_file.relative_to(Path(app.path))}:"
                        f"{access['line']} - direct repo access: {access['call']}"
                    )

        assert (
            not violations
        ), "Directive files MUST use use cases, not direct repo access:\n" + "\n".join(
            f"  - {v}" for v in violations
        )


# =============================================================================
# DOCTRINE: Placeholder Serialization
# =============================================================================


class TestSphinxPlaceholderSerialization:
    """Doctrine about Sphinx placeholder pickle serialization."""

    @pytest.mark.asyncio
    async def test_placeholder_classes_MUST_NOT_be_dynamically_created(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """Placeholder node classes MUST NOT be created with type().

        Doctrine: Sphinx pickles doctrees for incremental builds. Classes
        created dynamically with type() cannot be pickled because they don't
        have a stable qualified name that can be imported.

        Placeholder classes MUST be defined at module level:

        # GOOD - module-level class definition
        class MyPlaceholder(nodes.General, nodes.Element):
            pass

        # BAD - dynamic class creation
        MyPlaceholder = type("MyPlaceholder", (nodes.General, nodes.Element), {})

        This ensures Sphinx can serialize and deserialize doctrees correctly
        during incremental builds.
        """
        apps = await app_repo.list_by_type(AppType.SPHINX_EXTENSION)

        violations = []

        for app in apps:
            # Check directive files
            directive_files = _find_directive_files(Path(app.path))
            generated_files = _find_generated_directive_files(Path(app.path))

            for py_file in directive_files + generated_files:
                dynamic_classes = _extract_dynamic_class_creation(py_file)

                for dynamic in dynamic_classes:
                    # Only flag if it looks like a placeholder
                    if "Placeholder" in dynamic["class_name"]:
                        violations.append(
                            f"{py_file.relative_to(Path(app.path))}:"
                            f"{dynamic['line']} - dynamic placeholder: "
                            f"{dynamic['class_name']}"
                        )

        assert not violations, (
            "Placeholder classes MUST be module-level, not created with type():\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# =============================================================================
# DOCTRINE: No Duplicate Directive Implementations
# =============================================================================


class TestSphinxDirectiveDeduplication:
    """Doctrine about directive implementation deduplication."""

    @pytest.mark.asyncio
    async def test_generated_directives_MUST_NOT_have_manual_duplicates(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """Generated directives MUST replace manual implementations.

        Doctrine: When a directive is generated via factory pattern
        (e.g., GeneratedPersonaIndexDirective), the manual implementation
        (PersonaIndexDirective) MUST be removed from the directives/ module.

        Having both creates confusion about which is canonical and risks
        divergent behavior.

        The generated_directives.py module is the source of truth for
        factory-generated directives. Manual implementations in directives/
        are the source of truth for complex directives that can't be factored.
        """
        apps = await app_repo.list_by_type(AppType.SPHINX_EXTENSION)

        violations = []

        for app in apps:
            generated_files = _find_generated_directive_files(Path(app.path))

            # Extract Generated*Directive names
            generated_directive_names = set()
            for gen_file in generated_files:
                directives = _extract_directive_classes(gen_file)
                for name in directives:
                    # GeneratedPersonaIndexDirective -> PersonaIndexDirective
                    if name.startswith("Generated"):
                        manual_name = name[len("Generated") :]
                        generated_directive_names.add(manual_name)

            # Check directive files for duplicates
            directive_files = _find_directive_files(Path(app.path))
            for directive_file in directive_files:
                manual_directives = _extract_directive_classes(directive_file)

                for manual_name in manual_directives:
                    if manual_name in generated_directive_names:
                        violations.append(
                            f"{directive_file.relative_to(Path(app.path))}: "
                            f"{manual_name} exists but Generated{manual_name} "
                            f"also exists - remove the manual implementation"
                        )

        assert (
            not violations
        ), "Generated directives MUST replace manual implementations:\n" + "\n".join(
            f"  - {v}" for v in violations
        )

    @pytest.mark.asyncio
    async def test_generated_placeholders_MUST_NOT_have_manual_duplicates(
        self, app_repo: FilesystemApplicationRepository
    ) -> None:
        """Generated placeholders MUST replace manual implementations.

        Doctrine: When a placeholder is generated via factory pattern
        (e.g., GeneratedPersonaIndexPlaceholder), the manual implementation
        (PersonaIndexPlaceholder) MUST be removed from the directives/ module.
        """
        apps = await app_repo.list_by_type(AppType.SPHINX_EXTENSION)

        violations = []

        for app in apps:
            generated_files = _find_generated_directive_files(Path(app.path))

            # Extract Generated*Placeholder names
            generated_placeholder_names = set()
            for gen_file in generated_files:
                placeholders = _extract_placeholder_classes(gen_file)
                for name in placeholders:
                    # GeneratedPersonaIndexPlaceholder -> PersonaIndexPlaceholder
                    if name.startswith("Generated"):
                        manual_name = name[len("Generated") :]
                        generated_placeholder_names.add(manual_name)

            # Check directive files for duplicates
            directive_files = _find_directive_files(Path(app.path))
            for directive_file in directive_files:
                manual_placeholders = _extract_placeholder_classes(directive_file)

                for manual_name in manual_placeholders:
                    if manual_name in generated_placeholder_names:
                        violations.append(
                            f"{directive_file.relative_to(Path(app.path))}: "
                            f"{manual_name} exists but Generated{manual_name} "
                            f"also exists - remove the manual implementation"
                        )

        assert (
            not violations
        ), "Generated placeholders MUST replace manual implementations:\n" + "\n".join(
            f"  - {v}" for v in violations
        )

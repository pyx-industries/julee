"""Filesystem-based doctrine repository.

Extracts doctrine rules FROM test files by parsing their AST.
The tests ARE the doctrine - this repository is a projection,
not a separate store. Change a test docstring, change the rule.

This preserves the single-source-of-truth principle while enabling
introspection, display, and cross-referencing of doctrine rules.
"""

import ast
from pathlib import Path

from julee.core.entities.doctrine import (
    DoctrineArea,
    DoctrineCategory,
    DoctrineRule,
)

__all__ = ["FilesystemDoctrineRepository"]


class FilesystemDoctrineRepository:
    """Repository that extracts doctrine by parsing test files.

    Scans doctrine test directories, parses Python AST to extract
    docstrings from test classes and methods. The test file structure
    maps to entity types in julee.core.entities.

    The repository is read-only - doctrine is written by writing tests.
    """

    def __init__(
        self,
        doctrine_dir: Path,
        entities_dir: Path,
    ) -> None:
        """Initialize repository.

        Args:
            doctrine_dir: Directory containing doctrine test files
            entities_dir: Directory containing entity definitions
        """
        self.doctrine_dir = doctrine_dir
        self.entities_dir = entities_dir
        self._cache: dict[str, DoctrineArea] | None = None

    def _ensure_cache(self) -> dict[str, DoctrineArea]:
        """Load and cache all doctrine areas."""
        if self._cache is None:
            self._cache = self._extract_all_doctrine()
        return self._cache

    async def list_rules(self, area: str | None = None) -> list[DoctrineRule]:
        """List all doctrine rules, optionally filtered by area.

        Args:
            area: Optional area slug to filter by (e.g., "bounded_context")

        Returns:
            All matching doctrine rules
        """
        areas = self._ensure_cache()

        if area:
            # Normalize area name for lookup
            area_lower = area.lower().replace(" ", "_").replace("-", "_")
            for area_obj in areas.values():
                if area_obj.slug == area_lower or area_lower in area_obj.name.lower():
                    return area_obj.all_rules
            return []

        # Return all rules from all areas
        return [rule for area_obj in areas.values() for rule in area_obj.all_rules]

    async def list_areas(self) -> list[DoctrineArea]:
        """List all doctrine areas with their rules.

        Returns:
            All doctrine areas, each containing their categories and rules
        """
        areas = self._ensure_cache()
        return list(areas.values())

    async def get_area(self, slug: str) -> DoctrineArea | None:
        """Get a specific doctrine area by slug.

        Args:
            slug: The area identifier (e.g., "bounded_context")

        Returns:
            DoctrineArea if found, None otherwise
        """
        areas = self._ensure_cache()

        # Normalize slug for lookup
        slug_lower = slug.lower().replace(" ", "_").replace("-", "_")
        for area in areas.values():
            if area.slug == slug_lower:
                return area
        return None

    def _extract_all_doctrine(self) -> dict[str, DoctrineArea]:
        """Extract all doctrine from test files.

        Each test file in doctrine_dir corresponds to an entity type.
        The entity docstring provides the definition.

        Returns:
            Dict mapping display name to DoctrineArea
        """
        if not self.doctrine_dir.exists():
            return {}

        doctrine: dict[str, DoctrineArea] = {}

        for test_file in sorted(self.doctrine_dir.glob("test_*.py")):
            if test_file.stem == "test_doctrine_coverage":
                continue  # Skip meta-test

            # Extract entity name: test_bounded_context.py -> bounded_context
            entity_slug = test_file.stem.replace("test_", "")

            # Get categories from test file
            categories = self._extract_categories_from_file(test_file, entity_slug)
            if not categories:
                continue

            # Get definition from corresponding entity file
            entity_file = self.entities_dir / f"{entity_slug}.py"
            definition = self._extract_entity_definition(entity_file)

            # Make name more readable: bounded_context -> Bounded Context
            display_name = entity_slug.replace("_", " ").title()

            doctrine[display_name] = DoctrineArea(
                name=display_name,
                slug=entity_slug,
                definition=definition,
                categories=tuple(categories),
            )

        return doctrine

    def _extract_categories_from_file(
        self, file_path: Path, area_slug: str
    ) -> list[DoctrineCategory]:
        """Extract doctrine categories from a test file.

        Parses the AST to find test classes and methods, extracting their
        docstrings as doctrine statements.

        Args:
            file_path: Path to a doctrine test file
            area_slug: The entity type this file covers

        Returns:
            List of doctrine categories with their rules
        """
        try:
            source = file_path.read_text()
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, OSError):
            return []

        area_name = area_slug.replace("_", " ").title()
        categories = []

        # Use iter_child_nodes to get top-level classes only
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                # Get class docstring as category description
                class_doc = ast.get_docstring(node) or ""
                category_name = node.name[4:]  # Strip "Test" prefix

                # Make name more readable: TestBoundedContextStructure -> Bounded Context Structure
                readable_name = ""
                for char in category_name:
                    if char.isupper() and readable_name:
                        readable_name += " "
                    readable_name += char

                rules = []
                for item in node.body:
                    # Handle both sync and async test methods
                    if isinstance(
                        item, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ) and item.name.startswith("test_"):
                        doc = ast.get_docstring(item)
                        if doc:
                            rules.append(
                                DoctrineRule(
                                    statement=doc,
                                    test_name=item.name,
                                    test_file=file_path,
                                    category=readable_name,
                                    area=area_name,
                                )
                            )

                if rules:
                    categories.append(
                        DoctrineCategory(
                            name=readable_name,
                            description=class_doc,
                            rules=tuple(rules),
                        )
                    )

        return categories

    def _extract_entity_definition(self, entity_file: Path) -> str:
        """Extract the definition from an entity file.

        Looks for either:
        1. The primary class docstring (if the file contains a class matching the filename)
        2. The module docstring

        Args:
            entity_file: Path to a julee.core.entities/*.py file

        Returns:
            The definition string, or empty string if not found
        """
        if not entity_file.exists():
            return ""

        try:
            source = entity_file.read_text()
            tree = ast.parse(source, filename=str(entity_file))
        except (SyntaxError, OSError):
            return ""

        # First, try to find the primary class (name matches filename in PascalCase)
        expected_class_name = "".join(
            word.capitalize() for word in entity_file.stem.split("_")
        )

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and node.name == expected_class_name:
                docstring = ast.get_docstring(node)
                if docstring:
                    return docstring

        # Fall back to module docstring
        module_docstring = ast.get_docstring(tree)
        return module_docstring or ""

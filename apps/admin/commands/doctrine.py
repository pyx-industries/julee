"""Doctrine commands.

Commands for displaying architectural doctrine rules extracted from doctrine tests.
The doctrine tests ARE the doctrine - this command extracts and displays them.

Each doctrine test file corresponds to an entity in domain/models/.
The entity docstring is the definition; test docstrings are the rules.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

import click

# Doctrine location - each test file maps to an entity in entities/
DOCTRINE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "julee"
    / "core"
    / "doctrine"
)
MODELS_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "julee"
    / "core"
    / "entities"
)


@dataclass
class DoctrineRule:
    """A single doctrine rule extracted from a test."""

    statement: str
    test_name: str
    test_file: str


@dataclass
class DoctrineCategory:
    """A category of doctrine rules."""

    name: str
    description: str
    rules: list[DoctrineRule]


@dataclass
class DoctrineArea:
    """A doctrine area with definition and rules.

    Each area corresponds to an entity in domain/models/.
    The definition comes from the entity's docstring.
    """

    name: str
    definition: str  # From entity docstring
    categories: list[DoctrineCategory] = field(default_factory=list)

    @property
    def all_rules(self) -> list[DoctrineRule]:
        """Get all rules from all categories."""
        return [rule for cat in self.categories for rule in cat.rules]

    @property
    def rule_count(self) -> int:
        """Get total number of rules."""
        return sum(len(cat.rules) for cat in self.categories)


def extract_entity_definition(entity_file: Path) -> str:
    """Extract the definition from an entity file.

    Looks for either:
    1. The primary class docstring (if the file contains a class matching the filename)
    2. The module docstring

    Args:
        entity_file: Path to a domain/models/*.py file

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


def extract_doctrine_from_file(file_path: Path) -> list[DoctrineCategory]:
    """Extract doctrine rules from a test file.

    Parses the AST to find test classes and methods, extracting their
    docstrings as doctrine statements.

    Args:
        file_path: Path to a doctrine test file

    Returns:
        List of doctrine categories with their rules
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        return []

    categories = []

    # Use iter_child_nodes to get top-level classes only
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            # Get class docstring as category description
            class_doc = ast.get_docstring(node) or ""
            category_name = node.name[4:]  # Strip "Test" prefix

            # Make name more readable
            readable_name = ""
            for char in category_name:
                if char.isupper() and readable_name:
                    readable_name += " "
                readable_name += char

            rules = []
            for item in node.body:
                # Handle both sync and async test methods
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    doc = ast.get_docstring(item)
                    if doc:
                        rules.append(DoctrineRule(
                            statement=doc,
                            test_name=item.name,
                            test_file=file_path.name,
                        ))

            if rules:
                categories.append(DoctrineCategory(
                    name=readable_name,
                    description=class_doc,
                    rules=rules,
                ))

    return categories


def extract_all_doctrine_new(
    doctrine_dir: Path, models_dir: Path
) -> dict[str, DoctrineArea]:
    """Extract all doctrine from the new doctrine/ directory structure.

    Each test file in doctrine/ corresponds to an entity in domain/models/.
    The entity docstring provides the definition.

    Args:
        doctrine_dir: Directory containing doctrine test files (doctrine/)
        models_dir: Directory containing entity files (domain/models/)

    Returns:
        Dict mapping entity name to DoctrineArea
    """
    doctrine: dict[str, DoctrineArea] = {}

    for test_file in sorted(doctrine_dir.glob("test_*.py")):
        if test_file.stem == "test_doctrine_coverage":
            continue  # Skip meta-test

        # Extract entity name: test_bounded_context.py -> bounded_context
        entity_name = test_file.stem.replace("test_", "")

        # Get categories from test file
        categories = extract_doctrine_from_file(test_file)
        if not categories:
            continue

        # Get definition from corresponding entity file
        entity_file = models_dir / f"{entity_name}.py"
        definition = extract_entity_definition(entity_file)

        # Make name more readable: bounded_context -> Bounded Context
        display_name = entity_name.replace("_", " ").title()

        doctrine[display_name] = DoctrineArea(
            name=display_name,
            definition=definition,
            categories=categories,
        )

    return doctrine


def format_doctrine_with_definitions(doctrine: dict[str, DoctrineArea]) -> str:
    """Format doctrine with entity definitions.

    Shows the entity definition followed by its rules.

    Args:
        doctrine: Dict mapping area name to DoctrineArea

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("ARCHITECTURAL DOCTRINE")
    lines.append("=" * 70)
    lines.append("")

    for area_name, area in doctrine.items():
        lines.append(f"{area_name}")
        lines.append("-" * len(area_name))

        # Show definition (first paragraph only for brevity)
        if area.definition:
            # Get first paragraph
            paragraphs = area.definition.split("\n\n")
            first_para = paragraphs[0].strip()
            lines.append(first_para)
            lines.append("")

        # Show rules
        lines.append("Rules:")
        for rule in area.all_rules:
            # Only show first line of docstring
            first_line = rule.statement.split("\n")[0].strip()
            lines.append(f"  - {first_line}")

        lines.append("")

    return "\n".join(lines)


def format_doctrine_verbose(doctrine: dict[str, DoctrineArea]) -> str:
    """Format doctrine with full definitions and categorized rules.

    Args:
        doctrine: Dict mapping area name to DoctrineArea

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("ARCHITECTURAL DOCTRINE")
    lines.append("=" * 70)
    lines.append("")
    lines.append(
        "These rules are enforced by doctrine tests. "
        "The tests ARE the doctrine -"
    )
    lines.append("docstrings state rules, assertions enforce them.")
    lines.append("")

    for area_name, area in doctrine.items():
        lines.append("-" * 70)
        lines.append(f"{area_name.upper()}")
        lines.append("-" * 70)
        lines.append("")

        # Show full definition
        if area.definition:
            for line in area.definition.split("\n"):
                lines.append(f"  {line}")
            lines.append("")

        # Show rules by category
        for category in area.categories:
            if category.description:
                lines.append(f"  {category.name}: {category.description}")
            else:
                lines.append(f"  {category.name}")
            lines.append("")

            for rule in category.rules:
                # Only show first line of docstring
                first_line = rule.statement.split("\n")[0].strip()
                lines.append(f"    - {first_line}")

            lines.append("")

    return "\n".join(lines)


@click.group(name="doctrine")
def doctrine_group() -> None:
    """Display architectural doctrine."""
    pass


@doctrine_group.command(name="show")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show full definitions and categorized rules"
)
@click.option("--area", "-a", help="Filter to specific doctrine area")
def show_doctrine(verbose: bool, area: str | None) -> None:
    """Show architectural doctrine rules.

    Extracts doctrine from test files. Each doctrine test file corresponds
    to an entity in entities/. The entity docstring provides the
    definition; test docstrings are the rules.
    """
    if not DOCTRINE_DIR.exists():
        click.echo(f"Doctrine tests directory not found: {DOCTRINE_DIR}", err=True)
        raise SystemExit(1)

    doctrine = extract_all_doctrine_new(DOCTRINE_DIR, MODELS_DIR)

    if not doctrine:
        click.echo("No doctrine tests found.")
        return

    if area:
        # Filter to specific area
        area_lower = area.lower()
        filtered = {k: v for k, v in doctrine.items() if area_lower in k.lower()}
        if not filtered:
            click.echo(f"No doctrine found for area '{area}'")
            click.echo(f"Available areas: {', '.join(doctrine.keys())}")
            raise SystemExit(1)
        doctrine = filtered

    if verbose:
        click.echo(format_doctrine_verbose(doctrine))
    else:
        click.echo(format_doctrine_with_definitions(doctrine))


@doctrine_group.command(name="list")
def list_doctrine_areas() -> None:
    """List available doctrine areas."""
    if not DOCTRINE_DIR.exists():
        click.echo(f"Doctrine tests directory not found: {DOCTRINE_DIR}", err=True)
        raise SystemExit(1)

    doctrine = extract_all_doctrine_new(DOCTRINE_DIR, MODELS_DIR)

    if not doctrine:
        click.echo("No doctrine tests found.")
        return

    click.echo("Doctrine Areas:")
    click.echo("")
    for area_name, area in doctrine.items():
        click.echo(f"  {area_name}: {area.rule_count} rules")


@doctrine_group.command(name="verify")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed verification report"
)
@click.option("--area", "-a", help="Filter to specific doctrine area")
def verify_doctrine(verbose: bool, area: str | None) -> None:
    """Verify codebase compliance with architectural doctrine.

    Runs doctrine tests and displays results in a structured format.
    The tests ARE the doctrine - this command executes them and
    reports which rules pass or fail.
    """
    from apps.admin.commands.doctrine_plugin import run_doctrine_verification
    from apps.admin.templates import render_doctrine_verify

    if not DOCTRINE_DIR.exists():
        click.echo(f"Doctrine tests directory not found: {DOCTRINE_DIR}", err=True)
        raise SystemExit(1)

    click.echo("Running doctrine verification...\n")

    results, exit_code = run_doctrine_verification(DOCTRINE_DIR)

    if not results:
        click.echo("No doctrine tests found.")
        return

    if area:
        # Filter to specific area
        area_lower = area.lower()
        filtered = {k: v for k, v in results.items() if area_lower in k.lower()}
        if not filtered:
            click.echo(f"No doctrine found for area '{area}'")
            click.echo(f"Available areas: {', '.join(results.keys())}")
            raise SystemExit(1)
        results = filtered

    output = render_doctrine_verify(results, verbose=verbose)
    click.echo(output)

    # Exit with appropriate code
    raise SystemExit(exit_code)

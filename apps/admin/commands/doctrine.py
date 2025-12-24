"""Doctrine commands.

Commands for displaying architectural doctrine rules extracted from doctrine tests.
The doctrine tests ARE the doctrine - this command extracts and displays them.
"""

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import click

# Default location for doctrine tests
DOCTRINE_TESTS_DIR = Path(__file__).parent.parent.parent.parent / "src" / "julee" / "shared" / "tests" / "domain" / "use_cases"


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


def extract_all_doctrine(tests_dir: Path) -> dict[str, list[DoctrineCategory]]:
    """Extract all doctrine from doctrine test files.

    Args:
        tests_dir: Directory containing doctrine test files

    Returns:
        Dict mapping doctrine area to list of categories
    """
    doctrine = {}

    # Match both patterns: test_*_doctrine.py and test_doctrine_*.py
    doctrine_files = set()
    doctrine_files.update(tests_dir.glob("test_*_doctrine.py"))
    doctrine_files.update(tests_dir.glob("test_doctrine_*.py"))

    for test_file in sorted(doctrine_files):
        categories = extract_doctrine_from_file(test_file)
        if categories:
            # For compliance tests, use category names as areas
            # For other doctrine tests, use filename-derived area name
            if "compliance" in test_file.stem:
                # Use each category as its own area for compliance tests
                for category in categories:
                    area_name = category.name
                    if area_name not in doctrine:
                        doctrine[area_name] = []
                    doctrine[area_name].append(category)
            else:
                # Extract area name from filename: test_foo_doctrine.py -> Foo
                area_name = test_file.stem.replace("test_", "").replace("_doctrine", "")
                area_name = area_name.replace("_", " ").title()
                doctrine[area_name] = categories

    return doctrine


def format_doctrine_summary(doctrine: dict[str, list[DoctrineCategory]]) -> str:
    """Format doctrine as a readable summary.

    Args:
        doctrine: Dict mapping area to categories

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("ARCHITECTURAL DOCTRINE")
    lines.append("=" * 70)
    lines.append("")
    lines.append("These rules are enforced by doctrine tests.")
    lines.append("The tests ARE the doctrine - docstrings state rules, assertions enforce them.")
    lines.append("")

    for area, categories in doctrine.items():
        lines.append("-" * 70)
        lines.append(f"{area.upper()}")
        lines.append("-" * 70)
        lines.append("")

        for category in categories:
            if category.description:
                lines.append(f"  {category.name}: {category.description}")
            else:
                lines.append(f"  {category.name}")
            lines.append("")

            for rule in category.rules:
                # Only show first line of docstring
                first_line = rule.statement.split('\n')[0].strip()
                lines.append(f"    - {first_line}")

            lines.append("")

    return "\n".join(lines)


def format_doctrine_table(doctrine: dict[str, list[DoctrineCategory]]) -> str:
    """Format doctrine as a condensed table.

    Args:
        doctrine: Dict mapping area to categories

    Returns:
        Formatted string
    """
    lines = []
    lines.append("ARCHITECTURAL DOCTRINE")
    lines.append("")

    for area, categories in doctrine.items():
        lines.append(f"{area}:")
        for category in categories:
            for rule in category.rules:
                # Only show first line of docstring
                first_line = rule.statement.split('\n')[0].strip()
                lines.append(f"  - {first_line}")
        lines.append("")

    return "\n".join(lines)


@click.group(name="doctrine")
def doctrine_group() -> None:
    """Display architectural doctrine."""
    pass


@doctrine_group.command(name="show")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information including test names")
@click.option("--area", "-a", help="Filter to specific doctrine area")
def show_doctrine(verbose: bool, area: str | None) -> None:
    """Show architectural doctrine rules.

    Extracts doctrine from test files. The tests ARE the doctrine -
    their docstrings state rules, their assertions enforce them.
    """
    if not DOCTRINE_TESTS_DIR.exists():
        click.echo(f"Doctrine tests directory not found: {DOCTRINE_TESTS_DIR}", err=True)
        raise SystemExit(1)

    doctrine = extract_all_doctrine(DOCTRINE_TESTS_DIR)

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
        click.echo(format_doctrine_summary(doctrine))
    else:
        click.echo(format_doctrine_table(doctrine))


@doctrine_group.command(name="list")
def list_doctrine_areas() -> None:
    """List available doctrine areas."""
    if not DOCTRINE_TESTS_DIR.exists():
        click.echo(f"Doctrine tests directory not found: {DOCTRINE_TESTS_DIR}", err=True)
        raise SystemExit(1)

    doctrine = extract_all_doctrine(DOCTRINE_TESTS_DIR)

    if not doctrine:
        click.echo("No doctrine tests found.")
        return

    click.echo("Doctrine Areas:")
    click.echo("")
    for area, categories in doctrine.items():
        rule_count = sum(len(c.rules) for c in categories)
        click.echo(f"  {area}: {rule_count} rules")


@doctrine_group.command(name="verify")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed verification report")
@click.option("--area", "-a", help="Filter to specific doctrine area")
def verify_doctrine(verbose: bool, area: str | None) -> None:
    """Verify codebase compliance with architectural doctrine.

    Runs doctrine tests and displays results in a structured format.
    The tests ARE the doctrine - this command executes them and
    reports which rules pass or fail.
    """
    if not DOCTRINE_TESTS_DIR.exists():
        click.echo(f"Doctrine tests directory not found: {DOCTRINE_TESTS_DIR}", err=True)
        raise SystemExit(1)

    from apps.admin.commands.doctrine_plugin import run_doctrine_verification
    from apps.admin.templates import render_doctrine_verify

    click.echo("Running doctrine verification...\n")

    results, exit_code = run_doctrine_verification(DOCTRINE_TESTS_DIR)

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

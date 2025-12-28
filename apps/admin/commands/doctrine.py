"""Doctrine commands.

Commands for displaying architectural doctrine rules extracted from doctrine tests.
The doctrine tests ARE the doctrine - this command extracts and displays them.

These commands are thin wrappers around julee.core use cases.
"""

import asyncio
from pathlib import Path

import click

from apps.admin.dependencies import (
    find_project_root,
    get_list_doctrine_areas_use_case,
    get_list_doctrine_rules_use_case,
)
from julee.core.entities.doctrine import DoctrineArea
from julee.core.use_cases.list_doctrine_rules import (
    ListDoctrineAreasRequest,
    ListDoctrineRulesRequest,
)

# Framework root (where doctrine tests live)
JULEE_ROOT = Path(__file__).parent.parent.parent.parent
DOCTRINE_DIR = JULEE_ROOT / "src" / "julee" / "core" / "doctrine"


def _discover_app_doctrine_dirs() -> dict[str, Path]:
    """Discover all app doctrine directories using Solution introspection.

    Returns dict mapping app slug to doctrine directory path.
    Uses JULEE_TARGET env var if set, otherwise falls back to find_project_root().
    """
    import os

    from julee.core.infrastructure.repositories.introspection.solution import (
        FilesystemSolutionRepository,
    )

    # Use JULEE_TARGET if set (by verify command), otherwise find project root
    target = os.environ.get("JULEE_TARGET")
    project_root = Path(target) if target else find_project_root()

    async def _discover():
        repo = FilesystemSolutionRepository(project_root)
        solution = await repo.get()
        dirs = {}
        for app in solution.all_applications:
            doctrine_dir = Path(app.path) / "doctrine"
            if doctrine_dir.exists():
                dirs[app.slug] = doctrine_dir
        return dirs

    return asyncio.run(_discover())


# =============================================================================
# Output Formatting
# =============================================================================


def format_doctrine_brief(areas: list[DoctrineArea]) -> str:
    """Format doctrine areas with brief rule listings."""
    lines = []
    lines.append("=" * 70)
    lines.append("ARCHITECTURAL DOCTRINE")
    lines.append("=" * 70)
    lines.append("")

    for area in areas:
        lines.append(f"{area.name}")
        lines.append("-" * len(area.name))

        # Show definition (first paragraph only)
        if area.definition:
            paragraphs = area.definition.split("\n\n")
            first_para = paragraphs[0].strip()
            lines.append(first_para)
            lines.append("")

        # Show rules (first line only)
        lines.append("Rules:")
        for rule in area.all_rules:
            lines.append(f"  - {rule.first_line}")
        lines.append("")

    return "\n".join(lines)


def format_doctrine_verbose(areas: list[DoctrineArea]) -> str:
    """Format doctrine with full definitions and categorized rules."""
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

    for area in areas:
        lines.append("-" * 70)
        lines.append(f"{area.name.upper()}")
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
                lines.append(f"    - {rule.first_line}")
            lines.append("")

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================


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
    use_case = get_list_doctrine_areas_use_case()
    response = asyncio.run(use_case.execute(ListDoctrineAreasRequest()))

    if not response.areas:
        click.echo("No doctrine tests found.")
        return

    areas = response.areas
    if area:
        # Filter to specific area
        area_lower = area.lower()
        areas = [a for a in areas if area_lower in a.name.lower()]
        if not areas:
            click.echo(f"No doctrine found for area '{area}'")
            all_areas = [a.name for a in response.areas]
            click.echo(f"Available areas: {', '.join(all_areas)}")
            raise SystemExit(1)

    if verbose:
        click.echo(format_doctrine_verbose(areas))
    else:
        click.echo(format_doctrine_brief(areas))


@doctrine_group.command(name="list")
@click.option(
    "--scope",
    type=click.Choice(["core", "apps", "all"]),
    default="all",
    help="Doctrine scope: core (framework), apps (app instance), or all",
)
def list_doctrine_areas(scope: str) -> None:
    """List available doctrine areas.

    Scope controls which doctrine is shown:
    - core: Framework doctrine (src/julee/core/doctrine/)
    - apps: App instance doctrine (apps/{app}/doctrine/)
    - all: Both core and app doctrine
    """
    total_rules = 0

    # Core doctrine
    if scope in ("core", "all"):
        use_case = get_list_doctrine_areas_use_case()
        response = asyncio.run(use_case.execute(ListDoctrineAreasRequest()))

        if response.areas:
            click.echo("Core Doctrine:")
            click.echo("")
            for area in response.areas:
                click.echo(f"  {area.name}: {area.rule_count} rules")
                total_rules += area.rule_count
            click.echo("")
        else:
            click.echo(f"Core doctrine not found: {DOCTRINE_DIR}", err=True)

    # App instance doctrine
    if scope in ("apps", "all"):
        app_dirs = _discover_app_doctrine_dirs()
        if app_dirs:
            click.echo("App Instance Doctrine:")
            click.echo("")
            for app_slug, doctrine_dir in sorted(app_dirs.items()):
                # Create a repo for this app's doctrine
                from julee.core.infrastructure.repositories.introspection.doctrine import (
                    FilesystemDoctrineRepository,
                )
                from julee.core.use_cases.list_doctrine_rules import (
                    ListDoctrineAreasUseCase,
                )

                repo = FilesystemDoctrineRepository(
                    doctrine_dir=doctrine_dir,
                    entities_dir=doctrine_dir,  # Apps may not have separate entities
                )
                uc = ListDoctrineAreasUseCase(doctrine_repository=repo)
                resp = asyncio.run(uc.execute(None))

                if resp.areas:
                    click.echo(f"  {app_slug}: {resp.total_rules} rules")
                    total_rules += resp.total_rules
            click.echo("")
        elif scope == "apps":
            click.echo("No app instance doctrine found.")

    if total_rules > 0:
        click.echo(f"Total: {total_rules} rules")


@doctrine_group.command(name="verify")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed verification report"
)
@click.option("--area", "-a", help="Filter to specific doctrine area")
@click.option(
    "--scope",
    type=click.Choice(["core", "apps", "all"]),
    default="all",
    help="Doctrine scope: core (framework), apps (app instance), or all",
)
@click.option("--app", "app_filter", help="Filter to specific app (for apps scope)")
@click.option(
    "--target",
    "-t",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="Target directory to verify (default: current project)",
)
def verify_doctrine(
    verbose: bool,
    area: str | None,
    scope: str,
    app_filter: str | None,
    target: str | None,
) -> None:
    """Verify codebase compliance with architectural doctrine.

    Runs doctrine tests and displays results in a structured format.
    The tests ARE the doctrine - this command executes them and
    reports which rules pass or fail.

    Scope controls which doctrine is verified:
    - core: Framework doctrine only
    - apps: App instance doctrine only
    - all: Both (default)

    Use --target to verify an external solution:

        julee-admin doctrine verify --target /path/to/solution
    """
    import os

    from apps.admin.commands.doctrine_plugin import run_doctrine_verification
    from apps.admin.templates import render_doctrine_verify

    # Set JULEE_TARGET environment variable - explicit target or current project
    target_path = target if target else str(find_project_root())
    os.environ["JULEE_TARGET"] = target_path
    click.echo(f"Target: {target_path}\n")

    all_results: dict = {}
    final_exit_code = 0

    # Core doctrine
    if scope in ("core", "all"):
        if DOCTRINE_DIR.exists():
            click.echo("Verifying core doctrine...\n")
            results, exit_code = run_doctrine_verification(DOCTRINE_DIR)
            if results:
                for k, v in results.items():
                    all_results[f"Core: {k}"] = v
            if exit_code != 0:
                final_exit_code = exit_code
        else:
            click.echo(f"Core doctrine not found: {DOCTRINE_DIR}", err=True)

    # App instance doctrine
    if scope in ("apps", "all"):
        app_dirs = _discover_app_doctrine_dirs()
        if app_filter:
            app_dirs = {k: v for k, v in app_dirs.items() if k == app_filter}
            if not app_dirs:
                click.echo(f"App '{app_filter}' has no doctrine directory.")
                if scope == "apps":
                    raise SystemExit(1)

        for app_slug, doctrine_dir in sorted(app_dirs.items()):
            click.echo(f"Verifying {app_slug} app doctrine...\n")
            results, exit_code = run_doctrine_verification(doctrine_dir)
            if results:
                for k, v in results.items():
                    all_results[f"App/{app_slug}: {k}"] = v
            if exit_code != 0:
                final_exit_code = exit_code

    if not all_results:
        click.echo("No doctrine tests found.")
        return

    if area:
        # Filter to specific area
        area_lower = area.lower()
        filtered = {k: v for k, v in all_results.items() if area_lower in k.lower()}
        if not filtered:
            click.echo(f"No doctrine found for area '{area}'")
            click.echo(f"Available areas: {', '.join(all_results.keys())}")
            raise SystemExit(1)
        all_results = filtered

    output = render_doctrine_verify(all_results, verbose=verbose)
    click.echo(output)

    raise SystemExit(final_exit_code)

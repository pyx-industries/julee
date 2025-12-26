"""Solution structure commands.

Commands for inspecting solution structure: the solution itself,
applications, and deployments.
"""

import asyncio

import click

from apps.admin.dependencies import (
    get_application_repository,
    get_deployment_repository,
    get_project_root,
    get_solution_repository,
)


@click.group(name="solution")
def solution_group() -> None:
    """Inspect the solution structure."""
    pass


@solution_group.command(name="show")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def show_solution(verbose: bool) -> None:
    """Show the current solution structure."""
    repo = get_solution_repository()
    solution = asyncio.run(repo.get())

    click.echo(f"Solution: {solution.name}")
    click.echo(f"Path: {solution.path}")
    click.echo()

    # Bounded contexts
    click.echo(f"Bounded Contexts ({len(solution.bounded_contexts)}):")
    for bc in solution.bounded_contexts:
        flags = []
        if bc.is_viewpoint:
            flags.append("viewpoint")
        flag_str = f" ({', '.join(flags)})" if flags else ""
        click.echo(f"  - {bc.slug}{flag_str}")

    # Applications
    click.echo()
    click.echo(f"Applications ({len(solution.applications)}):")
    for app in solution.applications:
        click.echo(f"  - {app.slug} [{app.app_type.value}]")

    # Deployments
    click.echo()
    click.echo(f"Deployments ({len(solution.deployments)}):")
    for dep in solution.deployments:
        click.echo(f"  - {dep.slug} [{dep.deployment_type.value}]")

    # Nested solutions
    if solution.nested_solutions:
        click.echo()
        click.echo(f"Nested Solutions ({len(solution.nested_solutions)}):")
        for nested in solution.nested_solutions:
            click.echo(f"  - {nested.name} ({len(nested.bounded_contexts)} BCs)")

    # Documentation
    if verbose and solution.documentation:
        click.echo()
        click.echo("Documentation:")
        doc = solution.documentation
        click.echo(f"  Path: {doc.path}")
        click.echo(f"  Type: {doc.doc_type.value}")


@click.group(name="apps")
def apps_group() -> None:
    """Inspect applications in the solution."""
    pass


@apps_group.command(name="list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--type", "-t", "app_type", help="Filter by application type")
def list_apps(verbose: bool, app_type: str | None) -> None:
    """List all applications in the solution."""
    repo = get_application_repository()
    applications = asyncio.run(repo.list_all())

    if app_type:
        applications = [a for a in applications if a.app_type.value == app_type]

    if not applications:
        click.echo("No applications found.")
        return

    for app in applications:
        if verbose:
            click.echo(f"{app.slug}:")
            click.echo(f"  Type: {app.app_type.value}")
            click.echo(f"  Path: {app.path}")
            if app.markers:
                markers = []
                if app.markers.has_tests:
                    markers.append("tests")
                if app.markers.has_routers:
                    markers.append("routers")
                if app.markers.has_tools:
                    markers.append("tools")
                if app.markers.has_pipelines:
                    markers.append("pipelines")
                if app.markers.has_commands:
                    markers.append("commands")
                if markers:
                    click.echo(f"  Markers: {', '.join(markers)}")
            click.echo()
        else:
            click.echo(f"{app.slug} [{app.app_type.value}]")


@apps_group.command(name="show")
@click.argument("slug")
def show_app(slug: str) -> None:
    """Show details for a specific application."""
    repo = get_application_repository()
    app = asyncio.run(repo.get(slug))

    if app is None:
        click.echo(f"Application '{slug}' not found.", err=True)
        raise SystemExit(1)

    click.echo(f"Application: {app.slug}")
    click.echo(f"Type: {app.app_type.value}")
    click.echo(f"Path: {app.path}")

    if app.markers:
        click.echo()
        click.echo("Structural Markers:")
        click.echo(f"  Has tests: {app.markers.has_tests}")
        click.echo(f"  Has routers: {app.markers.has_routers}")
        click.echo(f"  Has tools: {app.markers.has_tools}")
        click.echo(f"  Has pipelines: {app.markers.has_pipelines}")
        click.echo(f"  Has activities: {app.markers.has_activities}")
        click.echo(f"  Has commands: {app.markers.has_commands}")
        click.echo(f"  Has directives: {app.markers.has_directives}")
        click.echo(f"  Uses BC organization: {app.markers.uses_bc_organization}")


@click.group(name="deployments")
def deployments_group() -> None:
    """Inspect deployments in the solution."""
    pass


@deployments_group.command(name="list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--type", "-t", "dep_type", help="Filter by deployment type")
def list_deployments(verbose: bool, dep_type: str | None) -> None:
    """List all deployments in the solution."""
    repo = get_deployment_repository()
    deployments = asyncio.run(repo.list_all())

    if dep_type:
        deployments = [d for d in deployments if d.deployment_type.value == dep_type]

    if not deployments:
        click.echo("No deployments found.")
        return

    for dep in deployments:
        if verbose:
            click.echo(f"{dep.slug}:")
            click.echo(f"  Type: {dep.deployment_type.value}")
            click.echo(f"  Path: {dep.path}")
            if dep.application_refs:
                click.echo(f"  App refs: {', '.join(dep.application_refs)}")
            click.echo()
        else:
            click.echo(f"{dep.slug} [{dep.deployment_type.value}]")


@deployments_group.command(name="show")
@click.argument("slug")
def show_deployment(slug: str) -> None:
    """Show details for a specific deployment."""
    repo = get_deployment_repository()
    dep = asyncio.run(repo.get(slug))

    if dep is None:
        click.echo(f"Deployment '{slug}' not found.", err=True)
        raise SystemExit(1)

    click.echo(f"Deployment: {dep.slug}")
    click.echo(f"Type: {dep.deployment_type.value}")
    click.echo(f"Path: {dep.path}")

    if dep.application_refs:
        click.echo()
        click.echo("Application References:")
        for ref in dep.application_refs:
            click.echo(f"  - {ref}")

    if dep.markers:
        click.echo()
        click.echo("Structural Markers:")
        click.echo(f"  Has Docker Compose: {dep.markers.has_docker_compose}")
        click.echo(f"  Has Dockerfiles: {dep.markers.has_dockerfiles}")
        click.echo(f"  Has K8s manifests: {dep.markers.has_manifests}")
        click.echo(f"  Has Helm: {dep.markers.has_helm}")
        click.echo(f"  Has Kustomize: {dep.markers.has_kustomize}")
        click.echo(f"  Has Terraform: {dep.markers.has_terraform}")

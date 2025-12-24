"""Routes commands.

Commands for listing and inspecting configured pipeline routes.
Routes define how responses from one pipeline are routed to downstream pipelines.
"""

import asyncio
import importlib
from typing import Callable

import click

from julee.shared.domain.models.pipeline_route import PipelineRoute
from julee.shared.repositories.memory.pipeline_route import InMemoryPipelineRouteRepository


# Default route modules to load
# Each module should have a get_*_routes() function or a *_routes list
DEFAULT_ROUTE_MODULES = [
    "julee.contrib.polling.apps.worker.routes",
]


def _load_routes_from_module(module_name: str) -> list[PipelineRoute]:
    """Load routes from a module.

    Looks for:
    - Functions named get_*_routes() that return list[PipelineRoute]
    - Variables named *_routes that are list[PipelineRoute]

    Args:
        module_name: Fully qualified module name

    Returns:
        List of routes found in the module
    """
    routes = []
    try:
        module = importlib.import_module(module_name)

        # Look for get_*_routes() functions
        for name in dir(module):
            if name.startswith("get_") and name.endswith("_routes"):
                func = getattr(module, name)
                if callable(func):
                    result = func()
                    if isinstance(result, list):
                        routes.extend(result)

        # Look for *_routes lists
        for name in dir(module):
            if name.endswith("_routes") and not name.startswith("get_"):
                value = getattr(module, name)
                if isinstance(value, list):
                    routes.extend(value)

    except ImportError as e:
        click.echo(f"Warning: Could not load module {module_name}: {e}", err=True)
    except Exception as e:
        click.echo(f"Warning: Error loading routes from {module_name}: {e}", err=True)

    return routes


def _get_route_repository(
    modules: list[str] | None = None,
) -> InMemoryPipelineRouteRepository:
    """Get a route repository populated with routes from configured modules.

    Args:
        modules: List of module names to load routes from.
                 Defaults to DEFAULT_ROUTE_MODULES.

    Returns:
        InMemoryPipelineRouteRepository with loaded routes
    """
    modules = modules or DEFAULT_ROUTE_MODULES
    all_routes = []

    for module_name in modules:
        routes = _load_routes_from_module(module_name)
        all_routes.extend(routes)

    return InMemoryPipelineRouteRepository(all_routes)


@click.group(name="routes")
def routes_group() -> None:
    """Pipeline routing configuration.

    Commands for inspecting how responses are routed to downstream pipelines.
    """
    pass


@routes_group.command(name="list")
@click.option(
    "--response-type", "-r",
    help="Filter routes by response type (partial match supported)",
)
@click.option(
    "--module", "-m",
    multiple=True,
    help="Additional module to load routes from (can be used multiple times)",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed route information",
)
def list_routes(
    response_type: str | None,
    module: tuple[str, ...],
    verbose: bool,
) -> None:
    """List configured pipeline routes.

    Shows all routes that define how responses are routed to downstream pipelines.
    """
    # Build module list
    modules = list(DEFAULT_ROUTE_MODULES)
    if module:
        modules.extend(module)

    repo = _get_route_repository(modules)
    routes = asyncio.run(repo.list_all())

    if not routes:
        click.echo("No routes configured.")
        click.echo()
        click.echo("Routes are loaded from these modules:")
        for m in modules:
            click.echo(f"  - {m}")
        return

    # Filter by response type if specified
    if response_type:
        routes = [
            r for r in routes
            if response_type.lower() in r.response_type.lower()
        ]
        if not routes:
            click.echo(f"No routes found for response type matching '{response_type}'")
            return

    # Display routes
    for route in routes:
        if verbose:
            _print_route_detail(route)
            click.echo()
        else:
            response_name = route.response_type.split(".")[-1]
            pipeline_name = route.pipeline.split(".")[-1]
            click.echo(f"{response_name} -> {pipeline_name}")
            click.echo(f"  condition: {route.condition}")
            if route.description:
                click.echo(f"  desc: {route.description}")

    click.echo()
    click.echo(f"Total: {len(routes)} route(s)")


@routes_group.command(name="show")
@click.argument("response_type")
@click.option(
    "--module", "-m",
    multiple=True,
    help="Additional module to load routes from",
)
def show_routes(response_type: str, module: tuple[str, ...]) -> None:
    """Show routes for a specific response type.

    RESPONSE_TYPE can be a full qualified name or just the class name.
    """
    modules = list(DEFAULT_ROUTE_MODULES)
    if module:
        modules.extend(module)

    repo = _get_route_repository(modules)
    routes = asyncio.run(repo.list_for_response_type(response_type))

    # Also try partial match if exact match finds nothing
    if not routes:
        all_routes = asyncio.run(repo.list_all())
        routes = [
            r for r in all_routes
            if response_type.lower() in r.response_type.lower()
        ]

    if not routes:
        click.echo(f"No routes found for response type '{response_type}'", err=True)
        raise SystemExit(1)

    click.echo(f"Routes for {response_type}:")
    click.echo()

    for route in routes:
        _print_route_detail(route)
        click.echo()


def _print_route_detail(route: PipelineRoute) -> None:
    """Print detailed information about a route."""
    click.echo(f"Response Type: {route.response_type}")
    click.echo(f"Condition:     {route.condition}")
    click.echo(f"Pipeline:      {route.pipeline}")
    click.echo(f"Request Type:  {route.request_type}")
    if route.description:
        click.echo(f"Description:   {route.description}")

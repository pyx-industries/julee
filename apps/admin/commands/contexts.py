"""Bounded context commands.

Commands for listing and inspecting bounded contexts in a Julee solution.
"""

import asyncio
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

from apps.admin.dependencies import (
    get_get_bounded_context_use_case,
    get_list_bounded_contexts_use_case,
)
from julee.core.entities import BoundedContext
from julee.core.use_cases import (
    GetBoundedContextRequest,
    ListBoundedContextsRequest,
)

# Template environment
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True)


def render_context_details(ctx: BoundedContext) -> str:
    """Render bounded context details using Jinja template.

    Args:
        ctx: The bounded context to render

    Returns:
        Formatted string representation
    """
    template = _env.get_template("context_details.txt.j2")
    return template.render(ctx=ctx)


@click.group(name="contexts")
def contexts_group() -> None:
    """Manage bounded contexts."""
    pass


@contexts_group.command(name="list")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information for each context"
)
def list_contexts(verbose: bool) -> None:
    """List all bounded contexts in the solution."""
    use_case = get_list_bounded_contexts_use_case()
    request = ListBoundedContextsRequest()
    response = asyncio.run(use_case.execute(request))

    if not response.bounded_contexts:
        click.echo("No bounded contexts found.")
        return

    for ctx in response.bounded_contexts:
        if verbose:
            click.echo(render_context_details(ctx))
            click.echo()
        else:
            flags = []
            if ctx.is_viewpoint:
                flags.append("viewpoint")
            if ctx.is_contrib:
                flags.append("contrib")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            click.echo(f"{ctx.slug}{flag_str}")


@contexts_group.command(name="show")
@click.argument("slug")
def show_context(slug: str) -> None:
    """Show details for a specific bounded context."""
    use_case = get_get_bounded_context_use_case()
    request = GetBoundedContextRequest(slug=slug)
    response = asyncio.run(use_case.execute(request))

    if response.bounded_context is None:
        click.echo(f"Bounded context '{slug}' not found.", err=True)
        raise SystemExit(1)

    click.echo(render_context_details(response.bounded_context))

"""Julee Admin CLI.

Main entry point for the julee-admin command-line interface.
"""

import click

from apps.admin.commands.artifacts import (
    entities_group,
    repositories_group,
    requests_group,
    responses_group,
    services_group,
    use_cases_group,
)
from apps.admin.commands.contexts import contexts_group
from apps.admin.commands.doctrine import doctrine_group
from apps.admin.commands.routes import routes_group


@click.group()
@click.version_option(package_name="julee")
def cli() -> None:
    """Julee administration CLI.

    Tools for managing and introspecting Julee solutions.
    """
    pass


# Register command groups
cli.add_command(contexts_group)
cli.add_command(entities_group)
cli.add_command(use_cases_group)
cli.add_command(repositories_group)
cli.add_command(services_group)
cli.add_command(requests_group)
cli.add_command(responses_group)
cli.add_command(routes_group)
cli.add_command(doctrine_group)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

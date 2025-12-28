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
from apps.admin.commands.hcd import (
    accelerators_group,
    epics_group,
    hcd_apps_group,
    integrations_group,
    journeys_group,
    personas_group,
    stories_group,
)
from apps.admin.commands.policy import policy_group
from apps.admin.commands.routes import routes_group
from apps.admin.commands.solution import (
    apps_group,
    deployments_group,
    solution_group,
)


@click.group()
@click.version_option(package_name="julee")
def cli() -> None:
    """Julee administration CLI.

    Tools for managing and introspecting Julee solutions.
    """
    pass


# Register command groups
cli.add_command(solution_group)
cli.add_command(apps_group)
cli.add_command(deployments_group)
cli.add_command(contexts_group)
cli.add_command(entities_group)
cli.add_command(use_cases_group)
cli.add_command(repositories_group)
cli.add_command(services_group)
cli.add_command(requests_group)
cli.add_command(responses_group)
cli.add_command(routes_group)
cli.add_command(doctrine_group)
cli.add_command(policy_group)

# HCD command groups (RST-backed entities)
cli.add_command(personas_group)
cli.add_command(journeys_group)
cli.add_command(epics_group)
cli.add_command(stories_group)
cli.add_command(hcd_apps_group)
cli.add_command(accelerators_group)
cli.add_command(integrations_group)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

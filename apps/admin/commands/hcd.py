"""Human-Centred Design commands.

Commands for listing and inspecting HCD entities (personas, journeys, epics,
stories, apps, accelerators, integrations) defined in RST documentation.
"""

from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

from apps.admin.dependencies import (
    get_get_accelerator_use_case,
    get_get_app_use_case,
    get_get_epic_use_case,
    get_get_integration_use_case,
    get_get_journey_use_case,
    get_get_persona_use_case,
    get_get_story_use_case,
    get_list_accelerators_use_case,
    get_list_apps_use_case,
    get_list_epics_use_case,
    get_list_integrations_use_case,
    get_list_journeys_use_case,
    get_list_personas_use_case,
    get_list_stories_use_case,
)
from julee.hcd.use_cases.crud import (
    GetAppRequest,
    GetEpicRequest,
    GetIntegrationRequest,
    GetJourneyRequest,
    GetPersonaRequest,
    GetStoryRequest,
    ListAppsRequest,
    ListEpicsRequest,
    ListIntegrationsRequest,
    ListJourneysRequest,
    ListPersonasRequest,
    ListStoriesRequest,
)
from julee.supply_chain.use_cases.crud import (
    GetAcceleratorRequest,
    ListAcceleratorsRequest,
)

# Template environment
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True)


# =============================================================================
# Personas
# =============================================================================


@click.group(name="personas")
def personas_group() -> None:
    """Manage personas."""
    pass


@personas_group.command(name="list")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information for each persona"
)
def list_personas(verbose: bool) -> None:
    """List all personas defined in documentation."""
    use_case = get_list_personas_use_case()
    request = ListPersonasRequest()
    response = use_case.execute_sync(request)

    if not response.entities:
        click.echo("No personas found.")
        return

    for persona in response.entities:
        if verbose:
            template = _env.get_template("persona_details.txt.j2")
            click.echo(template.render(p=persona))
            click.echo()
        else:
            click.echo(f"{persona.slug}: {persona.name}")


@personas_group.command(name="show")
@click.argument("slug")
def show_persona(slug: str) -> None:
    """Show details for a specific persona."""
    use_case = get_get_persona_use_case()
    request = GetPersonaRequest(slug=slug)
    response = use_case.execute_sync(request)

    if response.entity is None:
        click.echo(f"Persona '{slug}' not found.", err=True)
        raise SystemExit(1)

    template = _env.get_template("persona_details.txt.j2")
    click.echo(template.render(p=response.entity))


# =============================================================================
# Journeys
# =============================================================================


@click.group(name="journeys")
def journeys_group() -> None:
    """Manage journeys."""
    pass


@journeys_group.command(name="list")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information for each journey"
)
def list_journeys(verbose: bool) -> None:
    """List all journeys defined in documentation."""
    use_case = get_list_journeys_use_case()
    request = ListJourneysRequest()
    response = use_case.execute_sync(request)

    if not response.entities:
        click.echo("No journeys found.")
        return

    for journey in response.entities:
        if verbose:
            template = _env.get_template("journey_details.txt.j2")
            click.echo(template.render(j=journey))
            click.echo()
        else:
            step_count = len(journey.steps) if journey.steps else 0
            click.echo(f"{journey.slug}: {journey.display_title} ({step_count} steps)")


@journeys_group.command(name="show")
@click.argument("slug")
def show_journey(slug: str) -> None:
    """Show details for a specific journey."""
    use_case = get_get_journey_use_case()
    request = GetJourneyRequest(slug=slug)
    response = use_case.execute_sync(request)

    if response.entity is None:
        click.echo(f"Journey '{slug}' not found.", err=True)
        raise SystemExit(1)

    template = _env.get_template("journey_details.txt.j2")
    click.echo(template.render(j=response.entity))


# =============================================================================
# Epics
# =============================================================================


@click.group(name="epics")
def epics_group() -> None:
    """Manage epics."""
    pass


@epics_group.command(name="list")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information for each epic"
)
def list_epics(verbose: bool) -> None:
    """List all epics defined in documentation."""
    use_case = get_list_epics_use_case()
    request = ListEpicsRequest()
    response = use_case.execute_sync(request)

    if not response.entities:
        click.echo("No epics found.")
        return

    for epic in response.entities:
        if verbose:
            template = _env.get_template("epic_details.txt.j2")
            click.echo(template.render(e=epic))
            click.echo()
        else:
            story_count = len(epic.story_refs) if epic.story_refs else 0
            click.echo(f"{epic.slug}: {epic.display_title} ({story_count} stories)")


@epics_group.command(name="show")
@click.argument("slug")
def show_epic(slug: str) -> None:
    """Show details for a specific epic."""
    use_case = get_get_epic_use_case()
    request = GetEpicRequest(slug=slug)
    response = use_case.execute_sync(request)

    if response.entity is None:
        click.echo(f"Epic '{slug}' not found.", err=True)
        raise SystemExit(1)

    template = _env.get_template("epic_details.txt.j2")
    click.echo(template.render(e=response.entity))


# =============================================================================
# Stories
# =============================================================================


@click.group(name="stories")
def stories_group() -> None:
    """Manage stories."""
    pass


@stories_group.command(name="list")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information for each story"
)
@click.option("--app", "app_slug", help="Filter by app slug")
@click.option("--persona", help="Filter by persona")
def list_stories(verbose: bool, app_slug: str | None, persona: str | None) -> None:
    """List all stories defined in documentation."""
    use_case = get_list_stories_use_case()
    request = ListStoriesRequest(app_slug=app_slug, persona=persona)
    response = use_case.execute_sync(request)

    if not response.entities:
        click.echo("No stories found.")
        return

    for story in response.entities:
        if verbose:
            template = _env.get_template("story_details.txt.j2")
            click.echo(template.render(s=story))
            click.echo()
        else:
            persona_str = f" [{story.persona}]" if story.persona else ""
            click.echo(f"{story.slug}: {story.name}{persona_str}")


@stories_group.command(name="show")
@click.argument("slug")
def show_story(slug: str) -> None:
    """Show details for a specific story."""
    use_case = get_get_story_use_case()
    request = GetStoryRequest(slug=slug)
    response = use_case.execute_sync(request)

    if response.entity is None:
        click.echo(f"Story '{slug}' not found.", err=True)
        raise SystemExit(1)

    template = _env.get_template("story_details.txt.j2")
    click.echo(template.render(s=response.entity))


# =============================================================================
# Apps (HCD - from documentation)
# =============================================================================


@click.group(name="hcd-apps")
def hcd_apps_group() -> None:
    """Manage apps defined in HCD documentation."""
    pass


@hcd_apps_group.command(name="list")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information for each app"
)
@click.option("--type", "app_type", help="Filter by app type")
def list_hcd_apps(verbose: bool, app_type: str | None) -> None:
    """List all apps defined in documentation."""
    use_case = get_list_apps_use_case()
    request = ListAppsRequest(app_type=app_type)
    response = use_case.execute_sync(request)

    if not response.entities:
        click.echo("No apps found.")
        return

    for app in response.entities:
        if verbose:
            template = _env.get_template("app_details.txt.j2")
            click.echo(template.render(a=app))
            click.echo()
        else:
            type_str = f" [{app.app_type.value}]" if app.app_type else ""
            click.echo(f"{app.slug}: {app.name}{type_str}")


@hcd_apps_group.command(name="show")
@click.argument("slug")
def show_hcd_app(slug: str) -> None:
    """Show details for a specific app."""
    use_case = get_get_app_use_case()
    request = GetAppRequest(slug=slug)
    response = use_case.execute_sync(request)

    if response.entity is None:
        click.echo(f"App '{slug}' not found.", err=True)
        raise SystemExit(1)

    template = _env.get_template("app_details.txt.j2")
    click.echo(template.render(a=response.entity))


# =============================================================================
# Accelerators
# =============================================================================


@click.group(name="accelerators")
def accelerators_group() -> None:
    """Manage accelerators."""
    pass


@accelerators_group.command(name="list")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information for each accelerator",
)
@click.option("--status", help="Filter by status")
def list_accelerators(verbose: bool, status: str | None) -> None:
    """List all accelerators defined in documentation."""
    use_case = get_list_accelerators_use_case()
    request = ListAcceleratorsRequest(status=status)
    response = use_case.execute_sync(request)

    if not response.entities:
        click.echo("No accelerators found.")
        return

    for acc in response.entities:
        if verbose:
            template = _env.get_template("accelerator_details.txt.j2")
            click.echo(template.render(a=acc))
            click.echo()
        else:
            status_str = f" [{acc.status}]" if acc.status else ""
            click.echo(f"{acc.slug}: {acc.name}{status_str}")


@accelerators_group.command(name="show")
@click.argument("slug")
def show_accelerator(slug: str) -> None:
    """Show details for a specific accelerator."""
    use_case = get_get_accelerator_use_case()
    request = GetAcceleratorRequest(slug=slug)
    response = use_case.execute_sync(request)

    if response.entity is None:
        click.echo(f"Accelerator '{slug}' not found.", err=True)
        raise SystemExit(1)

    template = _env.get_template("accelerator_details.txt.j2")
    click.echo(template.render(a=response.entity))


# =============================================================================
# Integrations
# =============================================================================


@click.group(name="integrations")
def integrations_group() -> None:
    """Manage integrations."""
    pass


@integrations_group.command(name="list")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information for each integration",
)
def list_integrations(verbose: bool) -> None:
    """List all integrations defined in documentation."""
    use_case = get_list_integrations_use_case()
    request = ListIntegrationsRequest()
    response = use_case.execute_sync(request)

    if not response.entities:
        click.echo("No integrations found.")
        return

    for integration in response.entities:
        if verbose:
            template = _env.get_template("integration_details.txt.j2")
            click.echo(template.render(i=integration))
            click.echo()
        else:
            type_str = f" [{integration.system_type}]" if integration.system_type else ""
            click.echo(f"{integration.slug}: {integration.name}{type_str}")


@integrations_group.command(name="show")
@click.argument("slug")
def show_integration(slug: str) -> None:
    """Show details for a specific integration."""
    use_case = get_get_integration_use_case()
    request = GetIntegrationRequest(slug=slug)
    response = use_case.execute_sync(request)

    if response.entity is None:
        click.echo(f"Integration '{slug}' not found.", err=True)
        raise SystemExit(1)

    template = _env.get_template("integration_details.txt.j2")
    click.echo(template.render(i=response.entity))

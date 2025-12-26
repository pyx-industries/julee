"""Code artifact commands.

Commands for listing and inspecting code artifacts (entities, use cases,
repository protocols, service protocols, requests, responses) in a Julee solution.
"""

from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

from apps.admin.dependencies import (
    get_list_entities_use_case,
    get_list_repository_protocols_use_case,
    get_list_requests_use_case,
    get_list_responses_use_case,
    get_list_service_protocols_use_case,
    get_list_use_cases_use_case,
)
from julee.core.use_cases.code_artifact.uc_interfaces import (
    CodeArtifactWithContext,
    ListCodeArtifactsRequest,
)

# Template environment
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True)


def render_class_details(artifact: CodeArtifactWithContext) -> str:
    """Render class details using Jinja template.

    Args:
        artifact: The artifact with its bounded context

    Returns:
        Formatted string representation
    """
    template = _env.get_template("class_details.txt.j2")
    return template.render(artifact=artifact)


def _list_artifacts(
    use_case_factory,
    context: str | None,
    verbose: bool,
    artifact_type: str,
) -> None:
    """Generic artifact listing logic."""
    use_case = use_case_factory()
    request = ListCodeArtifactsRequest(bounded_context=context)
    response = use_case.execute_sync(request)

    if not response.artifacts:
        click.echo(f"No {artifact_type} found.")
        return

    for item in response.artifacts:
        if verbose:
            click.echo(render_class_details(item))
            click.echo()
        else:
            docstring = f" - {item.artifact.docstring}" if item.artifact.docstring else ""
            click.echo(f"{item.bounded_context}.{item.artifact.name}{docstring}")


def _show_artifact(
    use_case_factory,
    name: str,
    context: str | None,
    artifact_type: str,
) -> None:
    """Generic artifact show logic."""
    use_case = use_case_factory()
    request = ListCodeArtifactsRequest(bounded_context=context)
    response = use_case.execute_sync(request)

    # Find matching artifact(s)
    matches = [a for a in response.artifacts if a.artifact.name == name]

    if not matches:
        click.echo(f"{artifact_type.title()} '{name}' not found.", err=True)
        raise SystemExit(1)

    if len(matches) > 1 and not context:
        click.echo(f"Multiple {artifact_type} named '{name}' found. Use --context to narrow:")
        for m in matches:
            click.echo(f"  {m.bounded_context}.{m.artifact.name}")
        raise SystemExit(1)

    click.echo(render_class_details(matches[0]))


# =============================================================================
# Entities Commands
# =============================================================================


@click.group(name="entities")
def entities_group() -> None:
    """Manage domain entities."""
    pass


@entities_group.command(name="list")
@click.option("--context", "-c", help="Filter to specific bounded context")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_entities(context: str | None, verbose: bool) -> None:
    """List all domain entities."""
    _list_artifacts(get_list_entities_use_case, context, verbose, "entities")


@entities_group.command(name="show")
@click.argument("name")
@click.option("--context", "-c", help="Bounded context to search in")
def show_entity(name: str, context: str | None) -> None:
    """Show details for a specific entity."""
    _show_artifact(get_list_entities_use_case, name, context, "entity")


# =============================================================================
# Use Cases Commands
# =============================================================================


def _derive_contract_names(use_case_name: str) -> tuple[str | None, str | None]:
    """Derive request/response names from use case name by convention.

    Convention: {Action}{Entity}UseCase -> {Action}{Entity}Request / {Action}{Entity}Response

    Args:
        use_case_name: The use case class name

    Returns:
        Tuple of (request_name, response_name) or (None, None) if can't derive
    """
    if not use_case_name.endswith("UseCase"):
        return None, None

    prefix = use_case_name[:-7]  # Strip "UseCase"
    return f"{prefix}Request", f"{prefix}Response"


def _find_artifact_by_name(
    artifacts: list[CodeArtifactWithContext],
    name: str,
    context: str | None = None,
) -> CodeArtifactWithContext | None:
    """Find an artifact by name, optionally filtering by context."""
    for artifact in artifacts:
        if artifact.artifact.name == name:
            if context is None or artifact.bounded_context == context:
                return artifact
    return None


def render_use_case_details(
    artifact: CodeArtifactWithContext,
    request: CodeArtifactWithContext | None,
    response: CodeArtifactWithContext | None,
) -> str:
    """Render use case details with contract info using Jinja template.

    Args:
        artifact: The use case artifact
        request: The associated request DTO (if found)
        response: The associated response DTO (if found)

    Returns:
        Formatted string representation
    """
    template = _env.get_template("use_case_details.txt.j2")
    return template.render(artifact=artifact, request=request, response=response)


@click.group(name="use-cases")
def use_cases_group() -> None:
    """Manage use cases."""
    pass


@use_cases_group.command(name="list")
@click.option("--context", "-c", help="Filter to specific bounded context")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_use_cases(context: str | None, verbose: bool) -> None:
    """List all use cases."""
    _list_artifacts(get_list_use_cases_use_case, context, verbose, "use cases")


@use_cases_group.command(name="show")
@click.argument("name")
@click.option("--context", "-c", help="Bounded context to search in")
def show_use_case(name: str, context: str | None) -> None:
    """Show details for a specific use case with contract info."""
    # Get use case
    use_case = get_list_use_cases_use_case()
    request = ListCodeArtifactsRequest(bounded_context=context)
    response = use_case.execute_sync(request)

    matches = [a for a in response.artifacts if a.artifact.name == name]

    if not matches:
        click.echo(f"Use case '{name}' not found.", err=True)
        raise SystemExit(1)

    if len(matches) > 1 and not context:
        click.echo(f"Multiple use cases named '{name}' found. Use --context to narrow:")
        for m in matches:
            click.echo(f"  {m.bounded_context}.{m.artifact.name}")
        raise SystemExit(1)

    use_case_artifact = matches[0]

    # Derive and look up request/response by naming convention
    req_name, resp_name = _derive_contract_names(name)
    req_artifact = None
    resp_artifact = None

    if req_name:
        # Look up request in the same context
        req_use_case = get_list_requests_use_case()
        req_request = ListCodeArtifactsRequest(bounded_context=use_case_artifact.bounded_context)
        req_response = req_use_case.execute_sync(req_request)
        req_artifact = _find_artifact_by_name(
            req_response.artifacts, req_name, use_case_artifact.bounded_context
        )

    if resp_name:
        # Look up response in the same context
        resp_use_case = get_list_responses_use_case()
        resp_request = ListCodeArtifactsRequest(bounded_context=use_case_artifact.bounded_context)
        resp_response = resp_use_case.execute_sync(resp_request)
        resp_artifact = _find_artifact_by_name(
            resp_response.artifacts, resp_name, use_case_artifact.bounded_context
        )

    click.echo(render_use_case_details(use_case_artifact, req_artifact, resp_artifact))


# =============================================================================
# Repository Protocol Commands
# =============================================================================


@click.group(name="repositories")
def repositories_group() -> None:
    """Manage repository protocols."""
    pass


@repositories_group.command(name="list")
@click.option("--context", "-c", help="Filter to specific bounded context")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_repositories(context: str | None, verbose: bool) -> None:
    """List all repository protocols."""
    _list_artifacts(get_list_repository_protocols_use_case, context, verbose, "repository protocols")


@repositories_group.command(name="show")
@click.argument("name")
@click.option("--context", "-c", help="Bounded context to search in")
def show_repository(name: str, context: str | None) -> None:
    """Show details for a specific repository protocol."""
    _show_artifact(get_list_repository_protocols_use_case, name, context, "repository protocol")


# =============================================================================
# Service Protocol Commands
# =============================================================================


@click.group(name="services")
def services_group() -> None:
    """Manage service protocols."""
    pass


@services_group.command(name="list")
@click.option("--context", "-c", help="Filter to specific bounded context")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_services(context: str | None, verbose: bool) -> None:
    """List all service protocols."""
    _list_artifacts(get_list_service_protocols_use_case, context, verbose, "service protocols")


@services_group.command(name="show")
@click.argument("name")
@click.option("--context", "-c", help="Bounded context to search in")
def show_service(name: str, context: str | None) -> None:
    """Show details for a specific service protocol."""
    _show_artifact(get_list_service_protocols_use_case, name, context, "service protocol")


# =============================================================================
# Request DTO Commands
# =============================================================================


@click.group(name="requests")
def requests_group() -> None:
    """Manage request DTOs."""
    pass


@requests_group.command(name="list")
@click.option("--context", "-c", help="Filter to specific bounded context")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_requests(context: str | None, verbose: bool) -> None:
    """List all request DTOs."""
    _list_artifacts(get_list_requests_use_case, context, verbose, "requests")


@requests_group.command(name="show")
@click.argument("name")
@click.option("--context", "-c", help="Bounded context to search in")
def show_request(name: str, context: str | None) -> None:
    """Show details for a specific request DTO."""
    _show_artifact(get_list_requests_use_case, name, context, "request")


# =============================================================================
# Response DTO Commands
# =============================================================================


@click.group(name="responses")
def responses_group() -> None:
    """Manage response DTOs."""
    pass


@responses_group.command(name="list")
@click.option("--context", "-c", help="Filter to specific bounded context")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_responses(context: str | None, verbose: bool) -> None:
    """List all response DTOs."""
    _list_artifacts(get_list_responses_use_case, context, verbose, "responses")


@responses_group.command(name="show")
@click.argument("name")
@click.option("--context", "-c", help="Bounded context to search in")
def show_response(name: str, context: str | None) -> None:
    """Show details for a specific response DTO."""
    _show_artifact(get_list_responses_use_case, name, context, "response")

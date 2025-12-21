"""HCD MCP Server.

FastMCP server for managing HCD domain objects via Model Context Protocol.
"""

from fastmcp import FastMCP

from ..mcp_shared import (
    create_annotation,
    delete_annotation,
    read_only_annotation,
    update_annotation,
)
from .tools import (
    # Accelerators
    create_accelerator,
    # Apps
    create_app,
    # Epics
    create_epic,
    # Integrations
    create_integration,
    # Journeys
    create_journey,
    # Stories
    create_story,
    delete_accelerator,
    delete_app,
    delete_epic,
    delete_integration,
    delete_journey,
    delete_story,
    get_accelerator,
    get_app,
    get_epic,
    get_integration,
    get_journey,
    # Personas (read-only)
    get_persona,
    get_story,
    list_accelerators,
    list_apps,
    list_epics,
    list_integrations,
    list_journeys,
    list_personas,
    list_stories,
    update_accelerator,
    update_app,
    update_epic,
    update_integration,
    update_journey,
    update_story,
)

# Create the FastMCP server
mcp = FastMCP(
    "HCD Domain Server",
    instructions="MCP server for Human-Centered Design domain objects",
)


# ============================================================================
# Story tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create User Story"))
async def mcp_create_story(
    feature_title: str,
    persona: str,
    app_slug: str,
    i_want: str = "do something",
    so_that: str = "achieve a goal",
) -> dict:
    """Create a user story: 'As a <persona>, I want <action> so that <benefit>'.

    Stories are the atomic unit of user requirements in Human-Centered Design.
    They capture WHO needs something (persona), WHAT they need (i_want), and
    WHY they need it (so_that). Stories belong to apps and can be grouped into epics.

    The persona field automatically creates/references a derived Persona entity.
    Use list_personas() to see all personas derived from existing stories.

    Args:
        feature_title: Descriptive title (e.g., "Login with SSO", "Export Report")
        persona: Who needs this (e.g., "Staff Member", "External User", "Admin")
        app_slug: Which app this story belongs to (must exist - use list_apps())
        i_want: The action/capability needed (e.g., "log in using my company credentials")
        so_that: The benefit/value (e.g., "I don't need to remember another password")
    """
    return await create_story(
        feature_title=feature_title,
        persona=persona,
        app_slug=app_slug,
        i_want=i_want,
        so_that=so_that,
    )


@mcp.tool(annotations=read_only_annotation("Get Story"))
async def mcp_get_story(slug: str, format: str = "full") -> dict | None:
    """Get a story by its slug identifier.

    Args:
        slug: Story identifier (e.g., "login-with-sso-staff-member")
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await get_story(slug, format=format)


@mcp.tool(annotations=read_only_annotation("List Stories"))
async def mcp_list_stories(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all user stories in the HCD model.

    Use this to get an overview of requirements or find stories to add to epics.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await list_stories(limit=limit, offset=offset, format=format)


@mcp.tool(annotations=update_annotation("Update Story"))
async def mcp_update_story(
    slug: str,
    feature_title: str | None = None,
    persona: str | None = None,
    i_want: str | None = None,
    so_that: str | None = None,
) -> dict | None:
    """Update an existing story. Only provided fields are changed.

    Args:
        slug: Story identifier to update
        feature_title: New title (optional)
        persona: New persona - changes who the story is for (optional)
        i_want: New action/capability (optional)
        so_that: New benefit/value (optional)
    """
    return await update_story(
        slug=slug,
        feature_title=feature_title,
        persona=persona,
        i_want=i_want,
        so_that=so_that,
    )


@mcp.tool(annotations=delete_annotation("Delete Story"))
async def mcp_delete_story(slug: str) -> dict:
    """Delete a story by slug.

    Warning: This may leave epics with broken story references.

    Args:
        slug: Story identifier to delete
    """
    return await delete_story(slug)


# ============================================================================
# Epic tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Epic"))
async def mcp_create_epic(
    slug: str,
    description: str = "",
    story_refs: list[str] | None = None,
) -> dict:
    """Create an epic - a collection of related user stories.

    Epics group stories that together deliver a larger capability or feature set.
    For example, an "Authentication" epic might include stories for login, logout,
    password reset, and SSO integration.

    Args:
        slug: Unique identifier (e.g., "authentication", "reporting-dashboard")
        description: What this epic delivers and why it matters
        story_refs: List of story slugs to include (use list_stories() to find them)
    """
    return await create_epic(slug=slug, description=description, story_refs=story_refs)


@mcp.tool(annotations=read_only_annotation("Get Epic"))
async def mcp_get_epic(slug: str, format: str = "full") -> dict | None:
    """Get an epic by slug with its story references.

    Args:
        slug: Epic identifier
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await get_epic(slug, format=format)


@mcp.tool(annotations=read_only_annotation("List Epics"))
async def mcp_list_epics(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all epics in the HCD model.

    Use this to see how stories are organized or find epics to add stories to.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await list_epics(limit=limit, offset=offset, format=format)


@mcp.tool(annotations=update_annotation("Update Epic"))
async def mcp_update_epic(
    slug: str,
    description: str | None = None,
    story_refs: list[str] | None = None,
) -> dict | None:
    """Update an epic. Only provided fields are changed.

    Note: story_refs replaces the entire list if provided. To add a story,
    first get the epic, then update with the combined list.

    Args:
        slug: Epic identifier to update
        description: New description (optional)
        story_refs: New list of story slugs - replaces existing (optional)
    """
    return await update_epic(slug=slug, description=description, story_refs=story_refs)


@mcp.tool(annotations=delete_annotation("Delete Epic"))
async def mcp_delete_epic(slug: str) -> dict:
    """Delete an epic by slug.

    Stories referenced by this epic are NOT deleted - they become orphaned
    (not in any epic).

    Args:
        slug: Epic identifier to delete
    """
    return await delete_epic(slug)


# ============================================================================
# Journey tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Journey"))
async def mcp_create_journey(
    slug: str,
    persona: str,
    intent: str = "",
    outcome: str = "",
    goal: str = "",
    depends_on: list[str] | None = None,
) -> dict:
    """Create a journey - how a persona accomplishes a goal through a sequence of steps.

    Journeys are user journey maps that describe the end-to-end experience of a persona
    achieving a specific outcome. Each journey has steps that reference stories or
    other journeys (sub-journeys).

    Example: A "First-Time Login" journey for "New Employee" might include steps:
    1. Receive welcome email (story)
    2. Set up MFA (sub-journey)
    3. Access dashboard (story)

    Args:
        slug: Unique identifier (e.g., "first-time-login", "quarterly-reporting")
        persona: Who takes this journey (should match personas in stories)
        intent: What the persona wants to achieve (motivation)
        outcome: What success looks like (business value delivered)
        goal: Brief description of the activity
        depends_on: Journey slugs that must complete first (prerequisites)
    """
    return await create_journey(
        slug=slug,
        persona=persona,
        intent=intent,
        outcome=outcome,
        goal=goal,
        depends_on=depends_on,
    )


@mcp.tool(annotations=read_only_annotation("Get Journey"))
async def mcp_get_journey(slug: str, format: str = "full") -> dict | None:
    """Get a journey by slug with its steps and dependencies.

    Args:
        slug: Journey identifier
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await get_journey(slug, format=format)


@mcp.tool(annotations=read_only_annotation("List Journeys"))
async def mcp_list_journeys(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all journeys in the HCD model.

    Use this to see user flows or find personas that need journey definitions.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await list_journeys(limit=limit, offset=offset, format=format)


@mcp.tool(annotations=update_annotation("Update Journey"))
async def mcp_update_journey(
    slug: str,
    persona: str | None = None,
    intent: str | None = None,
    outcome: str | None = None,
    goal: str | None = None,
    depends_on: list[str] | None = None,
) -> dict | None:
    """Update a journey. Only provided fields are changed.

    Note: To update steps, use the steps parameter (list of step dicts with
    'step_type' and 'ref' keys). step_type is 'story' or 'journey'.

    Args:
        slug: Journey identifier to update
        persona: New persona (optional)
        intent: New intent/motivation (optional)
        outcome: New success criteria (optional)
        goal: New activity description (optional)
        depends_on: New prerequisite journeys (optional)
    """
    return await update_journey(
        slug=slug,
        persona=persona,
        intent=intent,
        outcome=outcome,
        goal=goal,
        depends_on=depends_on,
    )


@mcp.tool(annotations=delete_annotation("Delete Journey"))
async def mcp_delete_journey(slug: str) -> dict:
    """Delete a journey by slug.

    Warning: Other journeys may depend on this one or reference it as a sub-journey.

    Args:
        slug: Journey identifier to delete
    """
    return await delete_journey(slug)


# ============================================================================
# Persona tools (read-only)
# ============================================================================


@mcp.tool(annotations=read_only_annotation("List Personas"))
async def mcp_list_personas(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all personas - derived automatically from stories and epics.

    Personas are NOT created directly. They are derived from the 'persona' field
    in stories. This provides a unified view of all user types in the HCD model.

    Each persona shows:
    - Which apps they interact with (from their stories)
    - Which epics they participate in
    - Their normalized name for consistent matching

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await list_personas(limit=limit, offset=offset, format=format)


@mcp.tool(annotations=read_only_annotation("Get Persona"))
async def mcp_get_persona(name: str, format: str = "full") -> dict | None:
    """Get a persona by name (case-insensitive).

    Personas are derived from stories - you cannot create them directly.
    To add a new persona, create stories with that persona name.

    Args:
        name: Persona name (e.g., "Staff Member", "Admin") - case-insensitive
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await get_persona(name, format=format)


# ============================================================================
# Accelerator tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Accelerator"))
async def mcp_create_accelerator(
    slug: str,
    status: str = "",
    milestone: str | None = None,
    acceptance: str | None = None,
    objective: str = "",
    depends_on: list[str] | None = None,
    feeds_into: list[str] | None = None,
) -> dict:
    """Create an accelerator - a technical capability that enables apps and integrations.

    Accelerators are reusable platform components that apps depend on. They define
    data flow through integrations (sources_from, publishes_to) and can depend on
    other accelerators to form a capability graph.

    Example: A "Data Lake" accelerator might:
    - Source from: salesforce-integration, erp-integration
    - Publish to: analytics-warehouse-integration
    - Feed into: reporting-accelerator, ml-pipeline-accelerator

    Args:
        slug: Unique identifier (e.g., "data-lake", "auth-service", "notification-hub")
        status: Development status (e.g., "alpha", "beta", "production", "deprecated")
        milestone: Target delivery milestone
        acceptance: Acceptance criteria for completion
        objective: Business objective this accelerator achieves
        depends_on: Accelerator slugs this depends on (prerequisites)
        feeds_into: Accelerator slugs that depend on this one
    """
    return await create_accelerator(
        slug=slug,
        status=status,
        milestone=milestone,
        acceptance=acceptance,
        objective=objective,
        depends_on=depends_on,
        feeds_into=feeds_into,
    )


@mcp.tool(annotations=read_only_annotation("Get Accelerator"))
async def mcp_get_accelerator(slug: str, format: str = "full") -> dict | None:
    """Get an accelerator by slug with its integration connections.

    Args:
        slug: Accelerator identifier
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await get_accelerator(slug, format=format)


@mcp.tool(annotations=read_only_annotation("List Accelerators"))
async def mcp_list_accelerators(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all accelerators in the HCD model.

    Use this to understand the technical capability landscape.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await list_accelerators(limit=limit, offset=offset, format=format)


@mcp.tool(annotations=update_annotation("Update Accelerator"))
async def mcp_update_accelerator(
    slug: str,
    status: str | None = None,
    milestone: str | None = None,
    acceptance: str | None = None,
    objective: str | None = None,
    depends_on: list[str] | None = None,
    feeds_into: list[str] | None = None,
) -> dict | None:
    """Update an accelerator. Only provided fields are changed.

    Note: To update integrations (sources_from, publishes_to), include them
    in the request. List parameters replace existing values entirely.

    Args:
        slug: Accelerator identifier to update
        status: New status (optional)
        milestone: New milestone (optional)
        acceptance: New acceptance criteria (optional)
        objective: New objective (optional)
        depends_on: New dependencies - replaces existing (optional)
        feeds_into: New feeds_into - replaces existing (optional)
    """
    return await update_accelerator(
        slug=slug,
        status=status,
        milestone=milestone,
        acceptance=acceptance,
        objective=objective,
        depends_on=depends_on,
        feeds_into=feeds_into,
    )


@mcp.tool(annotations=delete_annotation("Delete Accelerator"))
async def mcp_delete_accelerator(slug: str) -> dict:
    """Delete an accelerator by slug.

    Warning: Apps may reference this accelerator, and other accelerators may
    depend on it.

    Args:
        slug: Accelerator identifier to delete
    """
    return await delete_accelerator(slug)


# ============================================================================
# Integration tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create Integration"))
async def mcp_create_integration(
    slug: str,
    module: str,
    name: str,
    description: str = "",
    direction: str = "bidirectional",
) -> dict:
    """Create an integration - a connection to an external system.

    Integrations represent data flow connections to external systems like APIs,
    databases, or third-party services. They are referenced by accelerators to
    define where data comes from (sources_from) and where it goes (publishes_to).

    Example integrations:
    - salesforce-api (inbound) - pulls customer data
    - analytics-warehouse (outbound) - pushes transformed data
    - erp-sync (bidirectional) - two-way sync with ERP

    Args:
        slug: Unique identifier (e.g., "salesforce-api", "s3-data-lake")
        module: Python module implementing this integration
        name: Human-readable name (e.g., "Salesforce CRM API")
        description: What this integration does and what data flows through it
        direction: Data flow - "inbound", "outbound", or "bidirectional"
    """
    return await create_integration(
        slug=slug,
        module=module,
        name=name,
        description=description,
        direction=direction,
    )


@mcp.tool(annotations=read_only_annotation("Get Integration"))
async def mcp_get_integration(slug: str, format: str = "full") -> dict | None:
    """Get an integration by slug with its accelerator connections.

    Args:
        slug: Integration identifier
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await get_integration(slug, format=format)


@mcp.tool(annotations=read_only_annotation("List Integrations"))
async def mcp_list_integrations(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all integrations in the HCD model.

    Use this to see the external system landscape or find integrations to connect.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await list_integrations(limit=limit, offset=offset, format=format)


@mcp.tool(annotations=update_annotation("Update Integration"))
async def mcp_update_integration(
    slug: str,
    name: str | None = None,
    description: str | None = None,
    direction: str | None = None,
) -> dict | None:
    """Update an integration. Only provided fields are changed.

    Args:
        slug: Integration identifier to update
        name: New display name (optional)
        description: New description (optional)
        direction: New direction - "inbound", "outbound", "bidirectional" (optional)
    """
    return await update_integration(
        slug=slug,
        name=name,
        description=description,
        direction=direction,
    )


@mcp.tool(annotations=delete_annotation("Delete Integration"))
async def mcp_delete_integration(slug: str) -> dict:
    """Delete an integration by slug.

    Warning: Accelerators may reference this integration in their sources_from
    or publishes_to.

    Args:
        slug: Integration identifier to delete
    """
    return await delete_integration(slug)


# ============================================================================
# App tools
# ============================================================================


@mcp.tool(annotations=create_annotation("Create App"))
async def mcp_create_app(
    slug: str,
    name: str,
    app_type: str = "unknown",
    status: str | None = None,
    description: str = "",
    accelerators: list[str] | None = None,
) -> dict:
    """Create an app - a user-facing application in the platform.

    Apps are the top-level containers for user stories. Each app has a type
    indicating its audience and can depend on accelerators for capabilities.

    App types:
    - staff: Internal tools for employees
    - external: Customer/partner-facing applications
    - member-tool: Member self-service applications
    - unknown: Not yet classified

    Example: A "HR Portal" app (staff type) might:
    - Have stories for "View Payslip", "Request Leave", "Update Profile"
    - Depend on accelerators: auth-service, notification-hub

    Args:
        slug: Unique identifier (e.g., "hr-portal", "customer-dashboard")
        name: Human-readable name (e.g., "HR Self-Service Portal")
        app_type: Audience type - "staff", "external", "member-tool", "unknown"
        status: Development status
        description: What this app does and who it serves
        accelerators: List of accelerator slugs this app depends on
    """
    return await create_app(
        slug=slug,
        name=name,
        app_type=app_type,
        status=status,
        description=description,
        accelerators=accelerators,
    )


@mcp.tool(annotations=read_only_annotation("Get App"))
async def mcp_get_app(slug: str, format: str = "full") -> dict | None:
    """Get an app by slug with its stories and accelerator dependencies.

    Args:
        slug: App identifier
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await get_app(slug, format=format)


@mcp.tool(annotations=read_only_annotation("List Apps"))
async def mcp_list_apps(
    limit: int | None = None,
    offset: int = 0,
    format: str = "full",
) -> dict:
    """List all apps in the HCD model.

    Use this to see the application landscape or find apps to add stories to.

    Args:
        limit: Maximum results to return (default 100, max 1000)
        offset: Skip first N results for pagination (default 0)
        format: Response verbosity - "summary", "full", or "extended"
    """
    return await list_apps(limit=limit, offset=offset, format=format)


@mcp.tool(annotations=update_annotation("Update App"))
async def mcp_update_app(
    slug: str,
    name: str | None = None,
    app_type: str | None = None,
    status: str | None = None,
    description: str | None = None,
    accelerators: list[str] | None = None,
) -> dict | None:
    """Update an app. Only provided fields are changed.

    Note: accelerators list replaces the entire list if provided.

    Args:
        slug: App identifier to update
        name: New display name (optional)
        app_type: New type - "staff", "external", "member-tool", "unknown" (optional)
        status: New status (optional)
        description: New description (optional)
        accelerators: New accelerator dependencies - replaces existing (optional)
    """
    return await update_app(
        slug=slug,
        name=name,
        app_type=app_type,
        status=status,
        description=description,
        accelerators=accelerators,
    )


@mcp.tool(annotations=delete_annotation("Delete App"))
async def mcp_delete_app(slug: str) -> dict:
    """Delete an app by slug.

    Warning: Stories belong to apps - deleting an app orphans its stories.

    Args:
        slug: App identifier to delete
    """
    return await delete_app(slug)


def main():
    """Run the HCD MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

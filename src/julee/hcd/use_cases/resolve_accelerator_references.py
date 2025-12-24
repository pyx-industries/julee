"""Use case for resolving accelerator references.

Finds apps, stories, journeys, and integrations related to an accelerator.
"""

from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App
from julee.hcd.entities.code_info import BoundedContextInfo
from julee.hcd.entities.integration import Integration
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.story import Story
from julee.hcd.utils import normalize_name


def get_apps_for_accelerator(
    accelerator: Accelerator,
    apps: list[App],
) -> list[App]:
    """Get apps that expose an accelerator.

    Apps expose accelerators via the 'accelerators' field in their manifest.

    Args:
        accelerator: Accelerator to find apps for
        apps: All App entities

    Returns:
        List of App entities that expose this accelerator, sorted by slug
    """
    matching = [app for app in apps if accelerator.slug in (app.accelerators or [])]
    return sorted(matching, key=lambda a: a.slug)


def get_stories_for_accelerator(
    accelerator: Accelerator,
    apps: list[App],
    stories: list[Story],
) -> list[Story]:
    """Get stories for apps that expose an accelerator.

    Args:
        accelerator: Accelerator to find stories for
        apps: All App entities
        stories: All Story entities

    Returns:
        List of Story entities from apps that expose this accelerator
    """
    # Get app slugs that expose this accelerator
    app_slugs = {
        app.slug for app in apps if accelerator.slug in (app.accelerators or [])
    }

    if not app_slugs:
        return []

    # Find stories for those apps
    matching = [s for s in stories if s.app_slug in app_slugs]
    return sorted(matching, key=lambda s: s.feature_title)


def get_journeys_for_accelerator(
    accelerator: Accelerator,
    apps: list[App],
    stories: list[Story],
    journeys: list[Journey],
) -> list[Journey]:
    """Get journeys that include stories from an accelerator's apps.

    Args:
        accelerator: Accelerator to find journeys for
        apps: All App entities
        stories: All Story entities
        journeys: All Journey entities

    Returns:
        List of Journey entities containing stories from this accelerator's apps
    """
    # Get stories for this accelerator
    accel_stories = get_stories_for_accelerator(accelerator, apps, stories)
    story_titles = {normalize_name(s.feature_title) for s in accel_stories}

    if not story_titles:
        return []

    # Find journeys containing these stories
    matching = []
    for journey in journeys:
        story_refs = journey.get_story_refs()
        if any(normalize_name(ref) in story_titles for ref in story_refs):
            matching.append(journey)

    return sorted(matching, key=lambda j: j.slug)


def get_source_integrations(
    accelerator: Accelerator,
    integrations: list[Integration],
) -> list[Integration]:
    """Get integrations that an accelerator sources from.

    Args:
        accelerator: Accelerator to find sources for
        integrations: All Integration entities

    Returns:
        List of Integration entities this accelerator sources from
    """
    source_slugs = accelerator.get_sources_from_slugs()
    integration_lookup = {i.slug: i for i in integrations}

    return [
        integration_lookup[slug] for slug in source_slugs if slug in integration_lookup
    ]


def get_publish_integrations(
    accelerator: Accelerator,
    integrations: list[Integration],
) -> list[Integration]:
    """Get integrations that an accelerator publishes to.

    Args:
        accelerator: Accelerator to find publish targets for
        integrations: All Integration entities

    Returns:
        List of Integration entities this accelerator publishes to
    """
    publish_slugs = accelerator.get_publishes_to_slugs()
    integration_lookup = {i.slug: i for i in integrations}

    return [
        integration_lookup[slug] for slug in publish_slugs if slug in integration_lookup
    ]


def get_dependent_accelerators(
    accelerator: Accelerator,
    accelerators: list[Accelerator],
) -> list[Accelerator]:
    """Get accelerators that depend on a specific accelerator.

    Args:
        accelerator: Accelerator to find dependents of
        accelerators: All Accelerator entities

    Returns:
        List of Accelerator entities that depend on this one
    """
    matching = [a for a in accelerators if accelerator.slug in a.depends_on]
    return sorted(matching, key=lambda a: a.slug)


def get_fed_by_accelerators(
    accelerator: Accelerator,
    accelerators: list[Accelerator],
) -> list[Accelerator]:
    """Get accelerators that feed into a specific accelerator.

    Args:
        accelerator: Accelerator to find feeders for
        accelerators: All Accelerator entities

    Returns:
        List of Accelerator entities that feed into this one
    """
    matching = [a for a in accelerators if accelerator.slug in a.feeds_into]
    return sorted(matching, key=lambda a: a.slug)


def get_code_info_for_accelerator(
    accelerator: Accelerator,
    code_infos: list[BoundedContextInfo],
) -> BoundedContextInfo | None:
    """Get code info for an accelerator's bounded context.

    Tries to match by slug or snake_case version of slug.

    Args:
        accelerator: Accelerator to find code for
        code_infos: All BoundedContextInfo entities

    Returns:
        BoundedContextInfo if found, None otherwise
    """
    # Try exact match
    for info in code_infos:
        if info.slug == accelerator.slug:
            return info

    # Try snake_case match
    snake_slug = accelerator.slug.replace("-", "_")
    for info in code_infos:
        if info.slug == snake_slug or info.code_dir == snake_slug:
            return info

    return None


def get_accelerator_cross_references(
    accelerator: Accelerator,
    accelerators: list[Accelerator],
    apps: list[App],
    stories: list[Story],
    journeys: list[Journey],
    integrations: list[Integration],
    code_infos: list[BoundedContextInfo],
) -> dict:
    """Get all cross-references for an accelerator.

    Convenience function to get all related entities at once.

    Args:
        accelerator: Accelerator to find references for
        accelerators: All Accelerator entities
        apps: All App entities
        stories: All Story entities
        journeys: All Journey entities
        integrations: All Integration entities
        code_infos: All BoundedContextInfo entities

    Returns:
        Dict with keys: apps, stories, journeys, source_integrations,
                       publish_integrations, dependents, fed_by, code_info
    """
    return {
        "apps": get_apps_for_accelerator(accelerator, apps),
        "stories": get_stories_for_accelerator(accelerator, apps, stories),
        "journeys": get_journeys_for_accelerator(accelerator, apps, stories, journeys),
        "source_integrations": get_source_integrations(accelerator, integrations),
        "publish_integrations": get_publish_integrations(accelerator, integrations),
        "dependents": get_dependent_accelerators(accelerator, accelerators),
        "fed_by": get_fed_by_accelerators(accelerator, accelerators),
        "code_info": get_code_info_for_accelerator(accelerator, code_infos),
    }

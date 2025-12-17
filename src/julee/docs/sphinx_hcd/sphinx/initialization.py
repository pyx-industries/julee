"""Sphinx initialization handlers for HCD context.

Handles builder-inited event to set up the HCDContext and populate
repositories with data that doesn't change during the build.
"""

import logging
from pathlib import Path

from ..config import get_config
from ..parsers import (
    parse_bounded_context,
    scan_app_manifests,
    scan_bounded_contexts,
    scan_feature_directory,
    scan_integration_manifests,
)
from .context import HCDContext, set_hcd_context

logger = logging.getLogger(__name__)


def initialize_hcd_context(app) -> None:
    """Initialize HCDContext at builder-inited.

    Creates the context and populates repositories with data that is
    static during the build:
    - Stories (from .feature files)
    - Apps (from app.yaml manifests)
    - Integrations (from integration.yaml manifests)
    - Code info (from src/ introspection)

    Journeys, epics, and accelerators are populated during doctree
    processing as they're defined in RST files.

    Args:
        app: Sphinx application object
    """
    context = HCDContext()
    set_hcd_context(app, context)

    config = get_config()

    # Load stories from feature files
    _load_stories(context, config)

    # Load apps from manifests
    _load_apps(context, config)

    # Load integrations from manifests
    _load_integrations(context, config)

    # Load code info from src/ introspection
    _load_code_info(context, config)

    logger.info("HCDContext initialized")


def _load_stories(context: HCDContext, config) -> None:
    """Load stories from feature files into the repository."""
    features_dir = config.get_path("feature_files")
    if not features_dir.exists():
        logger.info(f"Features directory not found: {features_dir}")
        return

    stories = scan_feature_directory(features_dir, config.project_root)
    for story in stories:
        context.story_repo.save(story)

    logger.info(f"Loaded {len(stories)} stories from feature files")


def _load_apps(context: HCDContext, config) -> None:
    """Load apps from manifest files into the repository."""
    apps_dir = config.get_path("app_manifests")
    if not apps_dir.exists():
        logger.info(f"Applications directory not found: {apps_dir}")
        return

    apps = scan_app_manifests(apps_dir)
    for app in apps:
        context.app_repo.save(app)

    logger.info(f"Loaded {len(apps)} apps from manifests")


def _load_integrations(context: HCDContext, config) -> None:
    """Load integrations from manifest files into the repository."""
    integrations_dir = config.get_path("integration_manifests")
    if not integrations_dir.exists():
        logger.info(f"Integrations directory not found: {integrations_dir}")
        return

    integrations = scan_integration_manifests(integrations_dir)
    for integration in integrations:
        context.integration_repo.save(integration)

    logger.info(f"Loaded {len(integrations)} integrations from manifests")


def _load_code_info(context: HCDContext, config) -> None:
    """Load code info from src/ introspection into the repository."""
    src_dir = config.get_path("bounded_contexts")
    if not src_dir.exists():
        logger.info(f"Source directory not found: {src_dir}")
        return

    contexts = scan_bounded_contexts(src_dir)
    for code_info in contexts:
        context.code_info_repo.save(code_info)

    logger.info(f"Loaded {len(contexts)} bounded contexts from source")


def purge_doc_from_context(app, env, docname: str) -> None:
    """Purge entities from a document when it's being re-read.

    Called during env-purge-doc event for incremental builds.

    Args:
        app: Sphinx application object
        env: Sphinx environment
        docname: Document being purged
    """
    from .context import get_hcd_context

    try:
        context = get_hcd_context(app)
        results = context.clear_by_docname(docname)

        total = sum(results.values())
        if total > 0:
            logger.debug(
                f"Purged from {docname}: "
                f"{results.get('journeys', 0)} journeys, "
                f"{results.get('epics', 0)} epics, "
                f"{results.get('accelerators', 0)} accelerators"
            )
    except AttributeError:
        # Context not initialized yet - this is fine during startup
        pass

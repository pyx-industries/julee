"""YAML manifest parsers.

Parses YAML manifest files for apps and integrations.
"""

import logging
from pathlib import Path

import yaml

from ..entities.app import App
from ..entities.integration import Integration

logger = logging.getLogger(__name__)


def parse_app_manifest(manifest_path: Path, app_slug: str | None = None) -> App | None:
    """Parse an app.yaml manifest file.

    Args:
        manifest_path: Path to the app.yaml file
        app_slug: Optional app slug override. If None, extracted from directory name.

    Returns:
        App entity, or None if parsing fails
    """
    try:
        content = manifest_path.read_text()
    except Exception as e:
        logger.warning(f"Could not read {manifest_path}: {e}")
        return None

    try:
        manifest = yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.warning(f"Could not parse YAML in {manifest_path}: {e}")
        return None

    if manifest is None:
        logger.warning(f"Empty manifest at {manifest_path}")
        return None

    # Extract app slug from directory name if not provided
    if app_slug is None:
        app_slug = manifest_path.parent.name

    return App.from_manifest(
        slug=app_slug,
        manifest=manifest,
        manifest_path=str(manifest_path),
    )


def scan_app_manifests(apps_dir: Path) -> list[App]:
    """Scan a directory for app.yaml manifest files.

    Expects structure: apps_dir/{app-slug}/app.yaml

    Args:
        apps_dir: Directory containing app subdirectories

    Returns:
        List of parsed App entities
    """
    apps = []

    if not apps_dir.exists():
        logger.info(
            f"Apps directory not found at {apps_dir} - no app manifests to index"
        )
        return apps

    for app_dir in apps_dir.iterdir():
        if not app_dir.is_dir():
            continue

        manifest_path = app_dir / "app.yaml"
        if not manifest_path.exists():
            continue

        app = parse_app_manifest(manifest_path)
        if app:
            apps.append(app)

    logger.info(f"Indexed {len(apps)} apps from {apps_dir}")
    return apps


def parse_manifest_content(content: str) -> dict | None:
    """Parse YAML content string.

    A lower-level helper for testing and direct content parsing.

    Args:
        content: YAML content string

    Returns:
        Parsed dictionary, or None if parsing fails
    """
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.warning(f"Could not parse YAML content: {e}")
        return None


# Integration manifest parsing


def parse_integration_manifest(
    manifest_path: Path, module_name: str | None = None
) -> Integration | None:
    """Parse an integration.yaml manifest file.

    Args:
        manifest_path: Path to the integration.yaml file
        module_name: Optional module name override. If None, extracted from directory name.

    Returns:
        Integration entity, or None if parsing fails
    """
    try:
        content = manifest_path.read_text()
    except Exception as e:
        logger.warning(f"Could not read {manifest_path}: {e}")
        return None

    try:
        manifest = yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.warning(f"Could not parse YAML in {manifest_path}: {e}")
        return None

    if manifest is None:
        logger.warning(f"Empty manifest at {manifest_path}")
        return None

    # Extract module name from directory name if not provided
    if module_name is None:
        module_name = manifest_path.parent.name

    return Integration.from_manifest(
        module_name=module_name,
        manifest=manifest,
        manifest_path=str(manifest_path),
    )


def scan_integration_manifests(integrations_dir: Path) -> list[Integration]:
    """Scan a directory for integration.yaml manifest files.

    Expects structure: integrations_dir/{module_name}/integration.yaml
    Directories starting with '_' are skipped.

    Args:
        integrations_dir: Directory containing integration subdirectories

    Returns:
        List of parsed Integration entities
    """
    integrations = []

    if not integrations_dir.exists():
        logger.info(
            f"Integrations directory not found at {integrations_dir} - "
            "no integration manifests to index"
        )
        return integrations

    for int_dir in integrations_dir.iterdir():
        # Skip non-directories and directories starting with '_'
        if not int_dir.is_dir() or int_dir.name.startswith("_"):
            continue

        manifest_path = int_dir / "integration.yaml"
        if not manifest_path.exists():
            continue

        integration = parse_integration_manifest(manifest_path)
        if integration:
            integrations.append(integration)

    logger.info(f"Indexed {len(integrations)} integrations from {integrations_dir}")
    return integrations

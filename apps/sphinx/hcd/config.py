"""Configuration for sphinx_hcd extension.

Provides defaults matching the RBA solution layout, with ability to override
via sphinx_hcd config dict in conf.py.
"""

from copy import deepcopy
from pathlib import Path

DEFAULT_CONFIG = {
    "paths": {
        # Where to find Gherkin feature files: {app}/features/*.feature
        "feature_files": "tests/e2e/",
        # Where to find app manifests: */app.yaml
        "app_manifests": "apps/",
        # Where to find integration manifests: */integration.yaml
        "integration_manifests": "src/integrations/",
        # Where to find bounded context code: {slug}/ directories
        "bounded_contexts": "src/",
    },
    "docs_structure": {
        # RST file locations relative to docs root
        "applications": "applications",
        "personas": "users/personas",
        "journeys": "users/journeys",
        "epics": "users/epics",
        "accelerators": "domain/accelerators",
        "integrations": "integrations",
        "stories": "users/stories",
    },
    # Repository backend: "memory" (default) or "rst"
    # When "rst", entities are loaded from/saved to RST files
    "repository_backend": "memory",
}


def config_factory() -> dict:
    """Return a fresh config dict populated with defaults.

    Usage in conf.py::

        from apps.sphinx.hcd.config import config_factory

        sphinx_hcd = config_factory()
        sphinx_hcd['paths']['feature_files'] = 'tests/bdd/'

    Returns:
        A deep copy of DEFAULT_CONFIG that can be modified.
    """
    return deepcopy(DEFAULT_CONFIG)


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base, returning new dict."""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class HCDConfig:
    """Configuration holder for sphinx_hcd extension.

    Provides access to paths and doc structure settings, resolving paths
    relative to the project root.
    """

    def __init__(self, app):
        """Initialize config from Sphinx app.

        Args:
            app: Sphinx application instance
        """
        self._app = app
        self._docs_dir = Path(app.srcdir)
        self._project_root = self._docs_dir.parent

        # Merge user config with defaults
        user_config = getattr(app.config, "sphinx_hcd", {}) or {}
        self._config = _deep_merge(DEFAULT_CONFIG, user_config)

    @property
    def project_root(self) -> Path:
        """Project root directory (parent of docs/)."""
        return self._project_root

    @property
    def docs_dir(self) -> Path:
        """Documentation source directory."""
        return self._docs_dir

    def get_path(self, key: str) -> Path:
        """Get an absolute path from the paths config.

        Args:
            key: Path key (e.g., 'feature_files', 'app_manifests')

        Returns:
            Absolute Path resolved relative to project root
        """
        rel_path = self._config["paths"].get(key, "")
        return self._project_root / rel_path

    def get_doc_path(self, key: str) -> str:
        """Get a doc structure path.

        Args:
            key: Doc path key (e.g., 'applications', 'personas')

        Returns:
            Relative path string for use in doc references
        """
        return self._config["docs_structure"].get(key, key)

    @property
    def repository_backend(self) -> str:
        """Get the repository backend type.

        Returns:
            "memory" or "rst"
        """
        return self._config.get("repository_backend", "memory")

    @property
    def use_rst_backend(self) -> bool:
        """Check if RST backend is configured.

        Returns:
            True if repository_backend is "rst"
        """
        return self.repository_backend == "rst"

    def get_rst_dir(self, entity_type: str) -> Path:
        """Get the RST directory for an entity type.

        Args:
            entity_type: Entity type key (e.g., 'journeys', 'epics')

        Returns:
            Absolute path to the RST directory
        """
        doc_path = self.get_doc_path(entity_type)
        return self._docs_dir / doc_path


# Module-level config instance, set by setup()
_config: HCDConfig | None = None


def get_config() -> HCDConfig:
    """Get the current HCD configuration.

    Returns:
        HCDConfig instance

    Raises:
        RuntimeError: If called before extension is initialized
    """
    if _config is None:
        raise RuntimeError(
            "sphinx_hcd config not initialized. "
            "Ensure 'julee.docs.sphinx_hcd' is in your Sphinx extensions."
        )
    return _config


def init_config(app) -> HCDConfig:
    """Initialize config from Sphinx app. Called by extension setup.

    Args:
        app: Sphinx application instance

    Returns:
        HCDConfig instance
    """
    global _config
    _config = HCDConfig(app)
    return _config

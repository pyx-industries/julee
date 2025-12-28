"""Configuration for sphinx_hcd extension.

Provides defaults matching the RBA solution layout, with ability to override
via sphinx_hcd config dict in conf.py.

Configuration can be set via:
1. Dict in conf.py: sphinx_hcd = {'paths': {'feature_files': 'tests/bdd/'}}
2. Pydantic model in conf.py: sphinx_hcd = SphinxHCDConfig(paths=PathsConfig(...))
3. Environment variables: SPHINX_HCD_REPOSITORY_BACKEND=rst
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PathsConfig(BaseModel):
    """Paths to source directories relative to project root."""

    feature_files: str = Field(
        default="tests/e2e/",
        description="Where to find Gherkin feature files: {app}/features/*.feature",
    )
    app_manifests: str = Field(
        default="apps/",
        description="Where to find app manifests: */app.yaml",
    )
    integration_manifests: str = Field(
        default="src/integrations/",
        description="Where to find integration manifests: */integration.yaml",
    )
    bounded_contexts: str = Field(
        default="src/julee/",
        description="Where to find bounded context code: {slug}/ directories",
    )


class DocsStructureConfig(BaseModel):
    """RST file locations relative to docs root."""

    applications: str = "applications"
    personas: str = "users/personas"
    journeys: str = "users/journeys"
    epics: str = "users/epics"
    accelerators: str = "domain/accelerators"
    integrations: str = "integrations"
    stories: str = "users/stories"


class SphinxHCDConfig(BaseModel):
    """Root configuration for sphinx_hcd extension.

    Can be instantiated directly in conf.py or created from a dict.
    Environment variables override config values.
    """

    paths: PathsConfig = Field(default_factory=PathsConfig)
    docs_structure: DocsStructureConfig = Field(default_factory=DocsStructureConfig)
    repository_backend: Literal["memory", "rst"] = Field(
        default="memory",
        description="Repository backend: 'memory' (default) or 'rst'",
    )

    @model_validator(mode="before")
    @classmethod
    def apply_env_overrides(cls, values: dict) -> dict:
        """Apply environment variable overrides."""
        # Check for env var override
        env_backend = os.environ.get("SPHINX_HCD_REPOSITORY_BACKEND")
        if env_backend and env_backend in ("memory", "rst"):
            values["repository_backend"] = env_backend
        return values


# Legacy DEFAULT_CONFIG for backwards compatibility
DEFAULT_CONFIG = {
    "paths": PathsConfig().model_dump(),
    "docs_structure": DocsStructureConfig().model_dump(),
    "repository_backend": "memory",
}


def config_factory() -> dict:
    """Return a fresh config dict populated with defaults.

    Usage in conf.py::

        from apps.sphinx.hcd.config import config_factory

        sphinx_hcd = config_factory()
        sphinx_hcd['paths']['feature_files'] = 'tests/bdd/'

    Returns:
        A fresh dict with default config values.
    """
    return SphinxHCDConfig().model_dump()


def _parse_config(user_config) -> SphinxHCDConfig:
    """Parse user config into validated SphinxHCDConfig.

    Args:
        user_config: Dict, SphinxHCDConfig, or None

    Returns:
        Validated SphinxHCDConfig instance
    """
    if user_config is None:
        return SphinxHCDConfig()
    if isinstance(user_config, SphinxHCDConfig):
        return user_config
    if isinstance(user_config, dict):
        return SphinxHCDConfig(**user_config)
    raise TypeError(
        f"sphinx_hcd config must be dict or SphinxHCDConfig, got {type(user_config)}"
    )


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

        # Parse and validate user config
        user_config = getattr(app.config, "sphinx_hcd", None)
        self._model = _parse_config(user_config)

    @property
    def project_root(self) -> Path:
        """Project root directory (parent of docs/)."""
        return self._project_root

    @property
    def docs_dir(self) -> Path:
        """Documentation source directory."""
        return self._docs_dir

    @property
    def model(self) -> SphinxHCDConfig:
        """Access the underlying validated config model."""
        return self._model

    def get_path(self, key: str) -> Path:
        """Get an absolute path from the paths config.

        Args:
            key: Path key (e.g., 'feature_files', 'app_manifests')

        Returns:
            Absolute Path resolved relative to project root
        """
        rel_path = getattr(self._model.paths, key, "")
        return self._project_root / rel_path

    def get_doc_path(self, key: str) -> str:
        """Get a doc structure path.

        Args:
            key: Doc path key (e.g., 'applications', 'personas')

        Returns:
            Relative path string for use in doc references
        """
        return getattr(self._model.docs_structure, key, key)

    @property
    def repository_backend(self) -> str:
        """Get the repository backend type.

        Returns:
            "memory" or "rst"
        """
        return self._model.repository_backend

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

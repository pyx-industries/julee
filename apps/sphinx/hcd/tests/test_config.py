"""Tests for sphinx_hcd configuration."""

import pytest

from apps.sphinx.hcd.config import (
    PathsConfig,
    SphinxHCDConfig,
    _parse_config,
    config_factory,
)


class TestSphinxHCDConfig:
    """Test SphinxHCDConfig Pydantic model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = SphinxHCDConfig()

        assert config.repository_backend == "memory"
        assert config.paths.feature_files == "tests/e2e/"
        assert config.paths.app_manifests == "apps/"
        assert config.docs_structure.applications == "applications"
        assert config.docs_structure.personas == "users/personas"

    def test_custom_values(self) -> None:
        """Test configuration with custom values."""
        config = SphinxHCDConfig(
            paths=PathsConfig(feature_files="tests/bdd/"),
            repository_backend="rst",
        )

        assert config.paths.feature_files == "tests/bdd/"
        assert config.repository_backend == "rst"

    def test_partial_paths_override(self) -> None:
        """Test partial override of paths config."""
        config = SphinxHCDConfig(
            paths=PathsConfig(app_manifests="applications/"),
        )

        assert config.paths.app_manifests == "applications/"
        assert config.paths.feature_files == "tests/e2e/"  # Default preserved

    def test_invalid_repository_backend(self) -> None:
        """Test that invalid repository_backend raises error."""
        with pytest.raises(ValueError):
            SphinxHCDConfig(repository_backend="invalid")


class TestParseConfig:
    """Test _parse_config helper function."""

    def test_parse_none(self) -> None:
        """Test parsing None returns defaults."""
        config = _parse_config(None)
        assert isinstance(config, SphinxHCDConfig)
        assert config.repository_backend == "memory"

    def test_parse_dict(self) -> None:
        """Test parsing dict config."""
        config = _parse_config({
            "paths": {"feature_files": "tests/"},
            "repository_backend": "rst",
        })
        assert config.paths.feature_files == "tests/"
        assert config.repository_backend == "rst"

    def test_parse_model(self) -> None:
        """Test parsing SphinxHCDConfig passes through."""
        original = SphinxHCDConfig(repository_backend="rst")
        config = _parse_config(original)
        assert config is original

    def test_parse_invalid_type(self) -> None:
        """Test parsing invalid type raises error."""
        with pytest.raises(TypeError):
            _parse_config("invalid")


class TestConfigFactory:
    """Test config_factory function."""

    def test_returns_dict(self) -> None:
        """Test config_factory returns dict."""
        config = config_factory()
        assert isinstance(config, dict)
        assert "paths" in config
        assert "docs_structure" in config
        assert "repository_backend" in config

    def test_returns_defaults(self) -> None:
        """Test config_factory returns default values."""
        config = config_factory()
        assert config["paths"]["feature_files"] == "tests/e2e/"
        assert config["repository_backend"] == "memory"

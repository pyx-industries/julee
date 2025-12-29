"""Tests for DocumentationMapping with SemanticRelation support."""

import pytest

from apps.sphinx.shared.documentation_mapping import (
    DocumentationMapping,
    DocumentationPattern,
    get_documentation_mapping,
)
from julee.core.entities.application import Application
from julee.core.entities.bounded_context import BoundedContext
from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.persona import Persona


class TestDocumentationPattern:
    """Tests for DocumentationPattern."""

    def test_page_pattern_resolves_slug(self):
        """Page pattern should format slug into URL."""
        pattern = DocumentationPattern("page", "users/personas/{slug}")
        result = pattern.resolve("doc-writer")
        assert result == "users/personas/doc-writer"

    def test_autoapi_pattern_resolves_slug(self):
        """Autoapi pattern should format slug into URL."""
        pattern = DocumentationPattern("autoapi", "autoapi/julee/{slug}/index")
        result = pattern.resolve("core")
        assert result == "autoapi/julee/core/index"

    def test_pattern_requires_pattern_for_page_type(self):
        """Page/autoapi types require pattern string."""
        pattern = DocumentationPattern("page")
        with pytest.raises(ValueError, match="Pattern required"):
            pattern.resolve("test")

    def test_anchor_requires_lookup_func(self):
        """Anchor type requires lookup function."""
        pattern = DocumentationPattern("anchor")
        with pytest.raises(ValueError, match="Lookup function required"):
            pattern.resolve("test", app=object())

    def test_anchor_requires_app(self):
        """Anchor lookup requires Sphinx app."""
        pattern = DocumentationPattern(
            "anchor", lookup_func=lambda slug, app: (slug, slug)
        )
        with pytest.raises(ValueError, match="Sphinx app required"):
            pattern.resolve("test")


class TestDocumentationMapping:
    """Tests for DocumentationMapping registry."""

    def test_core_bounded_context_pattern(self):
        """BoundedContext should resolve to autoapi page."""
        mapping = DocumentationMapping()
        result = mapping.resolve(BoundedContext, "core")
        assert result == "autoapi/julee/core/index"

    def test_core_application_pattern(self):
        """Application should resolve to autoapi page."""
        mapping = DocumentationMapping()
        result = mapping.resolve(Application, "api")
        assert result == "autoapi/apps/api/index"

    def test_hcd_persona_pattern(self):
        """Persona should resolve to dedicated page."""
        mapping = DocumentationMapping()
        result = mapping.resolve(Persona, "doc-writer")
        assert result == "users/personas/doc-writer"

    def test_hcd_epic_pattern(self):
        """Epic should resolve to dedicated page."""
        mapping = DocumentationMapping()
        result = mapping.resolve(Epic, "documentation")
        assert result == "users/epics/documentation"

    def test_hcd_journey_pattern(self):
        """Journey should resolve to dedicated page."""
        mapping = DocumentationMapping()
        result = mapping.resolve(Journey, "onboarding")
        assert result == "users/journeys/onboarding"


class TestSemanticRelationResolution:
    """Tests for semantic relation-based resolution."""

    def test_accelerator_projects_bounded_context(self):
        """Accelerator should resolve via PROJECTS relation to BC pattern.

        Accelerator has @semantic_relation(BoundedContext, PROJECTS), so
        it should use BoundedContext's autoapi pattern.
        """
        mapping = DocumentationMapping()
        result = mapping.resolve(Accelerator, "hcd")
        assert result == "autoapi/julee/hcd/index"

    def test_app_projects_application(self):
        """HCD App should resolve via PROJECTS relation to Application pattern.

        App has @semantic_relation(Application, PROJECTS), so
        it should use Application's autoapi pattern.
        """
        mapping = DocumentationMapping()
        result = mapping.resolve(App, "sphinx")
        assert result == "autoapi/apps/sphinx/index"

    def test_get_pattern_follows_projects_relation(self):
        """get_pattern should follow PROJECTS relation to target."""
        mapping = DocumentationMapping()

        # Accelerator's pattern should be the same as BoundedContext's
        acc_pattern = mapping.get_pattern(Accelerator)
        bc_pattern = mapping.get_pattern(BoundedContext)

        assert acc_pattern is not None
        assert bc_pattern is not None
        assert acc_pattern.pattern == bc_pattern.pattern

    def test_unregistered_entity_returns_none(self):
        """Entities without patterns or relations return None."""
        from pydantic import BaseModel

        class UnknownEntity(BaseModel):
            slug: str

        mapping = DocumentationMapping()
        result = mapping.resolve(UnknownEntity, "test")
        assert result is None


class TestSingletonMapping:
    """Tests for singleton mapping access."""

    def test_get_documentation_mapping_returns_singleton(self):
        """get_documentation_mapping should return same instance."""
        mapping1 = get_documentation_mapping()
        mapping2 = get_documentation_mapping()
        assert mapping1 is mapping2

    def test_singleton_has_default_patterns(self):
        """Singleton should have default patterns registered."""
        mapping = get_documentation_mapping()
        assert mapping.get_pattern(BoundedContext) is not None
        assert mapping.get_pattern(Application) is not None
        assert mapping.get_pattern(Persona) is not None

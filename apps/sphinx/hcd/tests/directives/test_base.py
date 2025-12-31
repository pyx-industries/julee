"""Tests for base directive utilities."""

from apps.sphinx.hcd.directives.base import make_deprecated_directive


class TestMakeDeprecatedDirective:
    """Test make_deprecated_directive function."""

    def test_creates_subclass(self) -> None:
        """Test that function creates a proper subclass."""
        from sphinx.util.docutils import SphinxDirective

        # Create a simple base class
        class TestDirective(SphinxDirective):
            def run(self):
                return []

        DeprecatedClass = make_deprecated_directive(
            TestDirective,
            "old-name",
            "new-name",
        )

        assert issubclass(DeprecatedClass, TestDirective)

    def test_class_name_set(self) -> None:
        """Test that deprecated class has appropriate name."""
        from sphinx.util.docutils import SphinxDirective

        class TestDirective(SphinxDirective):
            def run(self):
                return []

        DeprecatedClass = make_deprecated_directive(
            TestDirective,
            "old-name",
            "new-name",
        )

        assert "Deprecated" in DeprecatedClass.__name__


class TestDirectiveImports:
    """Test that all directives can be imported."""

    def test_story_directives_import(self) -> None:
        """Test story directive imports."""
        from apps.sphinx.hcd.directives.story import (
            StoriesDirective,
            StoryAppDirective,
            StoryIndexDirective,
            StoryListForAppDirective,
            StoryListForPersonaDirective,
            StoryRefDirective,
        )

        assert StoryAppDirective is not None
        assert StoryIndexDirective is not None
        assert StoryListForAppDirective is not None
        assert StoryListForPersonaDirective is not None
        assert StoryRefDirective is not None
        assert StoriesDirective is not None

    def test_journey_directives_import(self) -> None:
        """Test journey directive imports."""
        from apps.sphinx.hcd.directives.journey import (
            DefineJourneyDirective,
            JourneyIndexDirective,
            JourneysForPersonaDirective,
            StepEpicDirective,
            StepPhaseDirective,
            StepStoryDirective,
        )

        assert DefineJourneyDirective is not None
        assert JourneyIndexDirective is not None
        assert JourneysForPersonaDirective is not None
        assert StepEpicDirective is not None
        assert StepPhaseDirective is not None
        assert StepStoryDirective is not None

    def test_epic_directives_import(self) -> None:
        """Test epic directive imports."""
        from apps.sphinx.hcd.directives.epic import (
            DefineEpicDirective,
            EpicsForPersonaDirective,
            EpicStoryDirective,
        )
        from apps.sphinx.hcd.generated_directives import GeneratedEpicIndexDirective

        assert DefineEpicDirective is not None
        assert EpicStoryDirective is not None
        assert EpicsForPersonaDirective is not None
        assert GeneratedEpicIndexDirective is not None

    def test_app_directives_import(self) -> None:
        """Test app directive imports."""
        from apps.sphinx.hcd.directives.app import (
            AppsForPersonaDirective,
            DefineAppDirective,
        )
        from apps.sphinx.hcd.generated_directives import GeneratedAppIndexDirective

        assert DefineAppDirective is not None
        assert AppsForPersonaDirective is not None
        assert GeneratedAppIndexDirective is not None

    def test_accelerator_directives_import(self) -> None:
        """Test accelerator directive imports from supply_chain."""
        # NOTE: Accelerator directives moved to apps.sphinx.supply_chain
        from apps.sphinx.supply_chain.directives.accelerator import (
            AcceleratorDependencyDiagramDirective,
            AcceleratorsForAppDirective,
            AcceleratorStatusDirective,
            DefineAcceleratorDirective,
        )
        from apps.sphinx.supply_chain.generated_directives import GeneratedAcceleratorIndexDirective

        assert DefineAcceleratorDirective is not None
        assert AcceleratorsForAppDirective is not None
        assert AcceleratorDependencyDiagramDirective is not None
        assert AcceleratorStatusDirective is not None
        assert GeneratedAcceleratorIndexDirective is not None

    def test_integration_directives_import(self) -> None:
        """Test integration directive imports."""
        from apps.sphinx.hcd.directives.integration import (
            DefineIntegrationDirective,
        )
        from apps.sphinx.hcd.generated_directives import GeneratedIntegrationIndexDirective

        assert DefineIntegrationDirective is not None
        assert GeneratedIntegrationIndexDirective is not None

    def test_persona_directives_import(self) -> None:
        """Test persona directive imports."""
        from apps.sphinx.hcd.directives.persona import (
            PersonaDiagramDirective,
            PersonaIndexDiagramDirective,
        )

        assert PersonaDiagramDirective is not None
        assert PersonaIndexDiagramDirective is not None


class TestEventHandlerImports:
    """Test that all event handlers can be imported."""

    def test_event_handlers_import(self) -> None:
        """Test event handler imports."""
        from apps.sphinx.hcd.event_handlers import (
            on_builder_inited,
            on_doctree_read,
            on_doctree_resolved,
            on_env_purge_doc,
        )

        assert on_builder_inited is not None
        assert on_doctree_read is not None
        assert on_doctree_resolved is not None
        assert on_env_purge_doc is not None

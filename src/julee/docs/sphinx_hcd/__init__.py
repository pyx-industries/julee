"""Sphinx HCD (Human-Centered Design) Extensions for Julee Solutions.

This package provides Sphinx extensions for documenting Julee-based solutions
using Human-Centered Design patterns. It supports:

- Stories: User stories derived from Gherkin .feature files
- Journeys: User journeys composed of stories and epics
- Epics: Collections of related stories
- Apps: Application documentation with manifest-based metadata
- Accelerators: Domain accelerator documentation with bounded context scanning
- Integrations: External integration documentation
- Personas: Auto-generated UML diagrams showing persona-epic-app relationships

Usage in conf.py::

    extensions = ["julee.docs.sphinx_hcd"]

    # Optional configuration (defaults match standard Julee layout)
    sphinx_hcd = {
        'paths': {
            'feature_files': 'tests/e2e/',
            'app_manifests': 'apps/',
            'integration_manifests': 'src/integrations/',
            'bounded_contexts': 'src/',
        },
        'docs_structure': {
            'applications': 'applications',
            'personas': 'users/personas',
            'journeys': 'users/journeys',
            'epics': 'users/epics',
            'accelerators': 'domain/accelerators',
            'integrations': 'integrations',
            'stories': 'users/stories',
        },
    }
"""

from sphinx.util import logging

from .config import init_config

logger = logging.getLogger(__name__)

# Feature flag for new architecture (set to True to use new directives)
USE_NEW_ARCHITECTURE = True


def setup(app):
    """Set up all HCD extensions for Sphinx."""
    # Register configuration value first
    app.add_config_value("sphinx_hcd", {}, "env")

    # Initialize config when builder starts (after conf.py is loaded)
    app.connect("builder-inited", _init_config_handler, priority=0)

    if USE_NEW_ARCHITECTURE:
        _setup_new_architecture(app)
    else:
        _setup_legacy_architecture(app)

    logger.info("Loaded julee.docs.sphinx_hcd extensions")

    return {
        "version": "2.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }


def _init_config_handler(app):
    """Initialize HCD config from Sphinx app config."""
    init_config(app)


def _setup_new_architecture(app):
    """Set up using new clean architecture directives."""
    from .sphinx.directives import (
        # Story directives
        StoryAppDirective,
        StoryListForPersonaDirective,
        StoryListForAppDirective,
        StoryIndexDirective,
        StoriesDirective,
        StoryRefDirective,
        StorySeeAlsoPlaceholder,
        # Story deprecated aliases
        GherkinStoryDirective,
        GherkinStoriesDirective,
        GherkinStoriesForPersonaDirective,
        GherkinStoriesForAppDirective,
        GherkinStoriesIndexDirective,
        GherkinAppStoriesDirective,
        # Journey directives
        DefineJourneyDirective,
        StepStoryDirective,
        StepEpicDirective,
        StepPhaseDirective,
        JourneyIndexDirective,
        JourneyDependencyGraphDirective,
        JourneyDependencyGraphPlaceholder,
        JourneysForPersonaDirective,
        # Epic directives
        DefineEpicDirective,
        EpicStoryDirective,
        EpicIndexDirective,
        EpicIndexPlaceholder,
        EpicsForPersonaDirective,
        EpicsForPersonaPlaceholder,
        # App directives
        DefineAppDirective,
        DefineAppPlaceholder,
        AppIndexDirective,
        AppIndexPlaceholder,
        AppsForPersonaDirective,
        AppsForPersonaPlaceholder,
        # Accelerator directives
        DefineAcceleratorDirective,
        DefineAcceleratorPlaceholder,
        AcceleratorIndexDirective,
        AcceleratorIndexPlaceholder,
        AcceleratorsForAppDirective,
        AcceleratorsForAppPlaceholder,
        DependentAcceleratorsDirective,
        DependentAcceleratorsPlaceholder,
        AcceleratorDependencyDiagramDirective,
        AcceleratorDependencyDiagramPlaceholder,
        AcceleratorStatusDirective,
        # Integration directives
        DefineIntegrationDirective,
        DefineIntegrationPlaceholder,
        IntegrationIndexDirective,
        IntegrationIndexPlaceholder,
        # Persona directives
        PersonaDiagramDirective,
        PersonaDiagramPlaceholder,
        PersonaIndexDiagramDirective,
        PersonaIndexDiagramPlaceholder,
    )
    from .sphinx.event_handlers import (
        on_builder_inited,
        on_doctree_read,
        on_doctree_resolved,
        on_env_purge_doc,
    )

    # Connect event handlers
    app.connect("builder-inited", on_builder_inited, priority=100)
    app.connect("doctree-read", on_doctree_read)
    app.connect("doctree-resolved", on_doctree_resolved)
    app.connect("env-purge-doc", on_env_purge_doc)

    # Register story directives
    app.add_directive("story", StoryRefDirective)
    app.add_directive("stories", StoriesDirective)
    app.add_directive("story-list-for-persona", StoryListForPersonaDirective)
    app.add_directive("story-list-for-app", StoryListForAppDirective)
    app.add_directive("story-index", StoryIndexDirective)
    app.add_directive("story-app", StoryAppDirective)
    app.add_node(StorySeeAlsoPlaceholder)

    # Register deprecated story aliases
    app.add_directive("gherkin-story", GherkinStoryDirective)
    app.add_directive("gherkin-stories", GherkinStoriesDirective)
    app.add_directive("gherkin-stories-for-persona", GherkinStoriesForPersonaDirective)
    app.add_directive("gherkin-stories-for-app", GherkinStoriesForAppDirective)
    app.add_directive("gherkin-stories-index", GherkinStoriesIndexDirective)
    app.add_directive("gherkin-app-stories", GherkinAppStoriesDirective)

    # Register journey directives
    app.add_directive("define-journey", DefineJourneyDirective)
    app.add_directive("step-story", StepStoryDirective)
    app.add_directive("step-epic", StepEpicDirective)
    app.add_directive("step-phase", StepPhaseDirective)
    app.add_directive("journey-index", JourneyIndexDirective)
    app.add_directive("journey-dependency-graph", JourneyDependencyGraphDirective)
    app.add_directive("journeys-for-persona", JourneysForPersonaDirective)
    app.add_node(JourneyDependencyGraphPlaceholder)

    # Register epic directives
    app.add_directive("define-epic", DefineEpicDirective)
    app.add_directive("epic-story", EpicStoryDirective)
    app.add_directive("epic-index", EpicIndexDirective)
    app.add_directive("epics-for-persona", EpicsForPersonaDirective)
    app.add_node(EpicIndexPlaceholder)
    app.add_node(EpicsForPersonaPlaceholder)

    # Register app directives
    app.add_directive("define-app", DefineAppDirective)
    app.add_directive("app-index", AppIndexDirective)
    app.add_directive("apps-for-persona", AppsForPersonaDirective)
    app.add_node(DefineAppPlaceholder)
    app.add_node(AppIndexPlaceholder)
    app.add_node(AppsForPersonaPlaceholder)

    # Register accelerator directives
    app.add_directive("define-accelerator", DefineAcceleratorDirective)
    app.add_directive("accelerator-index", AcceleratorIndexDirective)
    app.add_directive("accelerators-for-app", AcceleratorsForAppDirective)
    app.add_directive("dependent-accelerators", DependentAcceleratorsDirective)
    app.add_directive("accelerator-dependency-diagram", AcceleratorDependencyDiagramDirective)
    app.add_directive("accelerator-status", AcceleratorStatusDirective)
    app.add_node(DefineAcceleratorPlaceholder)
    app.add_node(AcceleratorIndexPlaceholder)
    app.add_node(AcceleratorsForAppPlaceholder)
    app.add_node(DependentAcceleratorsPlaceholder)
    app.add_node(AcceleratorDependencyDiagramPlaceholder)

    # Register integration directives
    app.add_directive("define-integration", DefineIntegrationDirective)
    app.add_directive("integration-index", IntegrationIndexDirective)
    app.add_node(DefineIntegrationPlaceholder)
    app.add_node(IntegrationIndexPlaceholder)

    # Register persona directives
    app.add_directive("persona-diagram", PersonaDiagramDirective)
    app.add_directive("persona-index-diagram", PersonaIndexDiagramDirective)
    app.add_node(PersonaDiagramPlaceholder)
    app.add_node(PersonaIndexDiagramPlaceholder)

    logger.info("Using new clean architecture directives")


def _setup_legacy_architecture(app):
    """Set up using legacy directive modules (for backwards compatibility)."""
    from . import accelerators, apps, epics, integrations, journeys, personas, stories

    # Call setup on each legacy module
    stories.setup(app)
    journeys.setup(app)
    epics.setup(app)
    apps.setup(app)
    accelerators.setup(app)
    integrations.setup(app)
    personas.setup(app)

    logger.info("Using legacy directive modules")

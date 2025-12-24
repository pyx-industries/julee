"""Sphinx HCD (Human-Centered Design) Extension.

Provides Sphinx directives for documenting Julee-based solutions
using Human-Centered Design patterns.
"""

from sphinx.util import logging

from .adapters import SyncRepositoryAdapter
from .config import init_config
from .context import (
    HCDContext,
    create_sphinx_env_context,
    ensure_hcd_context,
    get_hcd_context,
    set_hcd_context,
)
from .initialization import initialize_hcd_context, purge_doc_from_context

logger = logging.getLogger(__name__)


def setup(app):
    """Set up HCD extension for Sphinx."""
    from .directives import (
        AcceleratorDependencyDiagramDirective,
        AcceleratorDependencyDiagramPlaceholder,
        AcceleratorIndexDirective,
        AcceleratorIndexPlaceholder,
        AcceleratorsForAppDirective,
        AcceleratorsForAppPlaceholder,
        AcceleratorStatusDirective,
        AppIndexDirective,
        AppIndexPlaceholder,
        AppsForPersonaDirective,
        AppsForPersonaPlaceholder,
        AcceleratorListDirective,
        AcceleratorListPlaceholder,
        AppListByInterfaceDirective,
        AppListByInterfacePlaceholder,
        C4ContainerDiagramDirective,
        C4ContainerDiagramPlaceholder,
        ContribIndexDirective,
        ContribIndexPlaceholder,
        ContribListDirective,
        ContribListPlaceholder,
        DefineAcceleratorDirective,
        DefineAcceleratorPlaceholder,
        DefineAppDirective,
        DefineAppPlaceholder,
        DefineContribDirective,
        DefineContribPlaceholder,
        DefineEpicDirective,
        DefineIntegrationDirective,
        DefineIntegrationPlaceholder,
        DefineJourneyDirective,
        DefinePersonaDirective,
        DependentAcceleratorsDirective,
        DependentAcceleratorsPlaceholder,
        EpicIndexDirective,
        EpicIndexPlaceholder,
        EpicsForPersonaDirective,
        EpicsForPersonaPlaceholder,
        EpicStoryDirective,
        GherkinAppStoriesDirective,
        GherkinStoriesDirective,
        GherkinStoriesForAppDirective,
        GherkinStoriesForPersonaDirective,
        GherkinStoriesIndexDirective,
        GherkinStoryDirective,
        IntegrationIndexDirective,
        IntegrationIndexPlaceholder,
        JourneyDependencyGraphDirective,
        JourneyDependencyGraphPlaceholder,
        JourneyIndexDirective,
        JourneysForPersonaDirective,
        ListAcceleratorCodeDirective,
        AcceleratorCodePlaceholder,
        AcceleratorEntityListDirective,
        AcceleratorEntityListPlaceholder,
        AcceleratorUseCaseListDirective,
        AcceleratorUseCaseListPlaceholder,
        EntityDiagramDirective,
        EntityDiagramPlaceholder,
        PersonaDiagramDirective,
        PersonaDiagramPlaceholder,
        PersonaIndexDiagramDirective,
        PersonaIndexDiagramPlaceholder,
        PersonaIndexDirective,
        PersonaIndexPlaceholder,
        StepEpicDirective,
        StepPhaseDirective,
        StepStoryDirective,
        StoriesDirective,
        StoryAppDirective,
        StoryIndexDirective,
        StoryListForAppDirective,
        StoryListForPersonaDirective,
        StoryRefDirective,
        StorySeeAlsoPlaceholder,
    )
    from .event_handlers import (
        on_builder_inited,
        on_doctree_read,
        on_doctree_resolved,
        on_env_check_consistency,
        on_env_merge_info,
        on_env_purge_doc,
    )

    # Register configuration value first
    app.add_config_value("sphinx_hcd", {}, "env")

    # Initialize config when builder starts
    app.connect("builder-inited", _init_config_handler, priority=0)

    # Connect event handlers
    app.connect("builder-inited", on_builder_inited, priority=100)
    app.connect("doctree-read", on_doctree_read)
    app.connect("doctree-resolved", on_doctree_resolved)
    app.connect("env-check-consistency", on_env_check_consistency)
    app.connect("env-merge-info", on_env_merge_info)
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
    app.add_directive(
        "accelerator-dependency-diagram", AcceleratorDependencyDiagramDirective
    )
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
    app.add_directive("define-persona", DefinePersonaDirective)
    app.add_directive("persona-index", PersonaIndexDirective)
    app.add_directive("persona-diagram", PersonaDiagramDirective)
    app.add_directive("persona-index-diagram", PersonaIndexDiagramDirective)
    app.add_node(PersonaIndexPlaceholder)
    app.add_node(PersonaDiagramPlaceholder)
    app.add_node(PersonaIndexDiagramPlaceholder)

    # Register C4 bridge directives (HCD -> C4)
    app.add_directive("c4-container-diagram", C4ContainerDiagramDirective)
    app.add_directive("app-list-by-interface", AppListByInterfaceDirective)
    app.add_directive("accelerator-list", AcceleratorListDirective)
    app.add_node(C4ContainerDiagramPlaceholder)
    app.add_node(AppListByInterfacePlaceholder)
    app.add_node(AcceleratorListPlaceholder)

    # Register contrib directives
    app.add_directive("define-contrib", DefineContribDirective)
    app.add_directive("contrib-index", ContribIndexDirective)
    app.add_directive("contrib-list", ContribListDirective)
    app.add_node(DefineContribPlaceholder)
    app.add_node(ContribIndexPlaceholder)
    app.add_node(ContribListPlaceholder)

    # Register code link directives
    app.add_directive("list-accelerator-code", ListAcceleratorCodeDirective)
    app.add_node(AcceleratorCodePlaceholder)

    # Register entity diagram directives
    app.add_directive("entity-diagram", EntityDiagramDirective)
    app.add_node(EntityDiagramPlaceholder)

    # Register accelerator entity/usecase list directives
    app.add_directive("accelerator-entity-list", AcceleratorEntityListDirective)
    app.add_node(AcceleratorEntityListPlaceholder)
    app.add_directive("accelerator-usecase-list", AcceleratorUseCaseListDirective)
    app.add_node(AcceleratorUseCaseListPlaceholder)

    # Register shared directives
    from apps.sphinx.shared.directives import (
        UseCaseDocumentationDirective,
        UseCaseSSDDirective,
    )

    app.add_directive("usecase-ssd", UseCaseSSDDirective)
    app.add_directive("usecase-documentation", UseCaseDocumentationDirective)

    logger.info("Loaded apps.sphinx.hcd extensions")

    return {
        "version": "2.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _init_config_handler(app):
    """Initialize HCD config from Sphinx app config."""
    init_config(app)


__all__ = [
    "HCDContext",
    "SyncRepositoryAdapter",
    "create_sphinx_env_context",
    "ensure_hcd_context",
    "get_hcd_context",
    "initialize_hcd_context",
    "purge_doc_from_context",
    "set_hcd_context",
    "setup",
]

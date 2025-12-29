"""Sphinx HCD (Human-Centered Design) Extension.

Provides Sphinx directives for documenting Julee solutions through the
Human-Centered Design viewpoint - projecting solution content in terms
of personas, journeys, stories, and apps.

HCD as a Viewpoint
------------------
The HCD extension is one of three viewpoint projections in julee:

- ``julee.hcd`` → Human-Centered Design viewpoint (this extension)
- ``julee.c4`` → Architecture viewpoint
- ``julee.core`` → Technical Manual viewpoint

Each viewpoint projects the SAME solution content through a different lens.
A Story defined in HCD terms links to the UseCase that enables it and the
App that contains it. The viewpoints are interconnected, not siloed.

Two Documentation Modes
-----------------------
**Framework documentation** screams software engineering - its bounded
contexts ARE the viewpoints (HCD, C4, Core) because the framework's domain
is software engineering methodology.

**Solution documentation** screams its business domain - bounded contexts
like "Henchmen Management" or "Very Large Kites" appear at root level,
with viewpoints projecting their content through HCD/C4/Core lenses.

Hub Pages
---------
HCD entities form hub pages that link outward to related content:

- **Persona** → journeys they take, apps they use, stories about them
- **Journey** → steps, epics involved, personas taking them
- **Epic** → stories within, personas served, journeys containing
- **Story** → features, use cases enabling, apps containing
- **App** → features, accelerators powering, personas using
- **Accelerator** → use cases, entities, apps depending on it

Directives Provided
-------------------
Define directives: ``define-persona``, ``define-journey``, ``define-epic``,
``define-app``, ``define-accelerator``, ``define-integration``, ``define-contrib``

Index directives: ``persona-index``, ``journey-index``, ``epic-index``,
``story-index``, ``app-index``, ``accelerator-index``, ``integration-index``,
``contrib-index``

Relationship directives: ``journeys-for-persona``, ``epics-for-persona``,
``apps-for-persona``, ``stories``, ``accelerators-for-app``, etc.

Diagram directives: ``persona-diagram``, ``journey-dependency-graph``,
``accelerator-dependency-diagram``, ``entity-diagram``, ``c4-container-diagram``
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
        AcceleratorCodePlaceholder,
        AcceleratorDependencyDiagramDirective,
        AcceleratorDependencyDiagramPlaceholder,
        AcceleratorEntityListDirective,
        AcceleratorEntityListPlaceholder,
        AcceleratorListDirective,
        AcceleratorListPlaceholder,
        AcceleratorsForAppDirective,
        AcceleratorsForAppPlaceholder,
        AcceleratorStatusDirective,
        AcceleratorUseCaseListDirective,
        AcceleratorUseCaseListPlaceholder,
        AppListByInterfaceDirective,
        AppListByInterfacePlaceholder,
        AppsForPersonaDirective,
        AppsForPersonaPlaceholder,
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
        EntityDiagramDirective,
        EntityDiagramPlaceholder,
        EpicsForPersonaDirective,
        EpicsForPersonaPlaceholder,
        EpicStoryDirective,
        GherkinAppStoriesDirective,
        GherkinStoriesDirective,
        GherkinStoriesForAppDirective,
        GherkinStoriesForPersonaDirective,
        GherkinStoriesIndexDirective,
        GherkinStoryDirective,
        JourneyDependencyGraphDirective,
        JourneyDependencyGraphPlaceholder,
        JourneyIndexDirective,
        JourneysForPersonaDirective,
        ListAcceleratorCodeDirective,
        PersonaDiagramDirective,
        PersonaDiagramPlaceholder,
        PersonaIndexDiagramDirective,
        PersonaIndexDiagramPlaceholder,
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

    # Register epic directives (epic-index uses generated directive)
    from .generated_directives import GeneratedEpicIndexDirective

    app.add_directive("define-epic", DefineEpicDirective)
    app.add_directive("epic-story", EpicStoryDirective)
    app.add_directive("epic-index", GeneratedEpicIndexDirective)  # Using generated
    app.add_directive("epics-for-persona", EpicsForPersonaDirective)
    app.add_node(GeneratedEpicIndexDirective.placeholder_class)
    app.add_node(EpicsForPersonaPlaceholder)

    # Register app directives (app-index uses generated directive)
    from .generated_directives import GeneratedAppIndexDirective

    app.add_directive("define-app", DefineAppDirective)
    app.add_directive("app-index", GeneratedAppIndexDirective)  # Using generated
    app.add_directive("apps-for-persona", AppsForPersonaDirective)
    app.add_node(DefineAppPlaceholder)
    app.add_node(GeneratedAppIndexDirective.placeholder_class)
    app.add_node(AppsForPersonaPlaceholder)

    # Register accelerator directives (accelerator-index uses generated directive)
    from .generated_directives import GeneratedAcceleratorIndexDirective

    app.add_directive("define-accelerator", DefineAcceleratorDirective)
    app.add_directive("accelerator-index", GeneratedAcceleratorIndexDirective)  # Using generated
    app.add_directive("accelerators-for-app", AcceleratorsForAppDirective)
    app.add_directive("dependent-accelerators", DependentAcceleratorsDirective)
    app.add_directive(
        "accelerator-dependency-diagram", AcceleratorDependencyDiagramDirective
    )
    app.add_directive("accelerator-status", AcceleratorStatusDirective)
    app.add_node(DefineAcceleratorPlaceholder)
    app.add_node(GeneratedAcceleratorIndexDirective.placeholder_class)
    app.add_node(AcceleratorsForAppPlaceholder)
    app.add_node(DependentAcceleratorsPlaceholder)
    app.add_node(AcceleratorDependencyDiagramPlaceholder)

    # Register integration directives (integration-index uses generated directive)
    from .generated_directives import GeneratedIntegrationIndexDirective

    app.add_directive("define-integration", DefineIntegrationDirective)
    app.add_directive("integration-index", GeneratedIntegrationIndexDirective)  # Using generated
    app.add_node(DefineIntegrationPlaceholder)
    app.add_node(GeneratedIntegrationIndexDirective.placeholder_class)

    # Register persona directives
    from .generated_directives import GeneratedPersonaIndexDirective

    app.add_directive("define-persona", DefinePersonaDirective)
    app.add_directive("persona-index", GeneratedPersonaIndexDirective)  # Using generated
    app.add_directive("persona-diagram", PersonaDiagramDirective)
    app.add_directive("persona-index-diagram", PersonaIndexDiagramDirective)
    app.add_node(GeneratedPersonaIndexDirective.placeholder_class)
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

    # Register HCD cross-reference roles using documentation mapping
    from apps.sphinx.shared import make_anchor_role
    from apps.sphinx.shared.documentation_mapping import get_documentation_mapping
    from apps.sphinx.shared.roles import make_semantic_role
    from julee.hcd.entities.accelerator import Accelerator
    from julee.hcd.entities.epic import Epic
    from julee.hcd.entities.journey import Journey
    from julee.hcd.entities.persona import Persona
    from julee.hcd.entities.story import Story
    from julee.hcd.use_cases.crud import GetStoryRequest

    mapping = get_documentation_mapping()

    # Register Story anchor lookup (Story requires app context for lookup)
    def lookup_story(slug, sphinx_app):
        """Look up story and return (docname, anchor)."""
        try:
            hcd_ctx = get_hcd_context(sphinx_app)
            response = hcd_ctx.get_story.execute_sync(GetStoryRequest(slug=slug))
            if response.story:
                return (f"applications/{response.story.app_slug}", f"story-{slug}")
        except Exception:
            pass
        return None

    mapping.register_anchor(Story, lookup_story)

    # :persona:`slug` -> resolved via Persona's registered pattern
    PersonaRole = make_semantic_role(Persona, mapping)
    app.add_role("persona", PersonaRole())

    # :epic:`slug` -> resolved via Epic's registered pattern
    EpicRole = make_semantic_role(Epic, mapping)
    app.add_role("epic", EpicRole())

    # :journey:`slug` -> resolved via Journey's registered pattern
    JourneyRole = make_semantic_role(Journey, mapping)
    app.add_role("journey", JourneyRole())

    # :story:`slug` -> resolved via Story's registered anchor pattern
    StoryRole = make_anchor_role(lookup_story)
    app.add_role("story", StoryRole())

    # :accelerator:`slug` -> resolved via Accelerator's PROJECTS relation to BC
    AcceleratorRole = make_semantic_role(Accelerator, mapping)
    app.add_role("accelerator", AcceleratorRole())

    logger.info("Loaded apps.sphinx.hcd extensions")

    return {
        "version": "2.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _init_config_handler(app):
    """Initialize HCD config from Sphinx app config."""
    init_config(app)



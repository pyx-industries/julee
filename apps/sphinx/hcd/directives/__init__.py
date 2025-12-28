"""Sphinx directives for sphinx_hcd.

Thin directive adapters that use domain models and repositories.
"""

from .accelerator import (
    AcceleratorDependencyDiagramDirective,
    AcceleratorDependencyDiagramPlaceholder,
    AcceleratorsForAppDirective,
    AcceleratorsForAppPlaceholder,
    AcceleratorStatusDirective,
    DefineAcceleratorDirective,
    DefineAcceleratorPlaceholder,
    DependentAcceleratorsDirective,
    DependentAcceleratorsPlaceholder,
    clear_accelerator_state,
)
from .app import (
    AppsForPersonaDirective,
    AppsForPersonaPlaceholder,
    DefineAppDirective,
    DefineAppPlaceholder,
)
from .base import HCDDirective, make_deprecated_directive
from .c4_bridge import (
    AcceleratorListDirective,
    AcceleratorListPlaceholder,
    AppListByInterfaceDirective,
    AppListByInterfacePlaceholder,
    C4ContainerDiagramDirective,
    C4ContainerDiagramPlaceholder,
)
from .code_links import (
    AcceleratorCodePlaceholder,
    AcceleratorEntityListDirective,
    AcceleratorEntityListPlaceholder,
    AcceleratorUseCaseListDirective,
    AcceleratorUseCaseListPlaceholder,
    EntityDiagramDirective,
    EntityDiagramPlaceholder,
    ListAcceleratorCodeDirective,
)
from .contrib import (
    ContribIndexDirective,
    ContribIndexPlaceholder,
    ContribListDirective,
    ContribListPlaceholder,
    DefineContribDirective,
    DefineContribPlaceholder,
)
from .epic import (
    DefineEpicDirective,
    EpicsForPersonaDirective,
    EpicsForPersonaPlaceholder,
    EpicStoryDirective,
    clear_epic_state,
)
from .integration import (
    DefineIntegrationDirective,
    DefineIntegrationPlaceholder,
)
from .journey import (
    DefineJourneyDirective,
    JourneyDependencyGraphDirective,
    JourneyDependencyGraphPlaceholder,
    JourneyIndexDirective,
    JourneysForPersonaDirective,
    StepEpicDirective,
    StepPhaseDirective,
    StepStoryDirective,
    clear_journey_state,
    process_journey_steps,
)
from .persona import (
    DefinePersonaDirective,
    PersonaDiagramDirective,
    PersonaDiagramPlaceholder,
    PersonaIndexDiagramDirective,
    PersonaIndexDiagramPlaceholder,
)
from .story import (
    GherkinAppStoriesDirective,
    GherkinStoriesDirective,
    GherkinStoriesForAppDirective,
    GherkinStoriesForPersonaDirective,
    GherkinStoriesIndexDirective,
    GherkinStoryDirective,
    StoriesDirective,
    StoryAppDirective,
    StoryIndexDirective,
    StoryListForAppDirective,
    StoryListForPersonaDirective,
    StoryRefDirective,
    StorySeeAlsoPlaceholder,
    process_story_seealso_placeholders,
)

__all__ = [
    # Base
    "HCDDirective",
    "make_deprecated_directive",
    # Story directives
    "StoryAppDirective",
    "StoryListForPersonaDirective",
    "StoryListForAppDirective",
    "StoryIndexDirective",
    "StoriesDirective",
    "StoryRefDirective",
    "StorySeeAlsoPlaceholder",
    "process_story_seealso_placeholders",
    # Story deprecated aliases
    "GherkinStoryDirective",
    "GherkinStoriesDirective",
    "GherkinStoriesForPersonaDirective",
    "GherkinStoriesForAppDirective",
    "GherkinStoriesIndexDirective",
    "GherkinAppStoriesDirective",
    # Journey directives
    "DefineJourneyDirective",
    "StepStoryDirective",
    "StepEpicDirective",
    "StepPhaseDirective",
    "JourneyIndexDirective",
    "JourneyDependencyGraphDirective",
    "JourneyDependencyGraphPlaceholder",
    "JourneysForPersonaDirective",
    "clear_journey_state",
    "process_journey_steps",
    # Epic directives
    "DefineEpicDirective",
    "EpicStoryDirective",
    "EpicsForPersonaDirective",
    "EpicsForPersonaPlaceholder",
    "clear_epic_state",
    # App directives
    "DefineAppDirective",
    "DefineAppPlaceholder",
    "AppsForPersonaDirective",
    "AppsForPersonaPlaceholder",
    # Accelerator directives
    "DefineAcceleratorDirective",
    "DefineAcceleratorPlaceholder",
    "AcceleratorsForAppDirective",
    "AcceleratorsForAppPlaceholder",
    "DependentAcceleratorsDirective",
    "DependentAcceleratorsPlaceholder",
    "AcceleratorDependencyDiagramDirective",
    "AcceleratorDependencyDiagramPlaceholder",
    "AcceleratorStatusDirective",
    "clear_accelerator_state",
    # Integration directives
    "DefineIntegrationDirective",
    "DefineIntegrationPlaceholder",
    # Persona directives
    "DefinePersonaDirective",
    "PersonaDiagramDirective",
    "PersonaDiagramPlaceholder",
    "PersonaIndexDiagramDirective",
    "PersonaIndexDiagramPlaceholder",
    # C4 bridge directives
    "C4ContainerDiagramDirective",
    "C4ContainerDiagramPlaceholder",
    "AppListByInterfaceDirective",
    "AppListByInterfacePlaceholder",
    "AcceleratorListDirective",
    "AcceleratorListPlaceholder",
    # Contrib directives
    "DefineContribDirective",
    "DefineContribPlaceholder",
    "ContribIndexDirective",
    "ContribIndexPlaceholder",
    "ContribListDirective",
    "ContribListPlaceholder",
    # Code link directives
    "ListAcceleratorCodeDirective",
    "AcceleratorCodePlaceholder",
    # Entity diagram directives
    "EntityDiagramDirective",
    "EntityDiagramPlaceholder",
    # Accelerator entity/usecase list directives
    "AcceleratorEntityListDirective",
    "AcceleratorEntityListPlaceholder",
    "AcceleratorUseCaseListDirective",
    "AcceleratorUseCaseListPlaceholder",
]

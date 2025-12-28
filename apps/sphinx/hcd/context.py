"""HCDContext for unified repository access.

Provides a single context object that holds all repositories for the
HCD documentation system. This replaces the scattered global/env registries
with a unified, type-safe interface.

Use cases are exposed as properties for filtering operations:
    response = context.list_stories.execute_sync(ListStoriesRequest(app_slug="portal"))
    stories = response.stories
"""

import warnings
from typing import TYPE_CHECKING

from julee.hcd.infrastructure.repositories.memory.accelerator import (
    MemoryAcceleratorRepository,
)
from julee.hcd.infrastructure.repositories.memory.app import MemoryAppRepository
from julee.hcd.infrastructure.repositories.memory.code_info import (
    MemoryCodeInfoRepository,
)
from julee.hcd.infrastructure.repositories.memory.contrib import MemoryContribRepository
from julee.hcd.infrastructure.repositories.memory.epic import MemoryEpicRepository
from julee.hcd.infrastructure.repositories.memory.integration import (
    MemoryIntegrationRepository,
)
from julee.hcd.infrastructure.repositories.memory.journey import MemoryJourneyRepository
from julee.hcd.infrastructure.repositories.memory.persona import MemoryPersonaRepository
from julee.hcd.infrastructure.repositories.memory.story import MemoryStoryRepository
from julee.hcd.use_cases.crud import (
    # Create use cases
    CreateAppUseCase,
    CreateContribModuleUseCase,
    CreateIntegrationUseCase,
    CreateJourneyUseCase,
    CreateStoryUseCase,
    # Get use cases
    GetAcceleratorUseCase,
    GetAppUseCase,
    GetCodeInfoUseCase,
    GetContribModuleUseCase,
    GetEpicUseCase,
    GetIntegrationUseCase,
    GetJourneyUseCase,
    GetPersonaUseCase,
    GetStoryUseCase,
    # List use cases
    ListAcceleratorsUseCase,
    ListAppsUseCase,
    ListContribModulesUseCase,
    ListEpicsUseCase,
    ListIntegrationsUseCase,
    ListJourneysUseCase,
    ListPersonasUseCase,
    ListStoriesUseCase,
    # Save use cases (for import operations)
    SaveCodeInfoUseCase,
    # Update use cases
    UpdateAppUseCase,
)

from .adapters import SyncRepositoryAdapter
from .repositories import (
    SphinxEnvAcceleratorRepository,
    SphinxEnvAppRepository,
    SphinxEnvCodeInfoRepository,
    SphinxEnvContribRepository,
    SphinxEnvEpicRepository,
    SphinxEnvIntegrationRepository,
    SphinxEnvJourneyRepository,
    SphinxEnvPersonaRepository,
    SphinxEnvStoryRepository,
)

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment

    from julee.hcd.entities import (
        Accelerator,
        App,
        BoundedContextInfo,
        ContribModule,
        Epic,
        Integration,
        Journey,
        Persona,
        Story,
    )


def _deprecation_warning(repo_name: str) -> None:
    """Emit deprecation warning for direct repository access."""
    warnings.warn(
        f"Direct repository access via '{repo_name}' is deprecated. "
        f"Use the corresponding use case property instead (e.g., list_*, get_*, create_*).",
        DeprecationWarning,
        stacklevel=3,
    )


class HCDContext:
    """Unified context for HCD documentation.

    Holds all repositories needed for the HCD documentation system.
    Each repository is wrapped in a SyncRepositoryAdapter for use in
    Sphinx's synchronous directive system.

    This context is created at builder-inited and attached to the
    Sphinx app object. It can be retrieved using get_hcd_context().

    IMPORTANT: Direct repository access (e.g., context.story_repo) is deprecated.
    Use the corresponding use case properties instead:
    - list_stories, get_story, create_story (not story_repo)
    - list_apps, get_app, create_app, update_app (not app_repo)
    - etc.
    """

    def __init__(
        self,
        story_repo: "SyncRepositoryAdapter[Story] | None" = None,
        journey_repo: "SyncRepositoryAdapter[Journey] | None" = None,
        epic_repo: "SyncRepositoryAdapter[Epic] | None" = None,
        app_repo: "SyncRepositoryAdapter[App] | None" = None,
        accelerator_repo: "SyncRepositoryAdapter[Accelerator] | None" = None,
        integration_repo: "SyncRepositoryAdapter[Integration] | None" = None,
        contrib_repo: "SyncRepositoryAdapter[ContribModule] | None" = None,
        persona_repo: "SyncRepositoryAdapter[Persona] | None" = None,
        code_info_repo: "SyncRepositoryAdapter[BoundedContextInfo] | None" = None,
    ) -> None:
        """Initialize HCDContext with repositories.

        Args:
            story_repo: Story repository (defaults to memory)
            journey_repo: Journey repository (defaults to memory)
            epic_repo: Epic repository (defaults to memory)
            app_repo: App repository (defaults to memory)
            accelerator_repo: Accelerator repository (defaults to memory)
            integration_repo: Integration repository (defaults to memory)
            contrib_repo: ContribModule repository (defaults to memory)
            persona_repo: Persona repository (defaults to memory)
            code_info_repo: BoundedContextInfo repository (defaults to memory)
        """
        self._story_repo = story_repo or SyncRepositoryAdapter(MemoryStoryRepository())
        self._journey_repo = journey_repo or SyncRepositoryAdapter(MemoryJourneyRepository())
        self._epic_repo = epic_repo or SyncRepositoryAdapter(MemoryEpicRepository())
        self._app_repo = app_repo or SyncRepositoryAdapter(MemoryAppRepository())
        self._accelerator_repo = accelerator_repo or SyncRepositoryAdapter(MemoryAcceleratorRepository())
        self._integration_repo = integration_repo or SyncRepositoryAdapter(MemoryIntegrationRepository())
        self._contrib_repo = contrib_repo or SyncRepositoryAdapter(MemoryContribRepository())
        self._persona_repo = persona_repo or SyncRepositoryAdapter(MemoryPersonaRepository())
        self._code_info_repo = code_info_repo or SyncRepositoryAdapter(MemoryCodeInfoRepository())

    # =========================================================================
    # Deprecated repository accessors (emit warnings)
    # =========================================================================

    @property
    def story_repo(self) -> "SyncRepositoryAdapter[Story]":
        """DEPRECATED: Use list_stories, get_story, or create_story instead."""
        _deprecation_warning("story_repo")
        return self._story_repo

    @property
    def journey_repo(self) -> "SyncRepositoryAdapter[Journey]":
        """DEPRECATED: Use list_journeys, get_journey, or create_journey instead."""
        _deprecation_warning("journey_repo")
        return self._journey_repo

    @property
    def epic_repo(self) -> "SyncRepositoryAdapter[Epic]":
        """DEPRECATED: Use list_epics or get_epic instead."""
        _deprecation_warning("epic_repo")
        return self._epic_repo

    @property
    def app_repo(self) -> "SyncRepositoryAdapter[App]":
        """DEPRECATED: Use list_apps, get_app, create_app, or update_app instead."""
        _deprecation_warning("app_repo")
        return self._app_repo

    @property
    def accelerator_repo(self) -> "SyncRepositoryAdapter[Accelerator]":
        """DEPRECATED: Use list_accelerators or get_accelerator instead."""
        _deprecation_warning("accelerator_repo")
        return self._accelerator_repo

    @property
    def integration_repo(self) -> "SyncRepositoryAdapter[Integration]":
        """DEPRECATED: Use list_integrations, get_integration, or create_integration instead."""
        _deprecation_warning("integration_repo")
        return self._integration_repo

    @property
    def contrib_repo(self) -> "SyncRepositoryAdapter[ContribModule]":
        """DEPRECATED: Use list_contribs, get_contrib, or create_contrib instead."""
        _deprecation_warning("contrib_repo")
        return self._contrib_repo

    @property
    def persona_repo(self) -> "SyncRepositoryAdapter[Persona]":
        """DEPRECATED: Use list_personas or get_persona instead."""
        _deprecation_warning("persona_repo")
        return self._persona_repo

    @property
    def code_info_repo(self) -> "SyncRepositoryAdapter[BoundedContextInfo]":
        """DEPRECATED: Use get_code_info or save_code_info instead."""
        _deprecation_warning("code_info_repo")
        return self._code_info_repo

    # =========================================================================
    # List use cases
    # =========================================================================

    @property
    def list_stories(self) -> ListStoriesUseCase:
        """Get ListStoriesUseCase for filtered story queries."""
        return ListStoriesUseCase(self._story_repo.async_repo)  # type: ignore

    @property
    def list_journeys(self) -> ListJourneysUseCase:
        """Get ListJourneysUseCase for filtered journey queries."""
        return ListJourneysUseCase(self._journey_repo.async_repo)  # type: ignore

    @property
    def list_epics(self) -> ListEpicsUseCase:
        """Get ListEpicsUseCase for filtered epic queries."""
        return ListEpicsUseCase(self._epic_repo.async_repo)  # type: ignore

    @property
    def list_apps(self) -> ListAppsUseCase:
        """Get ListAppsUseCase for filtered app queries."""
        return ListAppsUseCase(self._app_repo.async_repo)  # type: ignore

    @property
    def list_accelerators(self) -> ListAcceleratorsUseCase:
        """Get ListAcceleratorsUseCase for filtered accelerator queries."""
        return ListAcceleratorsUseCase(self._accelerator_repo.async_repo)  # type: ignore

    @property
    def list_integrations(self) -> ListIntegrationsUseCase:
        """Get ListIntegrationsUseCase for integration queries."""
        return ListIntegrationsUseCase(self._integration_repo.async_repo)  # type: ignore

    @property
    def list_personas(self) -> ListPersonasUseCase:
        """Get ListPersonasUseCase for persona queries."""
        return ListPersonasUseCase(self._persona_repo.async_repo)  # type: ignore

    @property
    def list_contribs(self) -> ListContribModulesUseCase:
        """Get ListContribModulesUseCase for contrib module queries."""
        return ListContribModulesUseCase(self._contrib_repo.async_repo)  # type: ignore

    # =========================================================================
    # Get use cases for single entity retrieval
    # =========================================================================

    @property
    def get_story(self) -> GetStoryUseCase:
        """Get GetStoryUseCase for single story lookup."""
        return GetStoryUseCase(self._story_repo.async_repo)  # type: ignore

    @property
    def get_journey(self) -> GetJourneyUseCase:
        """Get GetJourneyUseCase for single journey lookup."""
        return GetJourneyUseCase(self._journey_repo.async_repo)  # type: ignore

    @property
    def get_epic(self) -> GetEpicUseCase:
        """Get GetEpicUseCase for single epic lookup."""
        return GetEpicUseCase(self._epic_repo.async_repo)  # type: ignore

    @property
    def get_app(self) -> GetAppUseCase:
        """Get GetAppUseCase for single app lookup."""
        return GetAppUseCase(self._app_repo.async_repo)  # type: ignore

    @property
    def get_accelerator(self) -> GetAcceleratorUseCase:
        """Get GetAcceleratorUseCase for single accelerator lookup."""
        return GetAcceleratorUseCase(self._accelerator_repo.async_repo)  # type: ignore

    @property
    def get_integration(self) -> GetIntegrationUseCase:
        """Get GetIntegrationUseCase for single integration lookup."""
        return GetIntegrationUseCase(self._integration_repo.async_repo)  # type: ignore

    @property
    def get_persona(self) -> GetPersonaUseCase:
        """Get GetPersonaUseCase for single persona lookup."""
        return GetPersonaUseCase(self._persona_repo.async_repo)  # type: ignore

    @property
    def get_contrib(self) -> GetContribModuleUseCase:
        """Get GetContribModuleUseCase for single contrib module lookup."""
        return GetContribModuleUseCase(self._contrib_repo.async_repo)  # type: ignore

    @property
    def get_code_info(self) -> GetCodeInfoUseCase:
        """Get GetCodeInfoUseCase for code introspection lookup."""
        return GetCodeInfoUseCase(self._code_info_repo.async_repo)  # type: ignore

    # =========================================================================
    # Create/Update use cases
    # =========================================================================

    @property
    def create_contrib(self) -> CreateContribModuleUseCase:
        """Get CreateContribModuleUseCase for creating contrib modules."""
        return CreateContribModuleUseCase(self._contrib_repo.async_repo)  # type: ignore

    @property
    def create_journey(self) -> CreateJourneyUseCase:
        """Get CreateJourneyUseCase for creating journeys."""
        return CreateJourneyUseCase(self._journey_repo.async_repo)  # type: ignore

    @property
    def create_app(self) -> CreateAppUseCase:
        """Get CreateAppUseCase for creating apps."""
        return CreateAppUseCase(self._app_repo.async_repo)  # type: ignore

    @property
    def update_app(self) -> UpdateAppUseCase:
        """Get UpdateAppUseCase for updating apps."""
        return UpdateAppUseCase(self._app_repo.async_repo)  # type: ignore

    @property
    def create_story(self) -> CreateStoryUseCase:
        """Get CreateStoryUseCase for creating stories."""
        return CreateStoryUseCase(self._story_repo.async_repo)  # type: ignore

    @property
    def create_integration(self) -> CreateIntegrationUseCase:
        """Get CreateIntegrationUseCase for creating integrations."""
        return CreateIntegrationUseCase(self._integration_repo.async_repo)  # type: ignore

    @property
    def save_code_info(self) -> SaveCodeInfoUseCase:
        """Get SaveCodeInfoUseCase for saving code info."""
        return SaveCodeInfoUseCase(self._code_info_repo.async_repo)  # type: ignore

    # =========================================================================
    # Utility methods
    # =========================================================================

    def clear_all(self) -> None:
        """Clear all repositories.

        Useful for testing or when rebuilding documentation from scratch.
        """
        self._story_repo.clear()
        self._journey_repo.clear()
        self._epic_repo.clear()
        self._app_repo.clear()
        self._accelerator_repo.clear()
        self._integration_repo.clear()
        self._contrib_repo.clear()
        self._persona_repo.clear()
        self._code_info_repo.clear()

    def clear_by_docname(self, docname: str) -> dict[str, int]:
        """Clear entities defined in a specific document.

        Used during incremental builds when a document is re-read.
        Only entities that track docname are cleared.

        Args:
            docname: RST document name

        Returns:
            Dict mapping entity type to number of entities removed
        """
        results = {}

        # Journey repo has clear_by_docname
        journey_async = self._journey_repo.async_repo
        results["journeys"] = self._journey_repo.run_async(
            journey_async.clear_by_docname(docname)  # type: ignore
        )

        # Epic repo has clear_by_docname
        epic_async = self._epic_repo.async_repo
        results["epics"] = self._epic_repo.run_async(
            epic_async.clear_by_docname(docname)  # type: ignore
        )

        # Accelerator repo has clear_by_docname
        accel_async = self._accelerator_repo.async_repo
        results["accelerators"] = self._accelerator_repo.run_async(
            accel_async.clear_by_docname(docname)  # type: ignore
        )

        # Contrib repo has clear_by_docname
        contrib_async = self._contrib_repo.async_repo
        results["contrib"] = self._contrib_repo.run_async(
            contrib_async.clear_by_docname(docname)  # type: ignore
        )

        return results


def get_hcd_context(app) -> HCDContext:
    """Get the HCDContext from a Sphinx app.

    Args:
        app: Sphinx application object

    Returns:
        HCDContext attached to the app

    Raises:
        AttributeError: If context hasn't been initialized
    """
    return app._hcd_context


def set_hcd_context(app, context: HCDContext) -> None:
    """Set the HCDContext on a Sphinx app.

    Args:
        app: Sphinx application object
        context: HCDContext to attach
    """
    app._hcd_context = context


def ensure_hcd_context(app) -> HCDContext:
    """Ensure the HCDContext exists on a Sphinx app.

    Creates a new context if one doesn't exist. Uses the configured
    repository backend (memory or rst).

    Args:
        app: Sphinx application object

    Returns:
        HCDContext attached to the app
    """
    if not hasattr(app, "_hcd_context"):
        context = _create_context(app)
        set_hcd_context(app, context)
    return get_hcd_context(app)


def _create_context(app) -> HCDContext:
    """Create an HCDContext with the configured backend.

    Uses SphinxEnv repositories by default for parallel-safe builds.
    Data is stored in app.env.hcd_storage which is properly pickled
    between worker processes.

    Args:
        app: Sphinx application object

    Returns:
        HCDContext with appropriate repositories
    """
    from .config import get_config

    try:
        config = get_config()
    except RuntimeError:
        # Config not initialized yet, use SphinxEnv repos with app.env
        return create_sphinx_env_context(app.env)

    if config.use_rst_backend:
        return _create_rst_context(config)

    # Default: use SphinxEnv repos for parallel-safe builds
    return create_sphinx_env_context(app.env)


def _create_rst_context(config) -> HCDContext:
    """Create an HCDContext with RST file-backed repositories.

    Args:
        config: HCDConfig instance

    Returns:
        HCDContext with RST repositories
    """
    from julee.hcd.infrastructure.repositories.rst import (
        RstAcceleratorRepository,
        RstAppRepository,
        RstEpicRepository,
        RstIntegrationRepository,
        RstJourneyRepository,
        RstPersonaRepository,
        RstStoryRepository,
    )

    return HCDContext(
        story_repo=SyncRepositoryAdapter(
            RstStoryRepository(config.get_rst_dir("stories"))
        ),
        journey_repo=SyncRepositoryAdapter(
            RstJourneyRepository(config.get_rst_dir("journeys"))
        ),
        epic_repo=SyncRepositoryAdapter(RstEpicRepository(config.get_rst_dir("epics"))),
        app_repo=SyncRepositoryAdapter(
            RstAppRepository(config.get_rst_dir("applications"))
        ),
        accelerator_repo=SyncRepositoryAdapter(
            RstAcceleratorRepository(config.get_rst_dir("accelerators"))
        ),
        integration_repo=SyncRepositoryAdapter(
            RstIntegrationRepository(config.get_rst_dir("integrations"))
        ),
        persona_repo=SyncRepositoryAdapter(
            RstPersonaRepository(config.get_rst_dir("personas"))
        ),
        # Code info stays in memory (not stored in RST)
        code_info_repo=SyncRepositoryAdapter(MemoryCodeInfoRepository()),
    )


def create_sphinx_env_context(env: "BuildEnvironment") -> HCDContext:
    """Create an HCDContext with Sphinx env-backed repositories.

    This creates repositories that store data in env.hcd_storage, which is
    properly pickled between worker processes during parallel builds and
    merged back via the env-merge-info event.

    Args:
        env: Sphinx BuildEnvironment

    Returns:
        HCDContext with SphinxEnv repositories
    """
    return HCDContext(
        story_repo=SyncRepositoryAdapter(SphinxEnvStoryRepository(env)),
        journey_repo=SyncRepositoryAdapter(SphinxEnvJourneyRepository(env)),
        epic_repo=SyncRepositoryAdapter(SphinxEnvEpicRepository(env)),
        app_repo=SyncRepositoryAdapter(SphinxEnvAppRepository(env)),
        accelerator_repo=SyncRepositoryAdapter(SphinxEnvAcceleratorRepository(env)),
        integration_repo=SyncRepositoryAdapter(SphinxEnvIntegrationRepository(env)),
        contrib_repo=SyncRepositoryAdapter(SphinxEnvContribRepository(env)),
        persona_repo=SyncRepositoryAdapter(SphinxEnvPersonaRepository(env)),
        code_info_repo=SyncRepositoryAdapter(SphinxEnvCodeInfoRepository(env)),
    )

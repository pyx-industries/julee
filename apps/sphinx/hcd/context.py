"""HCDContext for unified repository access.

Provides a single context object that holds all repositories for the
HCD documentation system. This replaces the scattered global/env registries
with a unified, type-safe interface.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from julee.hcd.repositories.memory import (
    MemoryAcceleratorRepository,
    MemoryAppRepository,
    MemoryCodeInfoRepository,
    MemoryContribRepository,
    MemoryEpicRepository,
    MemoryIntegrationRepository,
    MemoryJourneyRepository,
    MemoryPersonaRepository,
    MemoryStoryRepository,
)
from .adapters import SyncRepositoryAdapter

if TYPE_CHECKING:
    from julee.hcd.domain.models import (
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


@dataclass
class HCDContext:
    """Unified context for HCD documentation.

    Holds all repositories needed for the HCD documentation system.
    Each repository is wrapped in a SyncRepositoryAdapter for use in
    Sphinx's synchronous directive system.

    This context is created at builder-inited and attached to the
    Sphinx app object. It can be retrieved using get_hcd_context().
    """

    story_repo: SyncRepositoryAdapter["Story"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryStoryRepository())
    )
    journey_repo: SyncRepositoryAdapter["Journey"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryJourneyRepository())
    )
    epic_repo: SyncRepositoryAdapter["Epic"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryEpicRepository())
    )
    app_repo: SyncRepositoryAdapter["App"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryAppRepository())
    )
    accelerator_repo: SyncRepositoryAdapter["Accelerator"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryAcceleratorRepository())
    )
    integration_repo: SyncRepositoryAdapter["Integration"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryIntegrationRepository())
    )
    contrib_repo: SyncRepositoryAdapter["ContribModule"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryContribRepository())
    )
    persona_repo: SyncRepositoryAdapter["Persona"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryPersonaRepository())
    )
    code_info_repo: SyncRepositoryAdapter["BoundedContextInfo"] = field(
        default_factory=lambda: SyncRepositoryAdapter(MemoryCodeInfoRepository())
    )

    def clear_all(self) -> None:
        """Clear all repositories.

        Useful for testing or when rebuilding documentation from scratch.
        """
        self.story_repo.clear()
        self.journey_repo.clear()
        self.epic_repo.clear()
        self.app_repo.clear()
        self.accelerator_repo.clear()
        self.integration_repo.clear()
        self.contrib_repo.clear()
        self.persona_repo.clear()
        self.code_info_repo.clear()

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
        journey_async = self.journey_repo.async_repo
        results["journeys"] = self.journey_repo.run_async(
            journey_async.clear_by_docname(docname)  # type: ignore
        )

        # Epic repo has clear_by_docname
        epic_async = self.epic_repo.async_repo
        results["epics"] = self.epic_repo.run_async(
            epic_async.clear_by_docname(docname)  # type: ignore
        )

        # Accelerator repo has clear_by_docname
        accel_async = self.accelerator_repo.async_repo
        results["accelerators"] = self.accelerator_repo.run_async(
            accel_async.clear_by_docname(docname)  # type: ignore
        )

        # Contrib repo has clear_by_docname
        contrib_async = self.contrib_repo.async_repo
        results["contrib"] = self.contrib_repo.run_async(
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

    Args:
        app: Sphinx application object

    Returns:
        HCDContext with appropriate repositories
    """
    from .config import get_config

    try:
        config = get_config()
    except RuntimeError:
        # Config not initialized yet, use defaults
        return HCDContext()

    if config.use_rst_backend:
        return _create_rst_context(config)

    return HCDContext()


def _create_rst_context(config) -> HCDContext:
    """Create an HCDContext with RST file-backed repositories.

    Args:
        config: HCDConfig instance

    Returns:
        HCDContext with RST repositories
    """
    from julee.hcd.repositories.rst import (
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

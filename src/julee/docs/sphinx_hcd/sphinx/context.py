"""HCDContext for unified repository access.

Provides a single context object that holds all repositories for the
HCD documentation system. This replaces the scattered global/env registries
with a unified, type-safe interface.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..domain.repositories import (
    AcceleratorRepository,
    EpicRepository,
    JourneyRepository,
)
from ..repositories.memory import (
    MemoryAcceleratorRepository,
    MemoryAppRepository,
    MemoryCodeInfoRepository,
    MemoryEpicRepository,
    MemoryIntegrationRepository,
    MemoryJourneyRepository,
    MemoryStoryRepository,
)
from .adapters import SyncRepositoryAdapter

if TYPE_CHECKING:
    from ..domain.models import (
        Accelerator,
        App,
        BoundedContextInfo,
        Epic,
        Integration,
        Journey,
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
        self.code_info_repo.clear()

    def clear_by_docname(self, docname: str) -> dict[str, int]:
        """Clear entities defined in a specific document.

        Used during incremental builds when a document is re-read.
        Only entities that track docname are cleared (journey, epic, accelerator).

        Args:
            docname: RST document name

        Returns:
            Dict mapping entity type to number of entities removed
        """
        results = {}

        # Journey repo has clear_by_docname
        journey_async = self.journey_repo.async_repo
        assert isinstance(journey_async, JourneyRepository)
        results["journeys"] = self.journey_repo.run_async(
            journey_async.clear_by_docname(docname)
        )

        # Epic repo has clear_by_docname
        epic_async = self.epic_repo.async_repo
        assert isinstance(epic_async, EpicRepository)
        results["epics"] = self.epic_repo.run_async(
            epic_async.clear_by_docname(docname)
        )

        # Accelerator repo has clear_by_docname
        accel_async = self.accelerator_repo.async_repo
        assert isinstance(accel_async, AcceleratorRepository)
        results["accelerators"] = self.accelerator_repo.run_async(
            accel_async.clear_by_docname(docname)
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
    context: HCDContext = app._hcd_context
    return context


def set_hcd_context(app, context: HCDContext) -> None:
    """Set the HCDContext on a Sphinx app.

    Args:
        app: Sphinx application object
        context: HCDContext to attach
    """
    app._hcd_context = context


def ensure_hcd_context(app) -> HCDContext:
    """Ensure the HCDContext exists on a Sphinx app.

    Creates a new context if one doesn't exist.

    Args:
        app: Sphinx application object

    Returns:
        HCDContext attached to the app
    """
    if not hasattr(app, "_hcd_context"):
        set_hcd_context(app, HCDContext())
    return get_hcd_context(app)

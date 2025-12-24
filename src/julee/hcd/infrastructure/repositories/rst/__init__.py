"""RST file-backed repository implementations.

Provides repository implementations that use RST files as a database backend.
Supports lossless round-trip: RST → Domain Entity → RST.

Usage:
    from pathlib import Path
    from julee.hcd.infrastructure.repositories.rst import create_rst_repositories

    repos = create_rst_repositories(Path("docs/hcd"))
    journeys = await repos["journey"].list_all()
"""

from pathlib import Path
from typing import Any

from .accelerator import RstAcceleratorRepository
from .app import RstAppRepository
from .epic import RstEpicRepository
from .integration import RstIntegrationRepository
from .journey import RstJourneyRepository
from .persona import RstPersonaRepository
from .story import RstStoryRepository

__all__ = [
    # Repositories
    "RstAcceleratorRepository",
    "RstAppRepository",
    "RstEpicRepository",
    "RstIntegrationRepository",
    "RstJourneyRepository",
    "RstPersonaRepository",
    "RstStoryRepository",
    # Factory
    "create_rst_repositories",
]


def create_rst_repositories(docs_dir: Path) -> dict[str, Any]:
    """Create all RST repositories for a docs directory.

    Creates repositories for each entity type, using standard directory
    structure conventions:
    - stories/       -> StoryRepository
    - journeys/      -> JourneyRepository
    - epics/         -> EpicRepository
    - accelerators/  -> AcceleratorRepository
    - personas/      -> PersonaRepository
    - applications/  -> AppRepository
    - integrations/  -> IntegrationRepository

    Args:
        docs_dir: Root directory for HCD documentation

    Returns:
        Dict mapping entity type names to repository instances
    """
    return {
        "story": RstStoryRepository(docs_dir / "stories"),
        "journey": RstJourneyRepository(docs_dir / "journeys"),
        "epic": RstEpicRepository(docs_dir / "epics"),
        "accelerator": RstAcceleratorRepository(docs_dir / "accelerators"),
        "persona": RstPersonaRepository(docs_dir / "personas"),
        "app": RstAppRepository(docs_dir / "applications"),
        "integration": RstIntegrationRepository(docs_dir / "integrations"),
    }

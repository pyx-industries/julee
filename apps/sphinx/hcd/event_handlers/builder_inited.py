"""Builder-inited event handler for sphinx_hcd.

Initializes HCD context and scans source files at build start.
"""

from sphinx.util import logging

from ..initialization import initialize_hcd_context

logger = logging.getLogger(__name__)


def on_builder_inited(app):
    """Initialize HCD context when builder is initialized.

    This handler:
    1. Creates the HCDContext with all repositories
    2. Scans feature files for stories
    3. Scans app manifests
    4. Scans integration manifests
    5. Scans bounded contexts for code info
    6. Initializes SemanticRelationRegistry with entity types

    Args:
        app: Sphinx application instance
    """
    logger.info("Initializing HCD context...")

    # Initialize the HCD context (creates repos, scans files)
    initialize_hcd_context(app)

    # Initialize SemanticRelationRegistry for unified links
    _initialize_semantic_registry(app)

    logger.info("HCD context initialized")


def _initialize_semantic_registry(app):
    """Initialize the SemanticRelationRegistry with all entity types.

    Registers entity types that have semantic relations for bidirectional
    documentation cross-references.

    Args:
        app: Sphinx application instance
    """
    from julee.core.services.semantic_relation_registry import SemanticRelationRegistry

    registry = SemanticRelationRegistry()

    # Register HCD entities with semantic relations
    from julee.hcd.entities.app import App
    from julee.hcd.entities.epic import Epic
    from julee.hcd.entities.integration import Integration
    from julee.hcd.entities.journey import Journey
    from julee.hcd.entities.persona import Persona
    from julee.hcd.entities.story import Story

    registry.register(App)
    registry.register(Epic)
    registry.register(Integration)
    registry.register(Journey)
    registry.register(Persona)
    registry.register(Story)

    # Register Supply Chain entities
    from julee.supply_chain.entities.accelerator import Accelerator

    registry.register(Accelerator)

    # Store registry on app for use by UnifiedLinkResolver
    app._semantic_relation_registry = registry

    logger.debug(
        f"Registered {len(registry)} entity types with semantic relations"
    )

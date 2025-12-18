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

    Args:
        app: Sphinx application instance
    """
    logger.info("Initializing HCD context...")

    # Initialize the HCD context (creates repos, scans files)
    initialize_hcd_context(app)

    logger.info("HCD context initialized")

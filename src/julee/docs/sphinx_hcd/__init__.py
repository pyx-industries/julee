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

from .config import config_factory, init_config

logger = logging.getLogger(__name__)


def setup(app):
    """Set up all HCD extensions for Sphinx."""
    # Register configuration value first
    app.add_config_value("sphinx_hcd", {}, "env")

    # Initialize config when builder starts (after conf.py is loaded)
    app.connect("builder-inited", _init_config_handler, priority=0)

    # Import and setup each extension module
    from . import accelerators, apps, epics, integrations, journeys, personas, stories

    # Call setup on each module
    stories.setup(app)
    journeys.setup(app)
    epics.setup(app)
    apps.setup(app)
    accelerators.setup(app)
    integrations.setup(app)
    personas.setup(app)

    logger.info("Loaded julee.docs.sphinx_hcd extensions")

    return {
        "version": "1.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }


def _init_config_handler(app):
    """Initialize HCD config from Sphinx app config."""
    init_config(app)

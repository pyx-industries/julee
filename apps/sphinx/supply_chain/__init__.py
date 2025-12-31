"""Sphinx Supply Chain Extension.

Provides Sphinx directives for documenting supply chain concepts:
- Accelerators (business process collections)
- Future: Credentials, Product Passports, Trust Graphs

This extension is part of the supply_chain bounded context which models
business processes as supply chains with provenance tracking.
"""

from sphinx.util import logging

logger = logging.getLogger(__name__)


def setup(app):
    """Set up supply chain extension for Sphinx."""
    from .directives.accelerator import (
        AcceleratorDependencyDiagramDirective,
        AcceleratorDependencyDiagramPlaceholder,
        AcceleratorStatusDirective,
        AcceleratorsForAppDirective,
        AcceleratorsForAppPlaceholder,
        DefineAcceleratorDirective,
        DefineAcceleratorPlaceholder,
        DependentAcceleratorsDirective,
        DependentAcceleratorsPlaceholder,
    )
    from .directives.code_links import (
        AcceleratorCodePlaceholder,
        AcceleratorEntityListDirective,
        AcceleratorEntityListPlaceholder,
        AcceleratorUseCaseListDirective,
        AcceleratorUseCaseListPlaceholder,
        EntityDiagramDirective,
        EntityDiagramPlaceholder,
        ListAcceleratorCodeDirective,
    )
    from .event_handlers import (
        on_doctree_resolved,
        on_env_merge_info,
        on_env_purge_doc,
    )
    from .generated_directives import (
        GeneratedAcceleratorIndexDirective,
        GeneratedAcceleratorIndexPlaceholder,
    )

    # Register accelerator directives
    app.add_directive("define-accelerator", DefineAcceleratorDirective)
    app.add_directive("accelerators-for-app", AcceleratorsForAppDirective)
    app.add_directive("dependent-accelerators", DependentAcceleratorsDirective)
    app.add_directive(
        "accelerator-dependency-diagram", AcceleratorDependencyDiagramDirective
    )
    app.add_directive("accelerator-status", AcceleratorStatusDirective)
    app.add_directive("accelerator-index", GeneratedAcceleratorIndexDirective)

    # Register code links directives
    app.add_directive("list-accelerator-code", ListAcceleratorCodeDirective)
    app.add_directive("accelerator-entity-list", AcceleratorEntityListDirective)
    app.add_directive("accelerator-usecase-list", AcceleratorUseCaseListDirective)
    app.add_directive("entity-diagram", EntityDiagramDirective)

    # Register placeholder nodes
    app.add_node(DefineAcceleratorPlaceholder)
    app.add_node(AcceleratorsForAppPlaceholder)
    app.add_node(DependentAcceleratorsPlaceholder)
    app.add_node(AcceleratorDependencyDiagramPlaceholder)
    app.add_node(GeneratedAcceleratorIndexPlaceholder)
    app.add_node(AcceleratorCodePlaceholder)
    app.add_node(AcceleratorEntityListPlaceholder)
    app.add_node(AcceleratorUseCaseListPlaceholder)
    app.add_node(EntityDiagramPlaceholder)

    # Connect event handlers
    app.connect("doctree-resolved", on_doctree_resolved)
    app.connect("env-merge-info", on_env_merge_info)
    app.connect("env-purge-doc", on_env_purge_doc)

    logger.info("Loaded apps.sphinx.supply_chain extension")

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

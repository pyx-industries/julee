"""Combined FastAPI application for all Julee accelerators."""

from fastapi import FastAPI

app = FastAPI(
    title="Julee API",
    description="Unified API for CEAP, HCD, and C4 accelerators",
    version="2.0.0",
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from .ceap.routers import (
        assembly_specifications,
        documents,
        knowledge_service_configs,
        knowledge_service_queries,
    )
    from .hcd.routers import (
        accelerators as hcd_accelerators,
        apps as hcd_apps,
        epics as hcd_epics,
        integrations as hcd_integrations,
        journeys as hcd_journeys,
        personas as hcd_personas,
        stories as hcd_stories,
    )
    from .c4.routers import (
        components as c4_components,
        containers as c4_containers,
        deployment_nodes as c4_deployment_nodes,
        diagrams as c4_diagrams,
        dynamic_steps as c4_dynamic_steps,
        relationships as c4_relationships,
        software_systems as c4_software_systems,
    )

    # CEAP routers
    app.include_router(
        documents.router, prefix="/ceap/documents", tags=["CEAP - Documents"]
    )
    app.include_router(
        assembly_specifications.router,
        prefix="/ceap/assembly-specifications",
        tags=["CEAP - Assembly Specifications"],
    )
    app.include_router(
        knowledge_service_configs.router,
        prefix="/ceap/knowledge-service-configs",
        tags=["CEAP - Knowledge Service Configs"],
    )
    app.include_router(
        knowledge_service_queries.router,
        prefix="/ceap/knowledge-service-queries",
        tags=["CEAP - Knowledge Service Queries"],
    )

    # HCD routers
    app.include_router(
        hcd_stories.router, prefix="/hcd/stories", tags=["HCD - Stories"]
    )
    app.include_router(hcd_epics.router, prefix="/hcd/epics", tags=["HCD - Epics"])
    app.include_router(
        hcd_journeys.router, prefix="/hcd/journeys", tags=["HCD - Journeys"]
    )
    app.include_router(
        hcd_personas.router, prefix="/hcd/personas", tags=["HCD - Personas"]
    )
    app.include_router(hcd_apps.router, prefix="/hcd/apps", tags=["HCD - Apps"])
    app.include_router(
        hcd_integrations.router, prefix="/hcd/integrations", tags=["HCD - Integrations"]
    )
    app.include_router(
        hcd_accelerators.router,
        prefix="/hcd/accelerators",
        tags=["HCD - Accelerators"],
    )

    # C4 routers
    app.include_router(
        c4_software_systems.router,
        prefix="/c4/software-systems",
        tags=["C4 - Software Systems"],
    )
    app.include_router(
        c4_containers.router, prefix="/c4/containers", tags=["C4 - Containers"]
    )
    app.include_router(
        c4_components.router, prefix="/c4/components", tags=["C4 - Components"]
    )
    app.include_router(
        c4_relationships.router,
        prefix="/c4/relationships",
        tags=["C4 - Relationships"],
    )
    app.include_router(
        c4_deployment_nodes.router,
        prefix="/c4/deployment-nodes",
        tags=["C4 - Deployment Nodes"],
    )
    app.include_router(
        c4_dynamic_steps.router,
        prefix="/c4/dynamic-steps",
        tags=["C4 - Dynamic Steps"],
    )
    app.include_router(
        c4_diagrams.router, prefix="/c4/diagrams", tags=["C4 - Diagrams"]
    )

    return app


# Create the app instance
app = create_app()

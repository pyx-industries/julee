"""Combined FastAPI application for all Julee accelerators."""

from fastapi import FastAPI

#: The main FastAPI application instance
julee_app = FastAPI(
    title="Julee API",
    description="Unified API for CEAP, HCD, and C4 accelerators",
    version="2.0.0",
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from .c4.routers import (
        components as c4_components,
    )
    from .c4.routers import (
        containers as c4_containers,
    )
    from .c4.routers import (
        deployment_nodes as c4_deployment_nodes,
    )
    from .c4.routers import (
        diagrams as c4_diagrams,
    )
    from .c4.routers import (
        dynamic_steps as c4_dynamic_steps,
    )
    from .c4.routers import (
        relationships as c4_relationships,
    )
    from .c4.routers import (
        software_systems as c4_software_systems,
    )
    from .ceap.routers import (
        assembly_specifications,
        documents,
        knowledge_service_configs,
        knowledge_service_queries,
    )
    from .hcd.routers import (
        accelerators as hcd_accelerators,
    )
    from .hcd.routers import (
        apps as hcd_apps,
    )
    from .hcd.routers import (
        epics as hcd_epics,
    )
    from .hcd.routers import (
        integrations as hcd_integrations,
    )
    from .hcd.routers import (
        journeys as hcd_journeys,
    )
    from .hcd.routers import (
        personas as hcd_personas,
    )
    from .hcd.routers import (
        stories as hcd_stories,
    )

    # CEAP routers
    julee_app.include_router(
        documents.router, prefix="/ceap/documents", tags=["CEAP - Documents"]
    )
    julee_app.include_router(
        assembly_specifications.router,
        prefix="/ceap/assembly-specifications",
        tags=["CEAP - Assembly Specifications"],
    )
    julee_app.include_router(
        knowledge_service_configs.router,
        prefix="/ceap/knowledge-service-configs",
        tags=["CEAP - Knowledge Service Configs"],
    )
    julee_app.include_router(
        knowledge_service_queries.router,
        prefix="/ceap/knowledge-service-queries",
        tags=["CEAP - Knowledge Service Queries"],
    )

    # HCD routers
    julee_app.include_router(
        hcd_stories.router, prefix="/hcd/stories", tags=["HCD - Stories"]
    )
    julee_app.include_router(hcd_epics.router, prefix="/hcd/epics", tags=["HCD - Epics"])
    julee_app.include_router(
        hcd_journeys.router, prefix="/hcd/journeys", tags=["HCD - Journeys"]
    )
    julee_app.include_router(
        hcd_personas.router, prefix="/hcd/personas", tags=["HCD - Personas"]
    )
    julee_app.include_router(hcd_apps.router, prefix="/hcd/apps", tags=["HCD - Apps"])
    julee_app.include_router(
        hcd_integrations.router, prefix="/hcd/integrations", tags=["HCD - Integrations"]
    )
    julee_app.include_router(
        hcd_accelerators.router,
        prefix="/hcd/accelerators",
        tags=["HCD - Accelerators"],
    )

    # C4 routers
    julee_app.include_router(
        c4_software_systems.router,
        prefix="/c4/software-systems",
        tags=["C4 - Software Systems"],
    )
    julee_app.include_router(
        c4_containers.router, prefix="/c4/containers", tags=["C4 - Containers"]
    )
    julee_app.include_router(
        c4_components.router, prefix="/c4/components", tags=["C4 - Components"]
    )
    julee_app.include_router(
        c4_relationships.router,
        prefix="/c4/relationships",
        tags=["C4 - Relationships"],
    )
    julee_app.include_router(
        c4_deployment_nodes.router,
        prefix="/c4/deployment-nodes",
        tags=["C4 - Deployment Nodes"],
    )
    julee_app.include_router(
        c4_dynamic_steps.router,
        prefix="/c4/dynamic-steps",
        tags=["C4 - Dynamic Steps"],
    )
    julee_app.include_router(
        c4_diagrams.router, prefix="/c4/diagrams", tags=["C4 - Diagrams"]
    )

    return julee_app


# Configure routers on the app instance
create_app()

"""CEAP API routers - imports from BC.

This thin composition layer imports routers from the bounded context.
"""

from julee.contrib.ceap.apps.api.routers.assembly_specifications import (
    router as assembly_specifications_router,
)
from julee.contrib.ceap.apps.api.routers.documents import (
    router as documents_router,
)
from julee.contrib.ceap.apps.api.routers.knowledge_service_configs import (
    router as knowledge_service_configs_router,
)
from julee.contrib.ceap.apps.api.routers.knowledge_service_queries import (
    router as knowledge_service_queries_router,
)
from julee.contrib.ceap.apps.api.routers.system import router as system_router
from julee.contrib.ceap.apps.api.routers.workflows import router as workflows_router

__all__ = [
    "knowledge_service_queries_router",
    "knowledge_service_configs_router",
    "assembly_specifications_router",
    "documents_router",
    "workflows_router",
    "system_router",
]

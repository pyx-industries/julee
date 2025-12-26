"""Knowledge Service Configs API router."""

import logging
from typing import cast

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate

from julee.contrib.ceap.apps.api.dependencies import (
    get_knowledge_service_config_repository,
)
from julee.contrib.ceap.entities.knowledge_service_config import (
    KnowledgeServiceConfig,
)
from julee.contrib.ceap.repositories.knowledge_service_config import (
    KnowledgeServiceConfigRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=Page[KnowledgeServiceConfig])
async def list_knowledge_service_configs(
    repository: KnowledgeServiceConfigRepository = Depends(
        get_knowledge_service_config_repository
    ),
) -> Page[KnowledgeServiceConfig]:
    """List all knowledge service configurations with pagination."""
    configs = await repository.list_all()
    return cast(Page[KnowledgeServiceConfig], paginate(configs))

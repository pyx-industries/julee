"""Knowledge Service Configs API router."""

import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException
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
    try:
        configs = await repository.list_all()
        return cast(Page[KnowledgeServiceConfig], paginate(configs))
    except Exception as e:
        logger.error("Failed to list knowledge service configs: %s", e)
        raise HTTPException(status_code=500, detail="Internal error") from e

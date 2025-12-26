"""Knowledge Service Queries API router."""

import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page, paginate

from julee.contrib.ceap.apps.api.dependencies import (
    get_knowledge_service_query_repository,
)
from julee.contrib.ceap.entities import KnowledgeServiceQuery
from julee.contrib.ceap.repositories.knowledge_service_query import (
    KnowledgeServiceQueryRepository,
)
from julee.contrib.ceap.use_cases.crud import (
    CreateKnowledgeServiceQueryRequest,
    CreateKnowledgeServiceQueryUseCase,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=Page[KnowledgeServiceQuery])
async def list_knowledge_service_queries(
    ids: str | None = Query(
        None,
        description="Comma-separated list of query IDs for bulk retrieval",
    ),
    repository: KnowledgeServiceQueryRepository = Depends(
        get_knowledge_service_query_repository
    ),
) -> Page[KnowledgeServiceQuery]:
    """List queries or bulk retrieve by IDs."""
    if ids is not None:
        if not ids.strip():
            raise HTTPException(status_code=400, detail="Invalid ids parameter")

        id_list = [id.strip() for id in ids.split(",") if id.strip()]
        if not id_list:
            raise HTTPException(status_code=400, detail="Invalid ids parameter")
        if len(id_list) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 IDs per request")

        results = await repository.get_many(id_list)
        found_queries = [q for q in results.values() if q is not None]
        return cast(Page[KnowledgeServiceQuery], paginate(found_queries))

    queries = await repository.list_all()
    return cast(Page[KnowledgeServiceQuery], paginate(queries))


@router.get("/{query_id}", response_model=KnowledgeServiceQuery)
async def get_knowledge_service_query(
    query_id: str,
    repository: KnowledgeServiceQueryRepository = Depends(
        get_knowledge_service_query_repository
    ),
) -> KnowledgeServiceQuery:
    """Get a specific knowledge service query by ID."""
    query = await repository.get(query_id)
    if query is None:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge service query '{query_id}' not found",
        )
    return query


@router.post("/", response_model=KnowledgeServiceQuery)
async def create_knowledge_service_query(
    request: CreateKnowledgeServiceQueryRequest,
    repository: KnowledgeServiceQueryRepository = Depends(
        get_knowledge_service_query_repository
    ),
) -> KnowledgeServiceQuery:
    """Create a new knowledge service query."""
    use_case = CreateKnowledgeServiceQueryUseCase(repository)
    response = await use_case.execute(request)
    return response.entity

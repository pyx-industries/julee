"""Documents API router."""

import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import Response
from fastapi_pagination import Page, paginate

from julee.contrib.ceap.apps.api.dependencies import get_document_repository
from julee.contrib.ceap.entities.document import Document
from julee.contrib.ceap.repositories.document import DocumentRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=Page[Document])
async def list_documents(
    repository: DocumentRepository = Depends(get_document_repository),
) -> Page[Document]:
    """List all documents with pagination."""
    documents = await repository.list_all()
    return cast(Page[Document], paginate(documents))


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str = Path(..., description="Document ID"),
    repository: DocumentRepository = Depends(get_document_repository),
) -> Document:
    """Get document metadata by ID."""
    document = await repository.get(document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found",
        )
    return document


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str = Path(..., description="Document ID"),
    repository: DocumentRepository = Depends(get_document_repository),
) -> Response:
    """Get document content by ID."""
    document = await repository.get(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found",
        )

    if not document.content:
        raise HTTPException(
            status_code=422,
            detail=f"Document '{document_id}' has no content",
        )

    content_bytes = document.content.read()
    return Response(
        content=content_bytes,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'inline; filename="{document.original_filename}"'
        },
    )

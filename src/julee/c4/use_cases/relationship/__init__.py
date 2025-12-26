"""Relationship use-cases.

CRUD operations for Relationship entities.
Re-exports from consolidated crud.py module.
"""

from julee.c4.use_cases.crud import (
    CreateRelationshipRequest,
    CreateRelationshipResponse,
    CreateRelationshipUseCase,
    DeleteRelationshipRequest,
    DeleteRelationshipResponse,
    DeleteRelationshipUseCase,
    GetRelationshipRequest,
    GetRelationshipResponse,
    GetRelationshipUseCase,
    ListRelationshipsRequest,
    ListRelationshipsResponse,
    ListRelationshipsUseCase,
    UpdateRelationshipRequest,
    UpdateRelationshipResponse,
    UpdateRelationshipUseCase,
)

__all__ = [
    "CreateRelationshipRequest",
    "CreateRelationshipResponse",
    "CreateRelationshipUseCase",
    "GetRelationshipRequest",
    "GetRelationshipResponse",
    "GetRelationshipUseCase",
    "ListRelationshipsRequest",
    "ListRelationshipsResponse",
    "ListRelationshipsUseCase",
    "UpdateRelationshipRequest",
    "UpdateRelationshipResponse",
    "UpdateRelationshipUseCase",
    "DeleteRelationshipRequest",
    "DeleteRelationshipResponse",
    "DeleteRelationshipUseCase",
]

"""Relationship use-cases.

CRUD operations for Relationship entities.
"""

from .create import (
    CreateRelationshipRequest,
    CreateRelationshipResponse,
    CreateRelationshipUseCase,
)
from .delete import (
    DeleteRelationshipRequest,
    DeleteRelationshipResponse,
    DeleteRelationshipUseCase,
)
from .get import GetRelationshipRequest, GetRelationshipResponse, GetRelationshipUseCase
from .list import (
    ListRelationshipsRequest,
    ListRelationshipsResponse,
    ListRelationshipsUseCase,
)
from .update import (
    UpdateRelationshipRequest,
    UpdateRelationshipResponse,
    UpdateRelationshipUseCase,
)

__all__ = [
    # Create
    "CreateRelationshipRequest",
    "CreateRelationshipResponse",
    "CreateRelationshipUseCase",
    # Get
    "GetRelationshipRequest",
    "GetRelationshipResponse",
    "GetRelationshipUseCase",
    # List
    "ListRelationshipsRequest",
    "ListRelationshipsResponse",
    "ListRelationshipsUseCase",
    # Update
    "UpdateRelationshipRequest",
    "UpdateRelationshipResponse",
    "UpdateRelationshipUseCase",
    # Delete
    "DeleteRelationshipRequest",
    "DeleteRelationshipResponse",
    "DeleteRelationshipUseCase",
]

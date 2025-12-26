"""SoftwareSystem use-cases.

CRUD operations for SoftwareSystem entities.
Re-exports from consolidated crud.py module.
"""

from julee.c4.use_cases.crud import (
    CreateSoftwareSystemRequest,
    CreateSoftwareSystemResponse,
    CreateSoftwareSystemUseCase,
    DeleteSoftwareSystemRequest,
    DeleteSoftwareSystemResponse,
    DeleteSoftwareSystemUseCase,
    GetSoftwareSystemRequest,
    GetSoftwareSystemResponse,
    GetSoftwareSystemUseCase,
    ListSoftwareSystemsRequest,
    ListSoftwareSystemsResponse,
    ListSoftwareSystemsUseCase,
    UpdateSoftwareSystemRequest,
    UpdateSoftwareSystemResponse,
    UpdateSoftwareSystemUseCase,
)

__all__ = [
    "CreateSoftwareSystemRequest",
    "CreateSoftwareSystemResponse",
    "CreateSoftwareSystemUseCase",
    "DeleteSoftwareSystemRequest",
    "DeleteSoftwareSystemResponse",
    "DeleteSoftwareSystemUseCase",
    "GetSoftwareSystemRequest",
    "GetSoftwareSystemResponse",
    "GetSoftwareSystemUseCase",
    "ListSoftwareSystemsRequest",
    "ListSoftwareSystemsResponse",
    "ListSoftwareSystemsUseCase",
    "UpdateSoftwareSystemRequest",
    "UpdateSoftwareSystemResponse",
    "UpdateSoftwareSystemUseCase",
]

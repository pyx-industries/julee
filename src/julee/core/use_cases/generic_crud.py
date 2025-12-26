"""Generic CRUD use case base classes.

Provides base classes for Get, List, Delete, Create, and Update operations.
Subclass these to create doctrine-compliant CRUD use cases with minimal boilerplate.

All base classes are decorated with @use_case, so subclasses automatically
receive protocol validation, logging, and error handling.

Example:
    from julee.core.use_cases import generic_crud
    from julee.hcd.entities.story import Story
    from julee.hcd.repositories.story import StoryRepository

    class GetStoryUseCase(generic_crud.GetUseCase[Story, StoryRepository]):
        '''Get a story by slug.'''

    class ListStoriesUseCase(generic_crud.ListUseCase[Story, StoryRepository]):
        '''List all stories.'''
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from julee.core.decorators import use_case

E = TypeVar("E", bound=BaseModel)
R = TypeVar("R")
Resp = TypeVar("Resp", bound=BaseModel)


# =============================================================================
# GET
# =============================================================================


class GetRequest(BaseModel):
    """Base request for get operations.

    Default identifier field is `slug`. Override in subclass if needed:

        class GetDocumentRequest(generic_crud.GetRequest):
            slug: None = None  # Remove default
            document_id: str   # Use different field
    """

    slug: str


class GetResponse(BaseModel, Generic[E]):
    """Base response for get operations.

    Returns the entity or None if not found.
    """

    entity: E | None = None


@use_case
class GetUseCase(Generic[E, R]):
    """Base use case for getting an entity by identifier.

    Class attributes:
        id_field: Name of the identifier field on the request (default: "slug")
        response_cls: Response class to use (default: GetResponse)

    The repository must have an async `get(id) -> Entity | None` method.
    """

    id_field: str = "slug"
    response_cls: type[Any] = GetResponse

    def __init__(self, repo: R) -> None:
        self.repo = repo

    async def execute(self, request: GetRequest) -> GetResponse[E]:
        entity_id = getattr(request, self.id_field)
        entity = await self.repo.get(entity_id)
        return self.response_cls(entity=entity)


# =============================================================================
# LIST
# =============================================================================


class ListRequest(BaseModel):
    """Base request for list operations.

    Empty by default. Add filtering fields in subclass:

        class ListStoriesRequest(generic_crud.ListRequest):
            app_slug: str | None = None  # Optional filter
    """

    pass


class ListResponse(BaseModel, Generic[E]):
    """Base response for list operations.

    Returns a list of entities.
    """

    entities: list[E] = []


@use_case
class ListUseCase(Generic[E, R]):
    """Base use case for listing entities.

    Class attributes:
        response_cls: Response class to use (default: ListResponse)

    The repository must have an async `list_all() -> list[Entity]` method.
    """

    response_cls: type[Any] = ListResponse

    def __init__(self, repo: R) -> None:
        self.repo = repo

    async def execute(self, request: ListRequest) -> ListResponse[E]:
        entities = await self.repo.list_all()
        return self.response_cls(entities=entities)


# =============================================================================
# PAGINATED LIST
# =============================================================================


class PaginatedListRequest(BaseModel):
    """Base request for paginated list operations.

    Provides standard pagination parameters. Add filtering in subclass:

        class ListStoriesRequest(generic_crud.PaginatedListRequest):
            app_slug: str | None = None  # Optional filter
    """

    limit: int = 100
    offset: int = 0


class PaginatedListResponse(BaseModel, Generic[E]):
    """Base response for paginated list operations.

    Returns entities with pagination metadata.
    """

    entities: list[E] = []
    total: int = 0
    limit: int = 100
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """True if there are more entities beyond this page."""
        return self.offset + len(self.entities) < self.total


@use_case
class PaginatedListUseCase(Generic[E, R]):
    """Base use case for paginated listing.

    The repository must have:
    - async `list_all() -> list[Entity]` method
    - OR async `list_paginated(limit, offset) -> tuple[list[Entity], int]` method

    If list_paginated exists, it's used for efficient pagination.
    Otherwise, list_all is used with in-memory slicing.
    """

    def __init__(self, repo: R) -> None:
        self.repo = repo

    async def execute(self, request: PaginatedListRequest) -> PaginatedListResponse[E]:
        if hasattr(self.repo, "list_paginated"):
            # Efficient: repo handles pagination
            entities, total = await self.repo.list_paginated(
                limit=request.limit, offset=request.offset
            )
        else:
            # Fallback: in-memory pagination
            all_entities = await self.repo.list_all()
            total = len(all_entities)
            entities = all_entities[request.offset : request.offset + request.limit]

        return PaginatedListResponse(
            entities=entities,
            total=total,
            limit=request.limit,
            offset=request.offset,
        )


# =============================================================================
# DELETE
# =============================================================================


class DeleteRequest(BaseModel):
    """Base request for delete operations.

    Default identifier field is `slug`. Override in subclass if needed.
    """

    slug: str


class DeleteResponse(BaseModel):
    """Base response for delete operations.

    Returns whether the entity was deleted.
    """

    deleted: bool = False


@use_case
class DeleteUseCase(Generic[E, R]):
    """Base use case for deleting an entity by identifier.

    Class attributes:
        id_field: Name of the identifier field on the request (default: "slug")

    The repository must have an async `delete(id) -> bool` method.
    """

    id_field: str = "slug"

    def __init__(self, repo: R) -> None:
        self.repo = repo

    async def execute(self, request: DeleteRequest) -> DeleteResponse:
        entity_id = getattr(request, self.id_field)
        deleted = await self.repo.delete(entity_id)
        return DeleteResponse(deleted=deleted)


# =============================================================================
# CREATE
# =============================================================================


class CreateRequest(BaseModel):
    """Base request for create operations.

    Subclass must define entity fields. The entity class should implement
    `from_create_data(**kwargs)` for custom creation logic.

        class CreateStoryRequest(generic_crud.CreateRequest):
            feature_title: str
            persona: str
            app_slug: str
    """

    pass


class CreateResponse(BaseModel, Generic[E]):
    """Base response for create operations.

    Returns the created entity.
    """

    entity: E


@use_case
class CreateUseCase(Generic[E, R]):
    """Base use case for creating an entity.

    Class attributes:
        entity_cls: The entity class to create (required)

    The entity class should implement `from_create_data(**kwargs)` class method.
    If not present, falls back to direct construction.

    The repository must have an async `save(entity)` method.
    """

    entity_cls: type[E]

    def __init__(self, repo: R) -> None:
        self.repo = repo

    async def execute(self, request: CreateRequest) -> CreateResponse[E]:
        data = request.model_dump()
        if hasattr(self.entity_cls, "from_create_data"):
            entity = self.entity_cls.from_create_data(**data)
        else:
            entity = self.entity_cls(**data)
        await self.repo.save(entity)
        return CreateResponse(entity=entity)


# =============================================================================
# UPDATE
# =============================================================================


class UpdateRequest(BaseModel):
    """Base request for update operations.

    Subclass must define identifier and update fields:

        class UpdateStoryRequest(generic_crud.UpdateRequest):
            slug: str  # Identifier
            i_want: str | None = None  # Optional update field
            so_that: str | None = None
    """

    slug: str


class UpdateResponse(BaseModel, Generic[E]):
    """Base response for update operations.

    Returns the updated entity or None if not found.
    """

    entity: E | None = None


@use_case
class UpdateUseCase(Generic[E, R]):
    """Base use case for updating an entity.

    Class attributes:
        id_field: Name of the identifier field on the request (default: "slug")
        update_fields: List of field names that can be updated (optional)

    The entity class should implement `apply_update(**kwargs)` method.
    If not present, falls back to model_copy(update=kwargs).

    The repository must have async `get(id)` and `save(entity)` methods.
    """

    id_field: str = "slug"
    update_fields: list[str] | None = None

    def __init__(self, repo: R) -> None:
        self.repo = repo

    async def execute(self, request: UpdateRequest) -> UpdateResponse[E]:
        entity_id = getattr(request, self.id_field)
        entity = await self.repo.get(entity_id)
        if entity is None:
            return UpdateResponse(entity=None)

        # Extract update data (exclude id field, exclude None values)
        data = request.model_dump(exclude={self.id_field}, exclude_none=True)

        # Filter to allowed fields if specified
        if self.update_fields:
            data = {k: v for k, v in data.items() if k in self.update_fields}

        # Apply update
        if hasattr(entity, "apply_update"):
            updated = entity.apply_update(**data)
        else:
            updated = entity.model_copy(update=data)

        await self.repo.save(updated)
        return UpdateResponse(entity=updated)

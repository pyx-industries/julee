"""Generic CRUD use case base classes.

Provides base classes for Get, List, Delete, Create, and Update operations.
Subclass these to create doctrine-compliant CRUD use cases with minimal boilerplate.

All base classes are decorated with @use_case, so subclasses automatically
receive protocol validation, logging, and error handling.

Response classes auto-derive field names from entity types:
    - GetResponse[SoftwareSystem] serializes as {"software_system": ...}
    - ListResponse[Story] serializes as {"stories": [...]}

Example:
    from julee.core.use_cases import generic_crud
    from julee.hcd.entities.story import Story
    from julee.hcd.repositories.story import StoryRepository

    class GetStoryUseCase(generic_crud.GetUseCase[Story, StoryRepository]):
        '''Get a story by slug.'''

    class ListStoriesUseCase(generic_crud.ListUseCase[Story, StoryRepository]):
        '''List all stories.'''
"""

import inspect
import re
import types
from typing import Any, ClassVar, Generic, TypeVar, get_args, get_origin, get_type_hints

from pydantic import BaseModel, Field, create_model, model_serializer

from julee.core.decorators import use_case

E = TypeVar("E", bound=BaseModel)
R = TypeVar("R")
Resp = TypeVar("Resp", bound=BaseModel)


# =============================================================================
# Auto-derived Field Names
# =============================================================================


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _pluralize(name: str) -> str:
    """Simple English pluralization."""
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        # Consonant + y -> ies (e.g., story -> stories)
        return name[:-1] + "ies"
    elif name.endswith("s") or name.endswith("x") or name.endswith("ch"):
        return name + "es"
    # Vowel + y -> ys (e.g., journey -> journeys)
    return name + "s"


def _get_entity_type_from_class(cls: type) -> type | None:
    """Extract the entity type E from a Pydantic model with entity/entities field.

    Uses Pydantic's model_fields which resolves generic type parameters.
    """
    # Check entity field (for singular responses)
    if hasattr(cls, "model_fields") and "entity" in cls.model_fields:
        annotation = cls.model_fields["entity"].annotation
        # Handle Optional[E] -> extract E
        origin = get_origin(annotation)
        if origin is not None:
            args = get_args(annotation)
            if args:
                # Get the first non-None type
                for arg in args:
                    if arg is not type(None) and isinstance(arg, type):
                        return arg
        elif isinstance(annotation, type):
            return annotation

    # Check entities field (for list responses)
    if hasattr(cls, "model_fields") and "entities" in cls.model_fields:
        annotation = cls.model_fields["entities"].annotation
        origin = get_origin(annotation)
        if origin is list:
            args = get_args(annotation)
            if args and isinstance(args[0], type):
                return args[0]

    return None


class EntityFieldMixin:
    """Mixin that provides auto-derived field name for entity responses.

    Subclasses get:
    - Dynamic attribute access: response.software_system (derived from SoftwareSystem)
    - Custom serialization: {"software_system": ...} instead of {"entity": ...}
    """

    _entity_field_name: ClassVar[str | None] = None  # Cached field name
    _is_list: ClassVar[bool] = False  # Whether this is a list response

    @classmethod
    def _get_entity_field_name(cls) -> str:
        """Get the snake_case field name derived from entity type."""
        if cls._entity_field_name:
            return cls._entity_field_name

        entity_type = _get_entity_type_from_class(cls)
        if entity_type is None:
            return "entities" if cls._is_list else "entity"

        name = _to_snake_case(entity_type.__name__)
        if cls._is_list:
            name = _pluralize(name)

        return name

    def __getattr__(self, name: str) -> Any:
        """Allow access via derived field name (e.g., response.software_system)."""
        # Get expected field name
        expected = self._get_entity_field_name()
        if name == expected:
            # Return the entity/entities from the actual field
            if self._is_list:
                return object.__getattribute__(self, "entities")
            return object.__getattribute__(self, "entity")
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")


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


class GetResponse(EntityFieldMixin, BaseModel, Generic[E]):
    """Base response for get operations.

    Returns the entity or None if not found.
    Auto-derives field name from entity type for serialization.

    Example:
        class GetSoftwareSystemResponse(GetResponse[SoftwareSystem]):
            pass

        response.software_system  # Works via __getattr__
        response.model_dump()     # {"software_system": ...}
    """

    entity: E | None = None
    _is_list: ClassVar[bool] = False

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        """Serialize with auto-derived field name."""
        field_name = self._get_entity_field_name()
        return {field_name: self.entity}


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


class ListResponse(EntityFieldMixin, BaseModel, Generic[E]):
    """Base response for list operations.

    Returns a list of entities with auto-derived field name.

    Example:
        class ListStoriesResponse(ListResponse[Story]):
            pass

        response.stories  # Works via __getattr__
        response.count    # Number of entities
        response.model_dump()  # {"stories": [...]}
    """

    entities: list[E] = []
    _is_list: ClassVar[bool] = True

    @property
    def count(self) -> int:
        """Number of entities in the response."""
        return len(self.entities)

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        """Serialize with auto-derived field name (pluralized)."""
        field_name = self._get_entity_field_name()
        return {field_name: self.entities}


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
# FILTERABLE LIST
# =============================================================================


def extract_filter_params(repo_class: type) -> dict[str, tuple[type, Any]]:
    """Extract filter parameters from repository's list_filtered signature.

    Introspects the `list_filtered` method signature to determine what filters
    are available. Each parameter with a default of None becomes a filter.

    Args:
        repo_class: Repository class or protocol with list_filtered method

    Returns:
        Dict mapping parameter name to (type, Field) tuple for create_model

    Example:
        >>> class MyRepo(Protocol):
        ...     async def list_filtered(
        ...         self, app_slug: str | None = None
        ...     ) -> list[Entity]: ...
        >>> extract_filter_params(MyRepo)
        {'app_slug': (str | None, FieldInfo(default=None))}
    """
    if not hasattr(repo_class, "list_filtered"):
        return {}

    try:
        hints = get_type_hints(repo_class.list_filtered)
    except Exception:
        hints = {}

    sig = inspect.signature(repo_class.list_filtered)
    filters: dict[str, tuple[type, Any]] = {}

    for name, param in sig.parameters.items():
        if name in ("self", "return"):
            continue

        type_hint = hints.get(name, str)

        # Handle X | None (UnionType) -> extract base type for Field
        origin = get_origin(type_hint)
        if origin is types.UnionType:
            args = get_args(type_hint)
            # Keep the full type hint (including None) for the field
            # but extract base for documentation
            base_type = next((t for t in args if t is not type(None)), str)
            field_type = base_type | None
        else:
            field_type = type_hint | None

        default = (
            param.default if param.default is not inspect.Parameter.empty else None
        )
        filters[name] = (field_type, Field(default=default))

    return filters


def make_list_request(name: str, repo_class: type) -> type[BaseModel]:
    """Generate a ListRequest model from repository's list_filtered signature.

    Creates a Pydantic model with filter fields matching the repository's
    list_filtered parameters. This enables automatic query param extraction
    in FastAPI via Depends().

    Args:
        name: Name for the generated model class
        repo_class: Repository class or protocol with list_filtered method

    Returns:
        A new Pydantic model class with filter fields

    Example:
        >>> ListStoriesRequest = make_list_request("ListStoriesRequest", StoryRepository)
        >>> # Equivalent to:
        >>> class ListStoriesRequest(BaseModel):
        ...     app_slug: str | None = None
        ...     persona: str | None = None
    """
    filter_params = extract_filter_params(repo_class)
    return create_model(name, **filter_params)


@use_case
class FilterableListUseCase(Generic[E, R]):
    """List use case with automatic filtering from repository.

    Delegates filtering to the repository's list_filtered() method. The
    repository protocol's list_filtered signature declares available filters.

    Class attributes:
        response_cls: Response class to use (default: ListResponse)

    Usage with dynamic request generation:
        ListStoriesRequest = make_list_request("ListStoriesRequest", StoryRepository)

        class ListStoriesUseCase(FilterableListUseCase[Story, StoryRepository]):
            pass

    Usage with explicit request (BCs can always choose this):
        class ListStoriesRequest(BaseModel):
            app_slug: str | None = None
            persona: str | None = None

        class ListStoriesUseCase(FilterableListUseCase[Story, StoryRepository]):
            pass

    The repository must implement:
        async def list_filtered(self, **filters) -> list[Entity]
        async def list_all(self) -> list[Entity]  # fallback when no filters
    """

    response_cls: type[Any] = ListResponse

    def __init__(self, repo: R) -> None:
        self.repo = repo

    async def execute(self, request: BaseModel) -> ListResponse[E]:
        """Execute list operation with optional filtering.

        Extracts non-None filter values from request and delegates to
        repository's list_filtered method. Falls back to list_all when
        no filters are provided or repository lacks list_filtered.
        """
        # Extract non-None filter values from request
        filters = {k: v for k, v in request.model_dump().items() if v is not None}

        # Delegate to repository's list_filtered if filters provided
        if filters and hasattr(self.repo, "list_filtered"):
            entities = await self.repo.list_filtered(**filters)
        else:
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


class CreateResponse(EntityFieldMixin, BaseModel, Generic[E]):
    """Base response for create operations.

    Returns the created entity with auto-derived field name.

    Example:
        class CreateSoftwareSystemResponse(CreateResponse[SoftwareSystem]):
            pass

        response.software_system  # Works via __getattr__
        response.model_dump()     # {"software_system": ...}
    """

    entity: E
    _is_list: ClassVar[bool] = False

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        """Serialize with auto-derived field name."""
        field_name = self._get_entity_field_name()
        return {field_name: self.entity}


@use_case
class CreateUseCase(Generic[E, R]):
    """Base use case for creating an entity.

    Class attributes:
        entity_cls: The entity class to create (required)
        response_cls: Response class to use (default: CreateResponse)

    The entity class should implement `from_create_data(**kwargs)` class method.
    If not present, falls back to direct construction.

    The repository must have an async `save(entity)` method.

    Optional handler parameter enables workflow orchestration - see ADR 003.
    """

    entity_cls: type[E]
    response_cls: type[Any] = CreateResponse

    def __init__(self, repo: R, post_create_handler: Any | None = None) -> None:
        self.repo = repo
        self.post_create_handler = post_create_handler

    async def execute(self, request: CreateRequest) -> CreateResponse[E]:
        data = request.model_dump()
        if hasattr(self.entity_cls, "from_create_data"):
            entity = self.entity_cls.from_create_data(**data)
        else:
            entity = self.entity_cls(**data)
        await self.repo.save(entity)

        if self.post_create_handler is not None:
            await self.post_create_handler.handle(entity)

        return self.response_cls(entity=entity)


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


class UpdateResponse(EntityFieldMixin, BaseModel, Generic[E]):
    """Base response for update operations.

    Returns the updated entity or None if not found.
    Auto-derives field name from entity type for serialization.

    Example:
        class UpdateSoftwareSystemResponse(UpdateResponse[SoftwareSystem]):
            pass

        response.software_system  # Works via __getattr__
        response.found            # True if entity was found
        response.model_dump()     # {"software_system": ..., "found": ...}
    """

    entity: E | None = None
    _is_list: ClassVar[bool] = False

    @property
    def found(self) -> bool:
        """True if entity was found and updated."""
        return self.entity is not None

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        """Serialize with auto-derived field name."""
        field_name = self._get_entity_field_name()
        return {field_name: self.entity, "found": self.found}


@use_case
class UpdateUseCase(Generic[E, R]):
    """Base use case for updating an entity.

    Class attributes:
        id_field: Name of the identifier field on the request (default: "slug")
        update_fields: List of field names that can be updated (optional)
        response_cls: Response class to use (default: UpdateResponse)

    The entity class should implement `apply_update(**kwargs)` method.
    If not present, falls back to model_copy(update=kwargs).

    The repository must have async `get(id)` and `save(entity)` methods.

    Optional handler parameter enables workflow orchestration - see ADR 003.
    """

    id_field: str = "slug"
    update_fields: list[str] | None = None
    response_cls: type[Any] = UpdateResponse

    def __init__(self, repo: R, post_update_handler: Any | None = None) -> None:
        self.repo = repo
        self.post_update_handler = post_update_handler

    async def execute(self, request: UpdateRequest) -> UpdateResponse[E]:
        entity_id = getattr(request, self.id_field)
        entity = await self.repo.get(entity_id)
        if entity is None:
            return self.response_cls(entity=None)

        # Extract update data (exclude id field, exclude None values)
        data = request.model_dump(exclude={self.id_field}, exclude_none=True)

        # Filter to allowed fields if specified
        if self.update_fields:
            data = {k: v for k, v in data.items() if k in self.update_fields}

        # Apply update - use apply_update() if available, otherwise
        # reconstruct via model_validate() to ensure validators run.
        # (model_copy() skips model validators, which can bypass
        # invariants like auto-setting timestamps on state transitions.)
        if hasattr(entity, "apply_update"):
            updated = entity.apply_update(**data)
        else:
            updated = type(entity).model_validate({**entity.model_dump(), **data})

        await self.repo.save(updated)

        if self.post_update_handler is not None:
            await self.post_update_handler.handle(updated)

        return self.response_cls(entity=updated)


# =============================================================================
# CRUD GENERATOR
# =============================================================================


def generate(
    entity: type,
    repository: type,
    *,
    filters: list[str] | None = None,
    id_field: str = "slug",
    delete: bool = True,
    update: bool = True,
    create: bool = True,
) -> None:
    """Generate CRUD use cases, requests, and responses for an entity.

    Injects generated classes into the calling module's namespace.
    This eliminates boilerplate while preserving the public API.

    Generated classes follow naming conventions:
        Get{Entity}UseCase, Get{Entity}Request, Get{Entity}Response
        List{Entities}UseCase, List{Entities}Request, List{Entities}Response
        Delete{Entity}UseCase, Delete{Entity}Request, Delete{Entity}Response
        Create{Entity}UseCase, Create{Entity}Request, Create{Entity}Response
        Update{Entity}UseCase, Update{Entity}Request, Update{Entity}Response

    Args:
        entity: The entity class (e.g., Story, Epic)
        repository: The repository class (e.g., StoryRepository)
        filters: List of filter field names for List operation
        id_field: Name of the identifier field (default: "slug")
        delete: Whether to generate Delete classes (default: True)
        update: Whether to generate Update classes (default: True)
        create: Whether to generate Create classes (default: True)

    Example:
        from julee.core.use_cases import generic_crud

        generic_crud.generate(Story, StoryRepository, filters=["app_slug", "persona"])

        # Now these are available in the module:
        # GetStoryUseCase, GetStoryRequest, GetStoryResponse
        # ListStoriesUseCase, ListStoriesRequest, ListStoriesResponse
        # DeleteStoryUseCase, DeleteStoryRequest, DeleteStoryResponse
        # CreateStoryUseCase, CreateStoryRequest, CreateStoryResponse
        # UpdateStoryUseCase, UpdateStoryRequest, UpdateStoryResponse
    """
    import inspect

    caller_globals = inspect.currentframe().f_back.f_globals

    name = entity.__name__  # "Story"
    plural = _pluralize(name)  # "Stories"

    # -------------------------------------------------------------------------
    # GET
    # -------------------------------------------------------------------------
    get_request_cls = _make_request(f"Get{name}Request", GetRequest, id_field)
    get_response_cls = _make_response(f"Get{name}Response", GetResponse, entity)
    get_use_case_cls = _make_use_case(
        f"Get{name}UseCase",
        GetUseCase,
        entity,
        repository,
        response_cls=get_response_cls,
        id_field=id_field,
    )

    caller_globals[f"Get{name}Request"] = get_request_cls
    caller_globals[f"Get{name}Response"] = get_response_cls
    caller_globals[f"Get{name}UseCase"] = get_use_case_cls

    # -------------------------------------------------------------------------
    # LIST
    # -------------------------------------------------------------------------
    list_request_cls = _make_list_request(f"List{plural}Request", filters)
    list_response_cls = _make_response(f"List{plural}Response", ListResponse, entity)

    if filters:
        list_use_case_cls = _make_use_case(
            f"List{plural}UseCase",
            FilterableListUseCase,
            entity,
            repository,
            response_cls=list_response_cls,
        )
    else:
        list_use_case_cls = _make_use_case(
            f"List{plural}UseCase",
            ListUseCase,
            entity,
            repository,
            response_cls=list_response_cls,
        )

    caller_globals[f"List{plural}Request"] = list_request_cls
    caller_globals[f"List{plural}Response"] = list_response_cls
    caller_globals[f"List{plural}UseCase"] = list_use_case_cls

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
    if delete:
        delete_request_cls = _make_request(
            f"Delete{name}Request", DeleteRequest, id_field
        )
        delete_response_cls = type(f"Delete{name}Response", (DeleteResponse,), {})
        delete_use_case_cls = _make_use_case(
            f"Delete{name}UseCase",
            DeleteUseCase,
            entity,
            repository,
            id_field=id_field,
        )

        caller_globals[f"Delete{name}Request"] = delete_request_cls
        caller_globals[f"Delete{name}Response"] = delete_response_cls
        caller_globals[f"Delete{name}UseCase"] = delete_use_case_cls

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    if create:
        # Basic create request - BC can subclass or replace with custom
        create_request_cls = _make_create_request(
            f"Create{name}Request", entity, id_field
        )
        create_response_cls = _make_response(
            f"Create{name}Response", CreateResponse, entity
        )
        create_use_case_cls = _make_use_case(
            f"Create{name}UseCase",
            CreateUseCase,
            entity,
            repository,
            response_cls=create_response_cls,
            entity_cls=entity,
        )

        caller_globals[f"Create{name}Request"] = create_request_cls
        caller_globals[f"Create{name}Response"] = create_response_cls
        caller_globals[f"Create{name}UseCase"] = create_use_case_cls

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    if update:
        update_request_cls = _make_update_request(
            f"Update{name}Request", entity, id_field
        )
        update_response_cls = _make_response(
            f"Update{name}Response", UpdateResponse, entity
        )
        update_use_case_cls = _make_use_case(
            f"Update{name}UseCase",
            UpdateUseCase,
            entity,
            repository,
            response_cls=update_response_cls,
            id_field=id_field,
        )

        caller_globals[f"Update{name}Request"] = update_request_cls
        caller_globals[f"Update{name}Response"] = update_response_cls
        caller_globals[f"Update{name}UseCase"] = update_use_case_cls


def _make_request(name: str, base: type, id_field: str) -> type:
    """Create a request class with id field."""
    if id_field == "slug":
        # Base already has slug, just subclass
        return type(
            name, (base,), {"__doc__": f"{name.replace('Request', '')} request."}
        )
    else:
        # Need custom id field
        return create_model(
            name,
            __base__=BaseModel,
            **{id_field: (str, Field(description=f"{id_field} identifier"))},
        )


def _make_list_request(name: str, filters: list[str] | None) -> type:
    """Create a list request class with optional filter fields."""
    if not filters:
        return type(name, (ListRequest,), {"__doc__": "List request."})

    # Build filter fields - all optional strings
    fields = {
        f: (str | None, Field(default=None, description=f"Filter by {f}"))
        for f in filters
    }
    return create_model(name, __base__=ListRequest, **fields)


def _make_response(name: str, base: type, entity: type) -> type:
    """Create a response class parameterized with entity type."""

    # Use types.new_class for generic base class inheritance
    def exec_body(ns: dict) -> None:
        ns["__doc__"] = f"{entity.__name__} response."

    return types.new_class(name, (base[entity],), exec_body=exec_body)


def _make_use_case(
    name: str,
    base: type,
    entity: type,
    repository: type,
    *,
    response_cls: type | None = None,
    id_field: str = "slug",
    entity_cls: type | None = None,
) -> type:
    """Create a use case class with proper generic binding."""
    attrs: dict[str, Any] = {"__doc__": f"{name.replace('UseCase', '')} use case."}

    if response_cls is not None:
        attrs["response_cls"] = response_cls
    if id_field != "slug":
        attrs["id_field"] = id_field
    if entity_cls is not None:
        attrs["entity_cls"] = entity_cls

    # Use types.new_class for generic base class inheritance
    def exec_body(ns: dict) -> None:
        ns.update(attrs)

    return types.new_class(name, (base[entity, repository],), exec_body=exec_body)


def _is_excluded_field(field_name: str, field_info: Any) -> bool:
    """Check if a field should be excluded from generated requests.

    Exclusion patterns (conventions that entities should follow):
    - Fields ending with '_normalized': Computed/derived fields
    - Fields ending with '_rst': RST round-trip fields (document structure)
    - Fields with exclude=True in Field() json_schema_extra
    """
    # Pattern: *_normalized fields are computed
    if field_name.endswith("_normalized"):
        return True

    # Pattern: *_rst fields are for RST round-trip
    if field_name.endswith("_rst"):
        return True

    # Explicit exclusion via Field(json_schema_extra={"exclude_from_crud": True})
    if field_info.json_schema_extra:
        extra = field_info.json_schema_extra
        if isinstance(extra, dict) and extra.get("exclude_from_crud"):
            return True

    return False


def _make_create_request_from_fields(name: str, entity: type) -> type:
    """Create a Create request by introspecting entity fields.

    Exclusion patterns:
    - *_normalized: Computed/derived fields
    - *_rst: RST round-trip fields
    - Fields with json_schema_extra={"exclude_from_crud": True}
    """
    fields: dict[str, tuple[type, Any]] = {}

    for field_name, field_info in entity.model_fields.items():
        if _is_excluded_field(field_name, field_info):
            continue

        annotation = field_info.annotation

        if field_info.is_required():
            # Required field
            fields[field_name] = (annotation, Field(...))
        elif field_info.default_factory is not None:
            # Field with default_factory (e.g., list, dict)
            fields[field_name] = (
                annotation,
                Field(default_factory=field_info.default_factory),
            )
        elif field_info.default is not None:
            # Field with default value
            fields[field_name] = (annotation, Field(default=field_info.default))
        else:
            # Optional field with None default
            fields[field_name] = (annotation, Field(default=None))

    return create_model(name, __base__=CreateRequest, **fields)


def _make_create_request(name: str, entity: type, id_field: str) -> type:
    """Create a Create request by introspecting entity's from_create_data or fields.

    If entity has from_create_data() class method with explicit params, uses its signature.
    Otherwise falls back to entity fields with exclusion patterns.
    """
    # Prefer from_create_data signature if available and has explicit params
    if hasattr(entity, "from_create_data"):
        try:
            hints = get_type_hints(entity.from_create_data)
        except Exception:
            hints = {}

        fields: dict[str, tuple[type, Any]] = {}
        sig = inspect.signature(entity.from_create_data)
        for param_name, param in sig.parameters.items():
            if param_name in ("cls", "self"):
                continue
            # Skip *args and **kwargs
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            type_hint = hints.get(param_name, str)
            default = param.default

            if default is inspect.Parameter.empty:
                # Required parameter
                fields[param_name] = (type_hint, Field(...))
            else:
                # Optional with default
                fields[param_name] = (type_hint, Field(default=default))

        # If from_create_data has explicit params, use them
        if fields:
            return create_model(name, __base__=CreateRequest, **fields)

    # Fallback: introspect entity fields
    return _make_create_request_from_fields(name, entity)


def _make_update_request(name: str, entity: type, id_field: str) -> type:
    """Create an Update request by introspecting entity fields.

    All fields are optional (for partial updates) except the id field.
    Uses same exclusion patterns as _make_create_request.
    """
    fields: dict[str, tuple[type, Any]] = {}

    # Always include id field as required
    fields[id_field] = (str, Field(..., description=f"{id_field} identifier"))

    for field_name, field_info in entity.model_fields.items():
        if field_name == id_field:
            continue  # Already added
        if _is_excluded_field(field_name, field_info):
            continue

        annotation = field_info.annotation
        # Make all update fields optional
        origin = get_origin(annotation)
        if origin is None:
            # Simple type - make optional
            optional_type = annotation | None
        else:
            # Already complex type (list, etc.) - wrap in Optional
            optional_type = annotation | None

        fields[field_name] = (optional_type, Field(default=None))

    return create_model(name, __base__=BaseModel, **fields)

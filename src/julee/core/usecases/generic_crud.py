"""Generic CRUD use case base classes.

Provides base classes for Get, List, Create, Update and Delete. Downstream
projects call generate_crud.py to emit concrete, doctrine-compliant use case
subclasses for a specific entity and repository.
"""

import dataclasses
import types
from abc import abstractmethod
from typing import (
    Any,
    Generic,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from julee.core.repositories.base import Deletable

E = TypeVar("E")
R = TypeVar("R")
RD = TypeVar("RD", bound=Deletable[Any])
"""A repository that has opted in to being deletable.

The other four bases leave their repository unbound and reach for its
methods behind a type: ignore. Delete does not, because not every
repository has one — ceap and polling have none across nine protocols —
so the bound is what makes asking for a delete use case over a repository
that refuses to delete a type error rather than an AttributeError.
"""


class EntityNotFoundError(Exception):
    """Raised when a requested entity does not exist in the repository."""

    def __init__(self, entity_id: str) -> None:
        """Initialise with the missing entity ID."""
        self.entity_id = entity_id
        super().__init__(f"Entity not found: {entity_id}")


class GetUseCase(Generic[E, R]):
    """Base for get-by-ID use cases.

    Subclasses implement execute() calling _get_by_id() with the ID field
    from the request.
    """

    def __init__(self, repo: R) -> None:
        """Initialise with the entity repository."""
        self.repo = repo

    async def _get_by_id(self, entity_id: str) -> E:
        """Retrieve entity by ID, raising EntityNotFoundError if absent."""
        entity: E | None = await self.repo.get(entity_id)  # type: ignore[attr-defined]
        if entity is None:
            raise EntityNotFoundError(entity_id)
        return entity


class ListUseCase(Generic[E, R]):
    """Base for list-all use cases.

    Subclasses implement execute() calling _list_all().
    """

    def __init__(self, repo: R) -> None:
        """Initialise with the entity repository."""
        self.repo = repo

    async def _list_all(self) -> list[E]:
        """Return all entities from the repository."""
        entities: list[E] = await self.repo.list_all()  # type: ignore[attr-defined]
        return entities


class CreateUseCase(Generic[E, R]):
    """Base for create use cases.

    Subclasses implement execute() calling _create() and override
    _build_entity() to construct the entity from a generated ID and
    request data.
    """

    def __init__(self, repo: R) -> None:
        """Initialise with the entity repository."""
        self.repo = repo

    @abstractmethod
    def _build_entity(self, entity_id: str, **kwargs: Any) -> E:
        """Construct the entity from a generated ID and request fields.

        Implemented by generated subclasses.
        """

    async def _create(self, entity_id: str | None = None, **kwargs: Any) -> E:
        """Build the entity, save and return it.

        The ID is generated unless the caller supplies one. Entities keyed by
        a surrogate ID leave it out; entities keyed by something the caller
        already knows, such as a slug derived from a name, pass it in.
        """
        if entity_id is None:
            entity_id = await self.repo.generate_id()  # type: ignore[attr-defined]
        entity = self._build_entity(entity_id, **kwargs)
        await self.repo.save(entity)  # type: ignore[attr-defined]
        return entity


def _admits_none(hint: object) -> bool:
    """Whether a field's declared type allows None.

    ``X | None``, ``Optional[X]``, ``Any``, ``object`` and ``None`` itself
    do. Anything else does not, whatever a caller passes.
    """
    if hint is Any or hint is object or hint is type(None):
        return True
    if isinstance(hint, types.UnionType) or get_origin(hint) is Union:
        return any(_admits_none(arg) for arg in get_args(hint))
    return False


def _refuse_none_the_type_forbids(entity: object, updates: dict[str, Any]) -> None:
    """Refuse a None for a field whose type does not admit one.

    An update request widens every field to ``T | None`` so that a field
    left out and a field set to None can be told apart: unset is "leave
    it alone" and None is "clear it". That leaves None free to reach a
    field the entity declares as ``str``, and ``dataclasses.replace``
    stores whatever it is handed. The entity was then quietly wrong —
    a str field holding None — and the response used to carry the
    entity, so nothing downstream looked either. The generated message
    (julee#348) was the first thing to refuse it, one step too late.

    This is the one check the request cannot make, because the request
    is the thing that widened the type. Everything else about a value
    the request has already validated.

    Args:
        entity: The entity as stored
        updates: The changes about to be applied

    Raises:
        ValueError: Naming the field and the type that forbids None
    """
    hints = get_type_hints(type(entity))
    for name, value in updates.items():
        if value is None and name in hints and not _admits_none(hints[name]):
            raise ValueError(
                f"{name} may not be cleared: {type(entity).__name__}.{name} is "
                f"{hints[name]!r}, which does not admit None"
            )


class UpdateUseCase(Generic[E, R]):
    """Base for update use cases.

    Subclasses implement execute() calling _update_by_id() with the ID
    field and a dict of field updates. The update is applied via
    model_copy(update=...) which suits entities whose mutable state maps
    directly to Pydantic fields. Entities with non-trivial update logic
    (e.g. JSON-content models) should keep hand-rolled use cases.
    """

    def __init__(self, repo: R) -> None:
        """Initialise with the entity repository."""
        self.repo = repo

    async def _update_by_id(self, entity_id: str, updates: dict[str, Any]) -> E:
        """Fetch the entity, apply the changes, save it and return it.

        A frozen dataclass is rebuilt with ``dataclasses.replace``,
        which runs ``__post_init__`` — so whatever the entity refuses
        to be, it still refuses to be after an update. A pydantic
        model uses ``model_copy``, which does not validate, and is
        what the estate has until its entities finish moving.

        Args:
            entity_id: Which entity to change
            updates: The fields to change and their new values

        Returns:
            The saved entity

        Raises:
            EntityNotFoundError: If nothing is stored under that id
            ValueError: If a change clears a field whose type forbids it,
                before anything is saved
        """
        entity = await self.repo.get(entity_id)  # type: ignore[attr-defined]
        if entity is None:
            raise EntityNotFoundError(entity_id)
        _refuse_none_the_type_forbids(entity, updates)
        updated: E
        if dataclasses.is_dataclass(entity) and not isinstance(entity, type):
            # replace() is typed as returning the DataclassInstance
            # protocol rather than the entity's own type, which is a
            # limit of the stub and not of the call.
            updated = cast("E", dataclasses.replace(entity, **updates))
        else:
            updated = entity.model_copy(update=updates)
        await self.repo.save(updated)  # type: ignore[attr-defined]
        return updated


class DeleteUseCase(Generic[E, RD]):
    """Base for delete-by-ID use cases.

    Subclasses implement execute() calling _delete_by_id() with the ID
    field from the request.

    Reports rather than raising, unlike GetUseCase and UpdateUseCase.
    Deleting something absent leaves the world as the caller wanted it,
    so it is not an error; fetching or updating something absent means
    the caller is working from something stale, so it is.
    """

    def __init__(self, repo: RD) -> None:
        """Initialise with the entity repository."""
        self.repo = repo

    async def _delete_by_id(self, entity_id: str) -> bool:
        """Remove the entity, saying whether there was one to remove."""
        return await self.repo.delete(entity_id)

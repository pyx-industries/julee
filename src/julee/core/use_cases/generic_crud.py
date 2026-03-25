"""Generic CRUD use case base classes.

Provides base classes for Get, List, Create, and Update operations. Downstream
projects call generate_crud.py to emit concrete, doctrine-compliant use case
subclasses for a specific entity and repository.
"""

from abc import abstractmethod
from typing import Any, Generic, TypeVar

E = TypeVar("E")
R = TypeVar("R")


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
        entity = await self.repo.get(entity_id)  # type: ignore[attr-defined]
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
        return await self.repo.list_all()  # type: ignore[attr-defined]


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

    async def _create(self, **kwargs: Any) -> E:
        """Generate an ID, build the entity, save and return it."""
        entity_id = await self.repo.generate_id()  # type: ignore[attr-defined]
        entity = self._build_entity(entity_id, **kwargs)
        await self.repo.save(entity)  # type: ignore[attr-defined]
        return entity


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
        """Fetch entity, apply field updates via model_copy, save and return."""
        entity = await self.repo.get(entity_id)  # type: ignore[attr-defined]
        if entity is None:
            raise EntityNotFoundError(entity_id)
        updated = entity.model_copy(update=updates)
        await self.repo.save(updated)  # type: ignore[attr-defined]
        return updated

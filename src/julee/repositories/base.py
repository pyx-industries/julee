"""
Generic base repository protocol for common CRUD operations.

This module defines a generic BaseRepository protocol that captures the common
patterns shared across all domain repositories in the Capture, Extract,
Assemble, Publish workflow. This reduces code duplication while maintaining
type safety and clean interfaces.

All repository operations follow the same principles:

- **Idempotency**: All methods are designed to be idempotent and safe for
  retry. Multiple calls with the same parameters will produce the same
  result without unintended side effects.

- **Workflow Safety**: A repository is reached from workflow code through
  a proxy that routes each call to an activity, never called directly —
  it does I/O, so its answer can differ between replays. ADR 016 puts it
  on the activity row for that reason, beside services and oracles, and
  distinguishes it from the ports a workflow may call inline.

- **Domain Objects**: Methods accept and return domain objects or primitives,
  never framework-specific types.

In Temporal workflow contexts, these protocols are implemented by workflow
stubs that delegate to activities for durability and proper error handling.
"""

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

# Type variable bound to Pydantic BaseModel for domain entities
T = TypeVar("T", bound=BaseModel)
# The marker names its entity and never takes or returns one, so its
# parameter is covariant, which is what a protocol with no methods needs.
T_co = TypeVar("T_co", bound=BaseModel, covariant=True)


class RepositoryOf(Protocol[T_co]):
    """Declares the one entity a repository is bound to, and nothing else.

    ADR 016 binds a repository to one entity type, and doctrine
    (``test_repository_protocol.py``) reads that entity from a
    ``RepositoryOf[Entity]`` base. A repository that offers CRUD inherits
    it through ``BaseRepository``; one that does not (a read-only source,
    a paged feed, a content-addressed store) inherits it directly and is
    checked by the same rule instead of being exempt from it.

    This inherited declaration is why a repository, alone among the six
    driven ports, is not held to a naming rule: it says what it is in a
    way mypy reads too, which is stronger than a suffix. A protocol bound
    to no entity is not a repository at all — see ADR 016 for which of
    the other five it is.

    Type Parameter:
        T_co: The domain entity type (must extend Pydantic BaseModel)
    """


@runtime_checkable
class BaseRepository(RepositoryOf[T], Protocol[T]):
    """Generic base repository protocol for common CRUD operations.

    This protocol defines the common interface shared by all domain
    repositories in the system. It uses generics to provide type safety
    while eliminating code duplication.

    Type Parameter:
        T: The domain entity type (must extend Pydantic BaseModel)
    """

    async def get(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID.

        Args:
            entity_id: Unique entity identifier

        Returns:
            Entity if found, None otherwise

        .. rubric:: Implementation Notes

        - Must be idempotent: multiple calls return same result
        - Should handle missing entities gracefully (return None)
        - Loads complete entity with all relationships

        """
        ...

    async def get_many(self, entity_ids: list[str]) -> dict[str, T | None]:
        """Retrieve multiple entities by ID.

        Args:
            entity_ids: List of unique entity identifiers

        Returns:
            Dict mapping entity_id to entity (or None if not found)

        .. rubric:: Implementation Notes

        - Must be idempotent: multiple calls return same result
        - Should handle missing entities gracefully (return None for missing)
        - Implementations may optimize with batch operations or fall back
          to individual get() calls
        - Keys in returned dict correspond exactly to input entity_ids
        - Missing entities have None values in the returned dict

        .. rubric:: Workflow Context

        In Temporal workflows, this method is implemented as an activity
        to ensure batch operations are durably stored and consistent
        across workflow replays.

        """
        ...

    async def save(self, entity: T) -> None:
        """Save an entity.

        Args:
            entity: Complete entity to save

        .. rubric:: Implementation Notes

        - Must be idempotent: saving same entity state is safe
        - Should update the updated_at timestamp
        - Must save complete entity with all relationships
        - Handles both new entities and updates to existing ones

        """
        ...

    async def list_all(self) -> list[T]:
        """List all entities.

        Returns:
            List of all entities in the repository

        .. rubric:: Implementation Notes

        - Must be idempotent: multiple calls return same result
        - Returns empty list if no entities exist
        - Should return entities in a consistent order (e.g., by ID)
        - For large datasets, consider pagination at the use case level

        .. rubric:: Workflow Context

        In Temporal workflows, this method is implemented as an activity
        to ensure the list operation is durably stored and consistent
        across workflow replays.

        .. rubric:: Default Implementation

        Base protocol provides a default that returns empty list.
        Repository implementations should override this method as needed.

        .. note::

            This default implementation returns empty list to avoid
            breaking existing repositories. Specific repositories should
            implement proper list_all() functionality as needed.

        """
        return []

    async def generate_id(self) -> str:
        """Generate a unique entity identifier.

        This operation is non-deterministic and must be called from
        workflow activities, not directly from workflow code.

        Optional. An entity identified by something its author already knows,
        such as a slug read off its name, has no ID for the repository to
        decide, and such a repository may leave this alone: callers supply the
        ID themselves and never reach here.

        Returns:
            Unique entity ID string

        Raises:
            NotImplementedError: If the repository does not mint IDs.

        .. rubric:: Implementation Notes

        - Must generate globally unique identifiers
        - May use UUIDs, database sequences, or distributed ID generators
        - Should be fast and reliable
        - Failure here should be rare but handled gracefully

        .. rubric:: Workflow Context

        In Temporal workflows, this method is implemented as an activity
        to ensure the generated ID is durably stored and consistent
        across workflow replays.

        """
        raise NotImplementedError(
            f"{type(self).__name__} does not generate IDs; its entities are "
            f"identified by something the caller already knows"
        )


@runtime_checkable
class Deletable(RepositoryOf[T_co], Protocol[T_co]):
    """A repository whose entities can be removed.

    Deliberately not part of :class:`BaseRepository`. Across the five
    kits the split is clean: c4 and hcd delete everything, because
    documentation that cannot forget goes stale — a container that no
    longer exists should stop appearing in diagrams. ceap and polling
    delete nothing, across eight repository protocols, because deleting a
    processed document destroys the record of having processed it.

    Putting ``delete`` on ``BaseRepository`` would force those eight to
    implement something they should refuse, so a repository opts in by
    inheriting this instead.

    Covariant like RepositoryOf, and for the same reason: deleting takes
    an identifier and returns a bool, so the entity type is named here
    and never passed or returned.

    Type Parameter:
        T_co: The domain entity type (must extend Pydantic BaseModel)
    """

    async def delete(self, entity_id: str) -> bool:
        """Remove one entity, saying whether there was one to remove.

        Reports rather than raising. "It was already gone" is the outcome
        the caller asked for, which is why deleting twice is not an
        error — unlike ``get`` and ``update``, where an absent entity
        means the caller is working from something stale.

        Both kits that hand-wrote delete before this existed arrived at
        the same answer independently.

        Args:
            entity_id: Identifier of the entity to remove

        Returns:
            True if an entity was removed, False if there was none
        """
        ...

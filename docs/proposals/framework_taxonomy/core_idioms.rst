Core Idioms: The Foundation
===========================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

The ``core/`` accelerator is the foundation of Julee. It defines the
**coding idioms** that:

- Viewpoints are **ontologically bound to** (they express concepts using these patterns)
- Contrib modules **depend on** (they build utilities using these patterns)
- Solutions **adopt** (they become julee solutions by following these patterns)

Everything in Julee—viewpoints, contrib, applications, solutions—speaks the
same language because they all derive from ``core/``.

What core/ Contains
-------------------

::

    core/
      entities/
        base.py              # BaseEntity - frozen Pydantic models
        identifiable.py      # ID generation patterns
        timestamps.py        # created_at, updated_at mixins
        validation.py        # Field validation patterns
      repositories/
        base.py              # Repository interface pattern
        exceptions.py        # NotFound, Conflict, etc.
        unit_of_work.py      # Transaction boundaries
      use_cases/
        base.py              # Use case interface pattern
        exceptions.py        # UseCaseError hierarchy
        decorators.py        # @use_case, @transactional
      infrastructure/
        repositories/
          memory/            # In-memory reference implementations
          file/              # File-based reference implementations

The Entity Idiom
----------------

Entities are **immutable domain objects** built on Pydantic:

.. code-block:: python

    # core/entities/base.py
    from pydantic import BaseModel, ConfigDict

    class BaseEntity(BaseModel):
        """Base class for all domain entities."""
        model_config = ConfigDict(frozen=True)

**What this gives you:**

- **Immutability**: Entities can't be accidentally mutated
- **Validation**: Pydantic validates on construction
- **Serialization**: ``model_dump()``, ``model_dump_json()`` for free
- **Type safety**: Full type hints, IDE completion

**The pattern in practice:**

.. code-block:: python

    # hcd/entities/story.py
    from julee.core.entities import BaseEntity

    class Story(BaseEntity):
        story_id: str
        title: str
        description: str
        acceptance_criteria: list[str] = []

        # Immutable - to "change" a story, create a new one
        def with_title(self, new_title: str) -> "Story":
            return self.model_copy(update={"title": new_title})

**Field validation patterns:**

.. code-block:: python

    # core/entities/validation.py
    from pydantic import field_validator

    class NonEmptyStrMixin:
        """Mixin for entities with non-empty string fields."""

        @field_validator("*", mode="before")
        @classmethod
        def strip_strings(cls, v):
            if isinstance(v, str):
                v = v.strip()
                if not v:
                    raise ValueError("Field cannot be empty")
            return v

The Repository Idiom
--------------------

Repositories are **Protocol interfaces** that define how entities are
persisted and retrieved. We use ``typing.Protocol`` for structural subtyping
(duck typing with type safety), not ABCs:

.. code-block:: python

    # core/repositories/base.py
    from typing import Protocol, TypeVar, runtime_checkable
    from pydantic import BaseModel

    T = TypeVar("T", bound=BaseModel)

    @runtime_checkable
    class BaseRepository(Protocol[T]):
        """Generic base repository protocol."""

        async def get(self, entity_id: str) -> T | None:
            """Retrieve entity by ID, or None if not found."""
            ...

        async def save(self, entity: T) -> None:
            """Persist entity."""
            ...

        async def delete(self, entity_id: str) -> bool:
            """Delete entity by ID, return True if deleted."""
            ...

        async def list_all(self) -> list[T]:
            """List all entities."""
            ...

**Why Protocols:**

- **Structural typing**: Any class with matching methods satisfies the protocol
- **No inheritance required**: Implementations don't need to inherit from anything
- **Runtime checkable**: ``isinstance(repo, BaseRepository)`` works
- **Duck typing + type safety**: The best of both worlds

The domain defines *what* persistence operations exist, not *how* they work.
Implementations live in ``infrastructure/``:

.. code-block:: python

    # hcd/repositories/story.py (interface)
    from typing import Protocol, runtime_checkable
    from .base import BaseRepository
    from ..models.story import Story

    @runtime_checkable
    class StoryRepository(BaseRepository[Story], Protocol):
        """Repository protocol for Story entities."""

        async def get_by_app(self, app_slug: str) -> list[Story]:
            """Get all stories for an application."""
            ...

        async def get_by_persona(self, persona: str) -> list[Story]:
            """Get all stories for a persona."""
            ...

    # hcd/infrastructure/repositories/memory/story.py (implementation)
    # Note: no inheritance required - just implement the methods
    class MemoryStoryRepository:
        def __init__(self):
            self._stories: dict[str, Story] = {}

        async def get(self, entity_id: str) -> Story | None:
            return self._stories.get(entity_id)

        async def save(self, entity: Story) -> None:
            self._stories[entity.story_id] = entity

        async def get_by_app(self, app_slug: str) -> list[Story]:
            return [s for s in self._stories.values() if s.app_slug == app_slug]

        # ... etc - implements all protocol methods

**Standard exceptions:**

.. code-block:: python

    # core/repositories/exceptions.py
    class RepositoryError(Exception):
        """Base for repository errors."""

    class EntityNotFound(RepositoryError):
        """Requested entity does not exist."""

    class EntityConflict(RepositoryError):
        """Entity already exists or version conflict."""

The Use Case Idiom
------------------

Use cases are **plain classes** that orchestrate entities and repositories
to accomplish business goals. No base class inheritance required:

.. code-block:: python

    # hcd/use_cases/story/create.py
    from ...repositories.story import StoryRepository
    from ..requests import CreateStoryRequest
    from ..responses import CreateStoryResponse

    class CreateStoryUseCase:
        """Use case for creating a story."""

        def __init__(self, story_repo: StoryRepository) -> None:
            """Initialize with repository dependency."""
            self.story_repo = story_repo

        async def execute(self, request: CreateStoryRequest) -> CreateStoryResponse:
            """Create a new story."""
            story = request.to_domain_model()
            await self.story_repo.save(story)
            return CreateStoryResponse(story=story)

**Request/Response objects** are Pydantic models with conversion methods:

.. code-block:: python

    # hcd/use_cases/requests.py
    from pydantic import BaseModel
    from ..models.story import Story

    class CreateStoryRequest(BaseModel):
        """Request to create a story."""
        title: str
        description: str
        acceptance_criteria: list[str] = []

        def to_domain_model(self) -> Story:
            """Convert request to domain entity."""
            return Story(
                story_id=generate_id(),
                title=self.title,
                description=self.description,
                acceptance_criteria=self.acceptance_criteria,
            )

    # hcd/use_cases/responses.py
    class CreateStoryResponse(BaseModel):
        """Response from creating a story."""
        story: Story

**Key principles:**

1. **Dependency injection**: Repositories passed to constructor
2. **Request/Response objects**: Clear contracts, not loose parameters
3. **Single responsibility**: One use case, one business operation
4. **No infrastructure**: Use cases don't know about HTTP, databases, files

The Infrastructure Idiom
------------------------

Infrastructure provides **concrete implementations** of repository interfaces:

::

    infrastructure/
      repositories/
        memory/          # In-memory (testing, development)
        file/            # File-based (simple persistence)
        minio/           # Object storage
        postgres/        # Relational database

**The pattern:**

.. code-block:: python

    # hcd/infrastructure/repositories/file/story.py
    import json
    from pathlib import Path
    from ....entities import Story
    from ....repositories import StoryRepository

    class FileStoryRepository(StoryRepository):
        def __init__(self, base_path: Path):
            self.base_path = base_path
            self.base_path.mkdir(parents=True, exist_ok=True)

        def _path(self, id: str) -> Path:
            return self.base_path / f"{id}.json"

        async def get(self, id: str) -> Story | None:
            path = self._path(id)
            if not path.exists():
                return None
            return Story.model_validate_json(path.read_text())

        async def save(self, entity: Story) -> Story:
            path = self._path(entity.story_id)
            path.write_text(entity.model_dump_json(indent=2))
            return entity

**Infrastructure reaches inward:**

.. code-block:: python

    # Valid: infrastructure imports from domain
    from ....entities import Story           # ✓
    from ....repositories import StoryRepo   # ✓

    # Invalid: domain imports from infrastructure
    # (This would never appear in entities/ or repositories/)
    from ..infrastructure import FileRepo    # ✗

Why These Idioms?
-----------------

**Immutable entities:**

- Prevent accidental state corruption
- Enable safe sharing across threads/async
- Make debugging easier (entities don't change unexpectedly)
- Support event sourcing patterns

**Protocol-based repositories:**

- Decouple domain from persistence mechanism
- Enable testing with in-memory implementations
- Allow swapping storage without changing domain code
- Make the domain's data needs explicit
- Structural typing: implementations don't inherit, just implement

**Use case classes:**

- Single responsibility, easy to test
- Clear entry points for business operations
- Self-documenting through Request/Response types
- Natural place for transaction boundaries

**Layered infrastructure:**

- Isolate external dependencies
- Organize by technology, not by entity
- Easy to add new storage backends
- Reference implementations guide custom ones

Adopting the Idioms
-------------------

A codebase becomes a "julee solution" by following these patterns:

1. **Entities extend BaseEntity** or follow its conventions
2. **Repositories implement the Repository interface** pattern
3. **Use cases follow the UseCase pattern** with DI
4. **Infrastructure is separated** from domain code
5. **Dependencies point inward** (infrastructure → domain, never reverse)

You don't have to inherit from ``julee.core`` classes—you can follow the
conventions independently. But inheriting gives you:

- Validation that you're following patterns correctly
- Shared utilities (ID generation, timestamps, etc.)
- Compatibility with framework tooling
- Documentation via viewpoints (HCD, C4 can introspect your code)

The Core is the Contract
------------------------

``core/`` is the contract between the framework and solutions. As long as a
solution follows these idioms:

- **Viewpoints work**: HCD and C4 can describe it
- **Applications work**: APIs, MCP, Sphinx extensions can expose it
- **Contrib works**: CEAP, polling, and other modules can integrate

The idioms are the API. Everything else builds on them.

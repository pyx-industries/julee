Accelerator Idioms
==================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

Every accelerator (bounded context) follows the same internal structure.
This consistency enables tooling, documentation generation, and cognitive
ease when navigating unfamiliar codebases.

The structure derives from Clean Architecture, with directory names chosen
to "scream" their purpose.

Internal Structure
------------------

::

    {accelerator}/
      __init__.py
      entities/              # Domain models (innermost layer)
      repositories/          # Abstract interfaces (ports)
      use_cases/             # Application logic
      infrastructure/        # Concrete implementations (adapters)
        repositories/
          file/
          memory/
          minio/
      tests/                 # Co-located tests

Each Layer
----------

entities/
^^^^^^^^^

The innermost layer. Pure domain models with no external dependencies.

.. code-block:: python

    # hcd/entities/story.py
    from pydantic import BaseModel

    class Story(BaseModel):
        story_id: str
        title: str
        description: str
        acceptance_criteria: list[str]

**Rules:**

- No imports from ``repositories/``, ``use_cases/``, or ``infrastructure/``
- May import from ``julee.core.entities`` for base classes
- May import from other entities within the same accelerator
- Pydantic models for validation and serialization

repositories/
^^^^^^^^^^^^^

Abstract interfaces (ports) that define how the domain accesses external
resources.

.. code-block:: python

    # hcd/repositories/story.py
    from abc import ABC, abstractmethod
    from ..entities import Story

    class StoryRepository(ABC):
        @abstractmethod
        async def get(self, story_id: str) -> Story | None: ...

        @abstractmethod
        async def save(self, story: Story) -> Story: ...

        @abstractmethod
        async def list(self) -> list[Story]: ...

**Rules:**

- May import from ``entities/``
- May import from ``julee.core.repositories`` for base classes
- No concrete implementations here—those live in ``infrastructure/``

use_cases/
^^^^^^^^^^

Application logic that orchestrates entities and repositories.

.. code-block:: python

    # hcd/use_cases/create_story.py
    from ..entities import Story
    from ..repositories import StoryRepository

    class CreateStory:
        def __init__(self, story_repo: StoryRepository):
            self.story_repo = story_repo

        async def execute(self, title: str, description: str) -> Story:
            story = Story(
                story_id=generate_id(),
                title=title,
                description=description,
                acceptance_criteria=[],
            )
            return await self.story_repo.save(story)

**Rules:**

- May import from ``entities/`` and ``repositories/``
- Receives repository implementations via dependency injection
- Contains business logic and orchestration
- May be organized in subdirectories by entity or feature

use_cases/ Subdirectory Organization
""""""""""""""""""""""""""""""""""""

For accelerators with many use cases, organize by entity::

    use_cases/
      __init__.py
      requests.py            # Shared request schemas
      responses.py           # Shared response schemas
      story/
        __init__.py
        create.py
        update.py
        delete.py
        get.py
        list.py
      persona/
        __init__.py
        create.py
        ...

infrastructure/
^^^^^^^^^^^^^^^

Concrete implementations of repository interfaces, organized by storage type.

::

    infrastructure/
      __init__.py
      repositories/
        __init__.py
        file/
          __init__.py
          story.py           # FileStoryRepository
          persona.py
        memory/
          __init__.py
          story.py           # MemoryStoryRepository
          persona.py

.. code-block:: python

    # hcd/infrastructure/repositories/memory/story.py
    from ....entities import Story
    from ....repositories import StoryRepository

    class MemoryStoryRepository(StoryRepository):
        def __init__(self):
            self._stories: dict[str, Story] = {}

        async def get(self, story_id: str) -> Story | None:
            return self._stories.get(story_id)

        async def save(self, story: Story) -> Story:
            self._stories[story.story_id] = story
            return story

**Rules:**

- Implements interfaces from ``repositories/``
- May import from ``entities/``
- Contains all external dependencies (file I/O, databases, APIs)
- Organized by storage/adapter type

tests/
^^^^^^

Co-located tests for the accelerator.

::

    tests/
      __init__.py
      entities/
        __init__.py
        test_story.py
        factories.py
      use_cases/
        __init__.py
        test_create_story.py
      infrastructure/
        repositories/
          test_memory_story.py

**Rules:**

- Mirror the source structure
- Factory classes for test data generation
- Unit tests for entities and use cases
- Integration tests for infrastructure

Import Flow
-----------

Imports should flow "inward" (toward entities)::

    infrastructure/ → use_cases/ → repositories/ → entities/
           │              │              │              │
           └──────────────┴──────────────┴──────────────┘
                          all may import from entities

**Valid imports:**

.. code-block:: python

    # In infrastructure/repositories/memory/story.py
    from ....entities import Story           # OK - inward
    from ....repositories import StoryRepo   # OK - inward

**Invalid imports:**

.. code-block:: python

    # In entities/story.py
    from ..repositories import StoryRepo     # BAD - outward
    from ..infrastructure import ...         # BAD - outward

Full Example
------------

::

    hcd/
      __init__.py
      entities/
        __init__.py
        story.py
        persona.py
        journey.py
        epic.py
        accelerator.py
        app.py
        integration.py
      repositories/
        __init__.py
        base.py
        story.py
        persona.py
        journey.py
        epic.py
        accelerator.py
        app.py
        integration.py
      use_cases/
        __init__.py
        requests.py
        responses.py
        story/
          create.py
          update.py
          delete.py
          get.py
          list.py
        persona/
          ...
      infrastructure/
        __init__.py
        repositories/
          __init__.py
          file/
            __init__.py
            story.py
            persona.py
            ...
          memory/
            __init__.py
            story.py
            persona.py
            ...
          rst/
            __init__.py
            story.py
            ...
      tests/
        __init__.py
        entities/
          __init__.py
          test_story.py
          factories.py
        use_cases/
          test_create_story.py

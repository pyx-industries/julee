Dependency Layers
=================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

Julee follows Clean Architecture's dependency rule: **dependencies point
inward**. This principle applies at two levels:

1. **Within an accelerator**: Infrastructure depends on use cases, which
   depend on repositories, which depend on entities.

2. **Across the solution**: Deployment depends on applications, which depend
   on accelerators, which depend on core.

The filesystem structure reflects this: conceptually, "inward" maps to
"parentward" in the directory hierarchy.

The Dependency Rule
-------------------

Uncle Bob's Clean Architecture defines concentric circles, with dependencies
always pointing toward the center::

    ┌─────────────────────────────────────────────┐
    │  Frameworks & Drivers (outermost)           │
    │  ┌─────────────────────────────────────┐    │
    │  │  Interface Adapters                 │    │
    │  │  ┌─────────────────────────────┐    │    │
    │  │  │  Application Business Rules │    │    │
    │  │  │  ┌─────────────────────┐    │    │    │
    │  │  │  │  Entities (core)    │    │    │    │
    │  │  │  └─────────────────────┘    │    │    │
    │  │  └─────────────────────────────┘    │    │
    │  └─────────────────────────────────────┘    │
    └─────────────────────────────────────────────┘

Nothing in an inner circle can know about anything in an outer circle.

Within an Accelerator
---------------------

Inside each accelerator, the layers map to directories::

    {accelerator}/
      entities/           # Innermost - knows nothing
      repositories/       # Depends on entities
      use_cases/          # Depends on entities + repositories
      infrastructure/     # Outermost - depends on everything above

**Valid imports (inward/parentward):**

.. code-block:: python

    # infrastructure/repositories/memory/story.py
    from ....entities import Story           # ✓ Goes inward
    from ....repositories import StoryRepo   # ✓ Goes inward

    # use_cases/create_story.py
    from ..entities import Story             # ✓ Goes inward
    from ..repositories import StoryRepo     # ✓ Goes inward

    # repositories/story.py
    from ..entities import Story             # ✓ Goes inward

**Invalid imports (outward):**

.. code-block:: python

    # entities/story.py
    from ..repositories import StoryRepo     # ✗ Goes outward!
    from ..use_cases import CreateStory      # ✗ Goes outward!

    # repositories/story.py
    from ..infrastructure import ...         # ✗ Goes outward!

Across the Solution
-------------------

At the solution level, the same principle applies::

    {solution}/
      core/               # Innermost - the idioms
      {viewpoints}/       # Depend on core
      contrib/            # Depends on core
      applications/       # Depends on viewpoints + contrib
      docs/               # Depends on applications
      deployment/         # Depends on applications

**Dependency graph:**

::

              ┌─────────────┐     ┌──────┐
              │ deployment/ │     │docs/ │
              └──────┬──────┘     └──┬───┘
                     │               │
                     └───────┬───────┘
                             ▼
                    ┌──────────────┐
                    │applications/ │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      ┌──────┐        ┌──────┐       ┌──────────┐
      │ hcd/ │        │ c4/  │       │ contrib/ │
      └──┬───┘        └──┬───┘       └────┬─────┘
         │               │                │
         └───────────────┼────────────────┘
                         ▼
                    ┌─────────┐
                    │  core/  │
                    └─────────┘

**Valid imports:**

.. code-block:: python

    # applications/api/hcd/routers/story.py
    from julee.hcd.entities import Story           # ✓
    from julee.hcd.use_cases import CreateStory    # ✓
    from julee.core.entities import BaseEntity     # ✓

    # hcd/entities/story.py
    from julee.core.entities import BaseEntity     # ✓

    # docs/conf.py
    from julee.applications.sphinx.hcd import setup  # ✓

**Invalid imports:**

.. code-block:: python

    # core/entities/base.py
    from julee.hcd.entities import Story           # ✗ Core can't know HCD!

    # hcd/entities/story.py
    from julee.applications.api import ...         # ✗ Domain can't know apps!

Parentward = Inward
-------------------

The filesystem metaphor: **imports should trend toward ``../`` (parent)**,
not ``./subdir/`` (child).

Within an accelerator, moving from ``infrastructure/`` to ``entities/``
means going up the directory tree::

    infrastructure/repositories/memory/story.py
                   ↓
    from ....entities import Story
         └── four levels up

Reaching "up" to a parent is reaching "in" to the core.

A module can freely import from its children (it owns them), but a child
reaching into a sibling's children is a smell:

.. code-block:: python

    # Bad: sibling reaching into sibling's internals
    # hcd/entities/story.py
    from ..use_cases.create_story import CreateStory  # ✗

Practical Guidelines
--------------------

1. **Entities import only from core and other entities**

   .. code-block:: python

       # hcd/entities/story.py
       from julee.core.entities import BaseEntity
       from .persona import Persona  # OK - same layer

2. **Repositories import from entities**

   .. code-block:: python

       # hcd/repositories/story.py
       from ..entities import Story

3. **Use cases import from entities and repositories**

   .. code-block:: python

       # hcd/use_cases/create_story.py
       from ..entities import Story
       from ..repositories import StoryRepository

4. **Infrastructure implements repository interfaces**

   .. code-block:: python

       # hcd/infrastructure/repositories/memory/story.py
       from ....entities import Story
       from ....repositories import StoryRepository

5. **Applications wire everything together**

   .. code-block:: python

       # applications/api/hcd/dependencies.py
       from julee.hcd.repositories import StoryRepository
       from julee.hcd.infrastructure.repositories.memory import (
           MemoryStoryRepository
       )

Dependency Injection
--------------------

The dependency rule is enforced through dependency injection. Inner layers
define interfaces; outer layers provide implementations:

.. code-block:: python

    # hcd/repositories/story.py (inner - defines interface)
    class StoryRepository(ABC):
        @abstractmethod
        async def save(self, story: Story) -> Story: ...

    # hcd/use_cases/create_story.py (middle - uses interface)
    class CreateStory:
        def __init__(self, repo: StoryRepository):  # Injected
            self.repo = repo

    # applications/api/hcd/dependencies.py (outer - provides implementation)
    def get_story_repository() -> StoryRepository:
        return MemoryStoryRepository()  # Concrete implementation

The use case doesn't know (or care) whether it gets a memory repository, a
file repository, or a PostgreSQL repository. It only knows the interface.

Violations and Smells
---------------------

**Circular imports**: Usually indicate a dependency rule violation. If A
imports B and B imports A, one of them is reaching the wrong direction.

**God modules**: A module that imports from every layer is probably doing
too much. Split it along layer boundaries.

**Leaking infrastructure**: If entity code imports ``requests`` or ``boto3``,
infrastructure has leaked into the domain. Wrap it in a repository interface.

**Test imports**: Tests can import from any layer (they're outside the
circles), but test utilities should follow the same rules as production code.

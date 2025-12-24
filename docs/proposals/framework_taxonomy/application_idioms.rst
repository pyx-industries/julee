Application Idioms
==================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

The ``applications/`` directory contains the exposure layer—how the solution
presents itself to the outside world. Each application type has its own
idiom (internal structure), but all follow the pattern::

    applications/{app_type}/{accelerator}/{idiom_files}

Application Types
-----------------

.. list-table::
   :header-rows: 1
   :widths: 15 30 55

   * - Type
     - Purpose
     - Exposes to
   * - ``api/``
     - REST/HTTP APIs
     - Machines, frontend applications
   * - ``mcp/``
     - Model Context Protocol servers
     - AI agents, LLM tools
   * - ``sphinx/``
     - Sphinx documentation extensions
     - Humans (via rendered docs)
   * - ``worker/``
     - Background job processors
     - Workflow engines (Temporal)

Structure
---------

::

    applications/
      api/
        {accelerator}/
          app.py
          dependencies.py
          requests.py
          responses.py
          routers/
      mcp/
        {accelerator}/
          server.py
          context.py
          tools/
      sphinx/
        {accelerator}/
          __init__.py
          config.py
          directives/
          event_handlers/
      worker/
        {accelerator}/
          activities.py
          workflows.py

API Idiom
---------

FastAPI-based REST APIs.

::

    api/{accelerator}/
      __init__.py
      app.py               # FastAPI app factory
      dependencies.py      # Dependency injection setup
      requests.py          # Pydantic request schemas
      responses.py         # Pydantic response schemas
      routers/
        __init__.py
        {entity}.py        # Routes for each entity

**app.py** - Application factory:

.. code-block:: python

    from fastapi import FastAPI
    from .routers import story, persona

    def create_app() -> FastAPI:
        app = FastAPI(title="HCD API")
        app.include_router(story.router, prefix="/stories", tags=["stories"])
        app.include_router(persona.router, prefix="/personas", tags=["personas"])
        return app

**dependencies.py** - Dependency injection:

.. code-block:: python

    from functools import lru_cache
    from julee.hcd.repositories import StoryRepository
    from julee.hcd.infrastructure.repositories.memory import MemoryStoryRepository

    @lru_cache
    def get_story_repository() -> StoryRepository:
        return MemoryStoryRepository()

**routers/{entity}.py** - Route handlers:

.. code-block:: python

    from fastapi import APIRouter, Depends
    from ..dependencies import get_story_repository
    from ..requests import CreateStoryRequest
    from ..responses import StoryResponse

    router = APIRouter()

    @router.post("/", response_model=StoryResponse)
    async def create_story(
        request: CreateStoryRequest,
        repo: StoryRepository = Depends(get_story_repository),
    ):
        use_case = CreateStory(repo)
        story = await use_case.execute(request.title, request.description)
        return StoryResponse.from_entity(story)

**Default routing convention:**

A naive implementation exposes CRUD at ``/{accelerator}/{entity}``:

- ``GET /hcd/stories`` - List stories
- ``POST /hcd/stories`` - Create story
- ``GET /hcd/stories/{id}`` - Get story
- ``PUT /hcd/stories/{id}`` - Update story
- ``DELETE /hcd/stories/{id}`` - Delete story

MCP Idiom
---------

Model Context Protocol servers for AI agent integration.

::

    mcp/{accelerator}/
      __init__.py
      server.py            # MCP server setup
      context.py           # State management
      tools/
        __init__.py
        {entity}.py        # Tools for each entity

**server.py** - Server setup:

.. code-block:: python

    from mcp import Server
    from .tools import story_tools, persona_tools

    def create_server() -> Server:
        server = Server("hcd")
        server.register_tools(story_tools)
        server.register_tools(persona_tools)
        return server

**tools/{entity}.py** - Tool definitions:

.. code-block:: python

    from mcp import tool

    @tool
    async def create_story(title: str, description: str) -> dict:
        """Create a new user story."""
        use_case = CreateStory(get_story_repository())
        story = await use_case.execute(title, description)
        return story.model_dump()

    @tool
    async def list_stories() -> list[dict]:
        """List all user stories."""
        use_case = ListStories(get_story_repository())
        stories = await use_case.execute()
        return [s.model_dump() for s in stories]

Sphinx Idiom
------------

Sphinx extensions for rendering viewpoints as documentation.

::

    sphinx/{accelerator}/
      __init__.py          # Extension entry point
      config.py            # Configuration values
      directives/
        __init__.py
        {directive}.py     # RST directive implementations
      event_handlers/
        __init__.py
        doctree_resolved.py
      adapters.py          # Connect to accelerator repositories

**__init__.py** - Extension entry point:

.. code-block:: python

    from sphinx.application import Sphinx
    from .config import DEFAULT_CONFIG
    from .directives import register_directives
    from .event_handlers import register_handlers

    def setup(app: Sphinx) -> dict:
        for key, default in DEFAULT_CONFIG.items():
            app.add_config_value(key, default, "env")

        register_directives(app)
        register_handlers(app)

        return {"version": "0.1.0", "parallel_read_safe": True}

**directives/{directive}.py** - RST directives:

.. code-block:: python

    from docutils.parsers.rst import Directive
    from sphinx.application import Sphinx

    class DefineStoryDirective(Directive):
        required_arguments = 1  # story ID
        has_content = True

        def run(self):
            story_id = self.arguments[0]
            # Parse content, register with environment
            ...

Worker Idiom
------------

Background job processors, typically Temporal workflows.

::

    worker/{accelerator}/
      __init__.py
      activities.py        # Temporal activities
      workflows.py         # Temporal workflows
      worker.py            # Worker setup

**activities.py** - Temporal activities:

.. code-block:: python

    from temporalio import activity
    from julee.hcd.use_cases import CreateStory

    @activity.defn
    async def create_story_activity(title: str, description: str) -> dict:
        use_case = CreateStory(get_story_repository())
        story = await use_case.execute(title, description)
        return story.model_dump()

**workflows.py** - Temporal workflows:

.. code-block:: python

    from temporalio import workflow
    from .activities import create_story_activity

    @workflow.defn
    class StoryWorkflow:
        @workflow.run
        async def run(self, title: str, description: str) -> dict:
            return await workflow.execute_activity(
                create_story_activity,
                args=[title, description],
                start_to_close_timeout=timedelta(seconds=30),
            )

Deployment Flexibility
----------------------

The idiom provides sensible defaults, but deployment can compose differently:

.. code-block:: python

    # Option A: One API serving all accelerators
    app = FastAPI()
    app.mount("/hcd", create_hcd_app())
    app.mount("/c4", create_c4_app())
    app.mount("/ceap", create_ceap_app())

    # Option B: Separate microservices
    # Deploy api/hcd/ as one service
    # Deploy api/ceap/ as another service

    # Option C: Mix and match
    public_app = FastAPI()
    public_app.mount("/hcd", create_hcd_app())  # Public
    # Deploy api/ceap/ internally only

The idioms give you **convention over configuration**: follow the structure
and it works. Need something custom? Compose the pieces differently.

Shared Code
-----------

Common utilities across applications live in ``applications/shared/``:

::

    applications/
      shared/
        __init__.py
        auth.py              # Authentication utilities
        middleware.py        # Common middleware
        pagination.py        # Pagination helpers
      api/
        ...
      mcp/
        ...

Applications import from shared:

.. code-block:: python

    from ..shared.auth import require_auth
    from ..shared.pagination import paginate

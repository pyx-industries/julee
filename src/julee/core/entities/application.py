"""Application domain model.

Applications are the entry points to a Julee solution. They turn use cases into
features that users or external systems can access.

All application types wire the same domain use cases. The application type
determines HOW use cases are invoked, not WHAT business logic runs.

Applications are orthogonal to bounded contexts:
- Bounded contexts define domain boundaries (entities, repositories, use cases)
- Applications compose and expose bounded context capabilities

Application Types
-----------------
A typical Julee solution includes multiple application types:

**REST-API** - Expose use cases as REST endpoints using FastAPI. APIs execute
use cases directly for synchronous operations, or trigger worker pipelines via
Temporal client for asynchronous operations. Use cases receive dependencies
(repositories, services) via FastAPI's dependency injection. Request and response
models are Pydantic models separate from domain models, providing API contracts
that can evolve independently. UIs interact with the system exclusively through
the API.

**TEMPORAL-WORKER** - Poll for work and execute pipeline activities. Workers are
the application type for long-running, reliable processes with audit trails.
Workers connect to a Temporal server and poll a task queue. When a pipeline is
triggered, Temporal schedules activities which the worker executes. Each activity
represents a use case step - fetching documents, calling AI services, storing
results. Temporal records the execution history, enabling replay and recovery.
Temporal automatically retries failed activities with configurable backoff.
Multiple worker instances can run concurrently; Temporal distributes work across
them. Workflow code must be deterministic for replay; side effects belong in
activities.

**CLI** - Expose use cases via command-line interfaces. CLI commands instantiate
and execute use cases directly, or trigger worker pipelines for asynchronous
operations. CLIs read configuration from environment variables or config files.
Common uses include administrative tasks, development and debugging, batch
operations, and system initialization. Unlike UIs, CLIs invoke use cases directly
rather than going through the API.

**MCP** - Model Context Protocol servers that expose use cases to AI assistants.

**SPHINX-EXTENSION** - Sphinx extensions that render documentation from solution
content using directives that call read use cases.

UI Note
-------
UI applications provide user interfaces for Julee solutions. They interact with
the system exclusively through the API - UIs don't have direct access to domain
use cases, repositories, services, or Temporal workflows. Julee is framework-
agnostic for UIs; any frontend technology (React, Vue, Svelte, HTMX) can be used.

Directory Convention
--------------------
The ``apps/`` directory is a reserved word - it cannot be a bounded context name.
Applications live at ``{solution}/apps/`` and may internally organize themselves
using bounded-context-based structural conventions.
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class AppType(str, Enum):
    """Classification of application types.

    Each type has its own structural conventions and doctrine requirements.
    """

    REST_API = "REST-API"
    MCP = "MCP"
    SPHINX_EXTENSION = "SPHINX-EXTENSION"
    TEMPORAL_WORKER = "TEMPORAL-WORKER"
    CLI = "CLI"


class AppStructuralMarkers(BaseModel):
    """Structural markers indicating what an application contains.

    These markers reflect the type-specific structure present in an
    application. Detection of these markers helps classify app type
    and verify doctrine compliance.
    """

    # Common markers
    has_tests: bool = False
    has_dependencies: bool = False  # dependencies.py or similar DI setup

    # REST-API specific
    has_routers: bool = False

    # MCP specific
    has_tools: bool = False

    # SPHINX-EXTENSION specific
    has_directives: bool = False

    # TEMPORAL-WORKER specific
    has_pipelines: bool = False
    has_activities: bool = False

    # CLI specific
    has_commands: bool = False

    # Organizational pattern
    uses_bc_organization: bool = False  # Has BC-named subdirectories


class Application(BaseModel):
    """A deployable/runnable composition of bounded context capabilities.

    In Clean Architecture terms, applications live in the outermost layer
    (Frameworks & Drivers). They compose use cases from one or more bounded
    contexts and expose them through a specific interface (REST, MCP, CLI, etc.).

    Applications are discovered at `{solution}/apps/` and may internally
    organize themselves using bounded-context-based structural conventions.
    For example, `apps/api/ceap/` and `apps/api/hcd/` are organizational
    subdivisions within a single REST-API application, not separate applications.

    Doctrine: Apps MAY internally organize themselves using BC-based structural
    conventions. REST-API and TEMPORAL-WORKER applications typically do this.
    """

    # Identity
    slug: str = Field(description="Directory name, e.g., 'api', 'admin', 'worker'")
    path: str = Field(description="Filesystem path relative to project root")

    # Classification
    app_type: AppType = Field(description="Type of application")

    # Structure
    markers: AppStructuralMarkers = Field(
        default_factory=AppStructuralMarkers,
        description="What structural elements this application contains",
    )

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @property
    def absolute_path(self) -> Path:
        """Get path as a Path object."""
        return Path(self.path)

    @property
    def display_name(self) -> str:
        """Human-readable name derived from slug and type."""
        name = self.slug.replace("-", " ").replace("_", " ").title()
        return f"{name} ({self.app_type.value})"

    @property
    def bc_subdirs(self) -> list[str]:
        """List BC-organized subdirectories if uses_bc_organization is True.

        Returns empty list if not using BC organization.
        """
        if not self.markers.uses_bc_organization:
            return []

        subdirs = []
        app_path = Path(self.path)
        if app_path.exists():
            for child in app_path.iterdir():
                if child.is_dir() and not child.name.startswith(("_", ".")):
                    if child.name not in ("shared", "tests", "__pycache__"):
                        if (child / "__init__.py").exists():
                            subdirs.append(child.name)
        return sorted(subdirs)

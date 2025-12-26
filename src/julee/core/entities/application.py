"""Application domain model.

Represents an application as a code structure, independent of any specific
framework or runtime. Applications are deployable/runnable compositions that
depend on one or more bounded contexts.

Applications are orthogonal to bounded contexts:
- Bounded contexts define domain boundaries (entities, repositories, use cases)
- Applications compose and expose bounded context capabilities

The `apps/` directory is a reserved word - it cannot be a bounded context name.
Applications live at `{solution}/apps/` and may internally organize themselves
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

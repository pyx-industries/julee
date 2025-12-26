"""Solution domain model.

Represents a solution as the top-level organizational container for a julee
project. A solution aggregates bounded contexts, applications, and optionally
nested solutions into a coherent unit.

Doctrine:
- Solution MAY contain one or more Bounded Contexts
- Solution MAY contain one or more Applications
- Solution MAY contain one or more nested Solutions

The canonical structure is:
    {solution}/
    ├── src/julee/           # Bounded contexts live here
    │   ├── core/            # Core BC
    │   ├── hcd/             # HCD BC
    │   └── contrib/         # Nested solution container
    │       ├── ceap/        # BC with optional apps/
    │       └── polling/     # BC with optional apps/
    └── apps/                # Applications live here
        ├── api/
        ├── mcp/
        └── worker/

Nested solutions (like contrib/) follow the same structure recursively.
BCs within nested solutions may contain reference applications at {bc}/apps/.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from julee.core.entities.application import Application
from julee.core.entities.bounded_context import BoundedContext


class Solution(BaseModel):
    """The top-level organizational container for a julee project.

    A solution aggregates bounded contexts (domain logic) and applications
    (deployment artifacts) into a coherent namespace. Solutions can be nested;
    for example, `contrib/` is a nested solution containing batteries-included
    bounded contexts with their reference applications.
    """

    # Identity
    name: str = Field(description="Solution name, typically derived from directory")
    path: str = Field(description="Absolute filesystem path to solution root")

    # Contents
    bounded_contexts: list[BoundedContext] = Field(
        default_factory=list,
        description="Bounded contexts discovered in this solution",
    )
    applications: list[Application] = Field(
        default_factory=list,
        description="Applications discovered in this solution",
    )
    nested_solutions: list[Solution] = Field(
        default_factory=list,
        description="Nested solutions (e.g., contrib/) within this solution",
    )

    # Configuration
    is_nested: bool = Field(
        default=False,
        description="True if this is a nested solution (not the root)",
    )
    parent_path: str | None = Field(
        default=None,
        description="Path to parent solution if nested",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @property
    def absolute_path(self) -> Path:
        """Get path as a Path object."""
        return Path(self.path)

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return self.name.replace("-", " ").replace("_", " ").title()

    @property
    def all_bounded_contexts(self) -> list[BoundedContext]:
        """All bounded contexts including those in nested solutions."""
        contexts = list(self.bounded_contexts)
        for nested in self.nested_solutions:
            contexts.extend(nested.all_bounded_contexts)
        return contexts

    @property
    def all_applications(self) -> list[Application]:
        """All applications including those in nested solutions."""
        apps = list(self.applications)
        for nested in self.nested_solutions:
            apps.extend(nested.all_applications)
        return apps

    def get_bounded_context(self, slug: str) -> BoundedContext | None:
        """Find a bounded context by slug, searching nested solutions."""
        for bc in self.bounded_contexts:
            if bc.slug == slug:
                return bc
        for nested in self.nested_solutions:
            bc = nested.get_bounded_context(slug)
            if bc:
                return bc
        return None

    def get_application(self, slug: str) -> Application | None:
        """Find an application by slug, searching nested solutions."""
        for app in self.applications:
            if app.slug == slug:
                return app
        for nested in self.nested_solutions:
            app = nested.get_application(slug)
            if app:
                return app
        return None

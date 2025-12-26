"""Solution domain model.

Represents a solution as the top-level organizational container for a julee
project. A solution aggregates bounded contexts, applications, deployments,
documentation, and optionally nested solutions into a coherent unit.

Doctrine:
- Solution MUST have documentation (docs/)
- Solution MAY contain one or more Bounded Contexts
- Solution MAY contain one or more Applications
- Solution MAY contain one or more Deployments
- Solution MAY contain one or more nested Solutions

The dependency chain flows outward:
    Deployment → Application → BoundedContext

The canonical structure is:
    {solution}/
    ├── docs/                # Documentation (REQUIRED)
    │   ├── conf.py          # Sphinx configuration
    │   ├── Makefile         # Build with 'make html'
    │   └── index.rst        # Entry point
    ├── src/{solution}/      # Bounded contexts live here
    │   ├── {bc}/            # Bounded context directories
    │   └── {nested}/        # Optional nested solution(s)
    │       └── {bc}/        # Bounded contexts in nested solution
    ├── apps/                # Applications live here
    │   └── {app}/           # Application directories
    └── deployments/         # Deployments live here
        └── {env}/           # Environment directories
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from julee.core.entities.application import Application
from julee.core.entities.bounded_context import BoundedContext
from julee.core.entities.deployment import Deployment
from julee.core.entities.documentation import Documentation


class Solution(BaseModel):
    """The top-level organizational container for a julee project.

    A solution aggregates bounded contexts (domain logic), applications
    (runnable compositions), and deployments (infrastructure configurations)
    into a coherent namespace. Solutions can be nested; for example, `contrib/`
    is a nested solution containing batteries-included bounded contexts with
    their reference applications.

    The dependency chain flows outward: Deployment → Application → BoundedContext.
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
    deployments: list[Deployment] = Field(
        default_factory=list,
        description="Deployments discovered in this solution",
    )
    nested_solutions: list[Solution] = Field(
        default_factory=list,
        description="Nested solutions (e.g., contrib/) within this solution",
    )
    documentation: Documentation | None = Field(
        default=None,
        description="Documentation configuration (docs/ directory)",
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

    @property
    def all_deployments(self) -> list[Deployment]:
        """All deployments including those in nested solutions."""
        deps = list(self.deployments)
        for nested in self.nested_solutions:
            deps.extend(nested.all_deployments)
        return deps

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

    def get_deployment(self, slug: str) -> Deployment | None:
        """Find a deployment by slug, searching nested solutions."""
        for dep in self.deployments:
            if dep.slug == slug:
                return dep
        for nested in self.nested_solutions:
            dep = nested.get_deployment(slug)
            if dep:
                return dep
        return None

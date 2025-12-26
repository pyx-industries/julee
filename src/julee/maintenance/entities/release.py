"""Release entity.

A Release represents a versioned release of the solution. Releases progress
through states: prepared (branch created, PR opened) -> tagged (merged and tagged).

The maintenance bounded context operates on releases, deployments, applications,
and bounded contexts - the things that are maintained over time.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ReleaseState(str, Enum):
    """State of a release in the release process."""

    DRAFT = "draft"  # Release notes being prepared
    PREPARED = "prepared"  # Branch created, PR opened
    MERGED = "merged"  # PR merged to main
    TAGGED = "tagged"  # Git tag created and pushed


class Release(BaseModel):
    """A versioned release of the solution.

    Releases follow semantic versioning (X.Y.Z) and progress through
    a defined lifecycle from draft to tagged.
    """

    version: str = Field(description="Semantic version string (X.Y.Z)")
    state: ReleaseState = Field(
        default=ReleaseState.DRAFT, description="Current state in release process"
    )
    branch_name: str | None = Field(
        default=None, description="Release branch name (release/vX.Y.Z)"
    )
    tag_name: str | None = Field(default=None, description="Git tag name (vX.Y.Z)")
    notes: str | None = Field(default=None, description="Release notes content")

    @field_validator("version", mode="before")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        import re

        if not v or not v.strip():
            raise ValueError("version cannot be empty")
        v = v.strip()
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError(f"version must be X.Y.Z format, got: {v}")
        return v

    @property
    def computed_branch_name(self) -> str:
        """Get the standard branch name for this release."""
        return f"release/v{self.version}"

    @property
    def computed_tag_name(self) -> str:
        """Get the standard tag name for this release."""
        return f"v{self.version}"

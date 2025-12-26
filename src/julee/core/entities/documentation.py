"""Documentation domain model.

Represents a solution's documentation configuration. Every julee solution MUST
have a docs/ directory with valid Sphinx configuration.

Doctrine:
- Solution MUST have docs/ directory
- docs/ MUST have a valid Sphinx conf.py
- docs/ MUST have a Makefile with 'make html' target

The `docs/` directory is a reserved word - it cannot be a bounded context name.
Documentation lives at `{solution}/docs/` and contains Sphinx configuration
for building solution documentation.
"""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class DocumentationStructuralMarkers(BaseModel):
    """Structural markers indicating documentation configuration.

    These markers are used to verify that documentation is properly
    configured according to doctrine requirements.
    """

    # Sphinx markers
    has_conf_py: bool = Field(
        default=False, description="Has Sphinx conf.py configuration"
    )
    has_makefile: bool = Field(default=False, description="Has Makefile for building")
    has_index_rst: bool = Field(
        default=False, description="Has index.rst entry point"
    )

    # Build infrastructure
    has_make_html_target: bool = Field(
        default=False, description="Makefile has 'html' target"
    )

    # Optional markers
    has_api_docs: bool = Field(
        default=False, description="Has API documentation directory"
    )
    has_static: bool = Field(
        default=False, description="Has _static directory for assets"
    )
    has_templates: bool = Field(
        default=False, description="Has _templates directory"
    )


class Documentation(BaseModel):
    """Documentation configuration for a julee solution.

    Every julee solution MUST have documentation. The documentation uses
    Sphinx as the standard tool for building docs from reStructuredText
    and integrates with the HCD and C4 bounded contexts for generating
    domain-specific documentation.
    """

    # Identity
    path: str = Field(description="Absolute filesystem path to docs directory")

    # Structure
    markers: DocumentationStructuralMarkers = Field(
        default_factory=DocumentationStructuralMarkers,
        description="Structural markers indicating documentation contents",
    )

    # Configuration
    sphinx_project: str | None = Field(
        default=None, description="Sphinx project name from conf.py"
    )
    sphinx_version: str | None = Field(
        default=None, description="Sphinx version requirement"
    )

    @property
    def absolute_path(self) -> Path:
        """Get path as a Path object."""
        return Path(self.path)

    @property
    def is_valid_sphinx(self) -> bool:
        """True if documentation has valid Sphinx configuration."""
        return self.markers.has_conf_py and self.markers.has_makefile

    @property
    def is_buildable(self) -> bool:
        """True if documentation can be built with 'make html'."""
        return self.markers.has_makefile and self.markers.has_make_html_target

    @field_validator("path", mode="before")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path is not empty."""
        if not v or not v.strip():
            raise ValueError("path cannot be empty")
        return v.strip()

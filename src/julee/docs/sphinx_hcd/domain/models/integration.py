"""Integration domain model.

Represents an integration module in the HCD documentation system.
Integrations are defined via YAML manifests in integrations/*/integration.yaml.
"""

from enum import StrEnum

from pydantic import Field, field_validator

from julee.core.entities.entity import Entity

from ...utils import normalize_name


class Direction(StrEnum):
    """Integration data flow direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"

    @classmethod
    def from_string(cls, value: str) -> "Direction":
        """Convert string to Direction, defaulting to BIDIRECTIONAL."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.BIDIRECTIONAL

    @property
    def label(self) -> str:
        """Get human-readable label."""
        labels = {
            Direction.INBOUND: "Inbound (data source)",
            Direction.OUTBOUND: "Outbound (data sink)",
            Direction.BIDIRECTIONAL: "Bidirectional",
        }
        return labels.get(self, str(self.value))


class ExternalDependency(Entity):
    """External system that an integration depends on."""

    name: str = Field(description="Display name of the external system")
    url: str | None = Field(
        default=None, description="Optional URL for documentation or reference"
    )
    description: str = Field(default="", description="Optional brief description")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @classmethod
    def from_dict(cls, data: dict) -> "ExternalDependency":
        """Create from dictionary (YAML parsed data).

        Args:
            data: Dictionary with name, url, description keys

        Returns:
            ExternalDependency instance
        """
        return cls(
            name=data.get("name", ""),
            url=data.get("url"),
            description=data.get("description", ""),
        )


class Integration(Entity):
    """Integration module entity.

    Integrations represent connections to external systems, defining
    data flow direction and external dependencies.
    """

    slug: str = Field(description='URL-safe identifier (e.g., "pilot-data-collection")')
    module: str = Field(
        description='Python module name (e.g., "pilot_data_collection")'
    )
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Human-readable description")
    direction: Direction = Field(
        default=Direction.BIDIRECTIONAL, description="Data flow direction"
    )
    depends_on: tuple[ExternalDependency, ...] = Field(
        default_factory=tuple, description="List of external dependencies"
    )
    manifest_path: str = Field(
        default="", description="Path to the integration.yaml file"
    )
    name_normalized: str = Field(default="", description="Lowercase name for matching")

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
        return v.strip()

    @field_validator("module", mode="before")
    @classmethod
    def validate_module(cls, v: str) -> str:
        """Validate module is not empty."""
        if not v or not v.strip():
            raise ValueError("module cannot be empty")
        return v.strip()

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("name_normalized", mode="before")
    @classmethod
    def compute_name_normalized(cls, v: str, info) -> str:
        """Compute normalized name from name if not provided."""
        if v:
            return v
        name = info.data.get("name", "")
        return normalize_name(name) if name else ""

    def model_post_init(self, __context) -> None:
        """Ensure normalized fields are computed after init."""
        if not self.name_normalized and self.name:
            object.__setattr__(self, "name_normalized", normalize_name(self.name))

    @classmethod
    def from_manifest(
        cls,
        module_name: str,
        manifest: dict,
        manifest_path: str,
    ) -> "Integration":
        """Create an Integration from a parsed YAML manifest.

        Args:
            module_name: Module directory name
            manifest: Parsed YAML content
            manifest_path: Path to the manifest file

        Returns:
            Integration instance
        """
        slug = manifest.get("slug", module_name.replace("_", "-"))
        name = manifest.get("name", slug.replace("-", " ").title())
        direction = Direction.from_string(manifest.get("direction", "bidirectional"))

        # Parse depends_on list
        depends_on_raw = manifest.get("depends_on", [])
        depends_on = [
            (
                ExternalDependency.from_dict(dep)
                if isinstance(dep, dict)
                else ExternalDependency(name=str(dep))
            )
            for dep in depends_on_raw
        ]

        return cls(
            slug=slug,
            module=module_name,
            name=name,
            description=manifest.get("description", "").strip(),
            direction=direction,
            depends_on=tuple(depends_on),
            manifest_path=manifest_path,
        )

    def matches_direction(self, direction: Direction | str) -> bool:
        """Check if this integration matches the given direction.

        Args:
            direction: Direction enum or string to match

        Returns:
            True if integration matches the direction
        """
        if isinstance(direction, str):
            direction = Direction.from_string(direction)
        return self.direction == direction

    def matches_name(self, name: str) -> bool:
        """Check if this integration matches the given name (case-insensitive).

        Args:
            name: Name to match against

        Returns:
            True if normalized names match
        """
        return self.name_normalized == normalize_name(name)

    def has_dependency(self, dep_name: str) -> bool:
        """Check if this integration has a specific dependency.

        Args:
            dep_name: Dependency name to check (case-insensitive)

        Returns:
            True if dependency exists
        """
        dep_normalized = normalize_name(dep_name)
        return any(
            normalize_name(dep.name) == dep_normalized for dep in self.depends_on
        )

    @property
    def direction_label(self) -> str:
        """Get human-readable direction label."""
        return self.direction.label

    @property
    def module_path(self) -> str:
        """Get full module path for display."""
        return f"integrations.{self.module}"

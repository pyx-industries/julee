"""App domain model.

Represents an application in the HCD documentation system.
Apps are defined via YAML manifests in apps/*/app.yaml.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from ...utils import normalize_name


class AppType(str, Enum):
    """Application type classification."""

    STAFF = "staff"
    EXTERNAL = "external"
    MEMBER_TOOL = "member-tool"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "AppType":
        """Convert string to AppType, defaulting to UNKNOWN."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.UNKNOWN


class App(BaseModel):
    """Application entity.

    Apps represent distinct applications in the system, defined via YAML
    manifests. They serve as containers for stories and provide organization
    for the documentation.

    Attributes:
        slug: URL-safe identifier (e.g., "staff-portal")
        name: Display name (e.g., "Staff Portal")
        app_type: Classification (staff, external, member-tool)
        status: Optional status indicator (e.g., "in-development", "live")
        description: Human-readable description
        accelerators: List of accelerator slugs associated with this app
        manifest_path: Path to the app.yaml file
        name_normalized: Lowercase name for matching
    """

    slug: str
    name: str
    app_type: AppType = AppType.UNKNOWN
    status: str | None = None
    description: str = ""
    accelerators: list[str] = Field(default_factory=list)
    manifest_path: str = ""
    name_normalized: str = ""

    # Document structure (RST round-trip)
    page_title: str = ""
    preamble_rst: str = ""
    epilogue_rst: str = ""

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug is not empty."""
        if not v or not v.strip():
            raise ValueError("slug cannot be empty")
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
        slug: str,
        manifest: dict,
        manifest_path: str,
    ) -> "App":
        """Create an App from a parsed YAML manifest.

        Args:
            slug: App slug (usually directory name)
            manifest: Parsed YAML content
            manifest_path: Path to the manifest file

        Returns:
            App instance
        """
        name = manifest.get("name", slug.replace("-", " ").title())
        app_type = AppType.from_string(manifest.get("type", "unknown"))

        return cls(
            slug=slug,
            name=name,
            app_type=app_type,
            status=manifest.get("status"),
            description=manifest.get("description", "").strip(),
            accelerators=manifest.get("accelerators", []),
            manifest_path=manifest_path,
        )

    def matches_type(self, app_type: AppType | str) -> bool:
        """Check if this app matches the given type.

        Args:
            app_type: AppType enum or string to match

        Returns:
            True if app matches the type
        """
        if isinstance(app_type, str):
            app_type = AppType.from_string(app_type)
        return self.app_type == app_type

    def matches_name(self, name: str) -> bool:
        """Check if this app matches the given name (case-insensitive).

        Args:
            name: Name to match against

        Returns:
            True if normalized names match
        """
        return self.name_normalized == normalize_name(name)

    @property
    def type_label(self) -> str:
        """Get human-readable type label."""
        labels = {
            AppType.STAFF: "Staff Application",
            AppType.EXTERNAL: "External Application",
            AppType.MEMBER_TOOL: "Member Tool",
            AppType.UNKNOWN: "Unknown",
        }
        return labels.get(self.app_type, str(self.app_type))

"""Kit manifest.

A kit is a distribution that plugs domain code into a julee solution: one
or more bounded contexts, their infrastructure, and whatever they
contribute to a solution's apps. The manifest is what the framework knows
about a kit without importing any of it.

A kit registers its manifest through an entry point::

    [project.entry-points."julee.kits"]
    ceap = "julee_ceap:kit"

and a solution adopts it by slug::

    [tool.julee]
    kits = ["ceap"]

Installing a kit does not activate it. Adoption is explicit, so a kit that
arrives as a transitive dependency cannot change a solution's behaviour.

See docs/ADRs/012-framework-and-kits.md.
"""

from collections.abc import Mapping

from pydantic import Field, field_validator

from julee.core.entities.entity import Entity


class Kit(Entity):
    """What a kit tells the framework about itself.

    The manifest carries no imported objects. Contributions are dotted
    paths, resolved by whichever integration consumes them, so reading a
    manifest never imports FastAPI, Temporal or Sphinx.
    """

    slug: str = Field(
        description='Unique identifier, matching the entry point name (e.g. "ceap")'
    )
    name: str = Field(description="Human-readable name")
    package: str = Field(
        description="Import root of the kit, introspected to find its "
        'bounded contexts (e.g. "julee_ceap")'
    )
    requires: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Slugs of other kits this kit builds on",
    )
    contributes: Mapping[str, str] = Field(
        default_factory=dict,
        description="Contribution point to dotted path, for example "
        '{"fastapi.routers": "julee_ceap.apps.api:router"}',
    )
    viewpoint: bool = Field(
        default=False,
        description="True if this kit's bounded contexts describe a solution "
        "rather than implement a domain",
    )
    policies: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Slugs of policies this kit contributes, which a solution "
        "may adopt",
    )

    @field_validator("slug", "name", "package", mode="before")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Reject empty identifiers."""
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

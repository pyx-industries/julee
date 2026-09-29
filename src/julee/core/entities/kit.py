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
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Kit:
    """What a kit tells the framework about itself.

    The manifest carries no imported objects. Contributions are dotted
    paths, resolved by whichever integration consumes them, so reading a
    manifest never imports FastAPI, Temporal or Sphinx.
    """

    slug: str
    """Unique identifier, matching the entry point name (e.g. "ceap")."""
    name: str
    """Human-readable name."""
    package: str
    """Import root of the kit, introspected to find its bounded contexts (e.g. "julee_ceap")."""
    requires: tuple[str, ...] = ()
    """Slugs of other kits this kit builds on."""
    contributes: Mapping[str, str | tuple[str, ...]] = field(default_factory=dict)
    """What this kit offers, by contribution point.

    Each point maps to one dotted path or several::

        {"fastapi.routers": "julee_ceap.apps.api:router"}
        {"sphinx.extension": ("a.b", "a.c")}
    """

    def contributed(self, point: str) -> tuple[str, ...]:
        """What this kit offers at one contribution point.

        A kit may offer one thing or several, and a caller asking should
        not have to care which: a point with a single path reads the same
        as a point with three.

        Args:
            point: The contribution point, e.g. "sphinx.extension"

        Returns:
            The dotted paths, in the order the manifest gives them
        """
        offered = self.contributes.get(point)
        if offered is None:
            return ()
        if isinstance(offered, str):
            return (offered,)
        return tuple(offered)

    viewpoint: bool = False
    """True if this kit's bounded contexts describe a solution rather than implement a domain."""
    policies: tuple[str, ...] = ()
    """Slugs of policies this kit contributes, which a solution may adopt."""

    def __post_init__(self) -> None:
        """Check the identifiers are named, and trim them.

        This was a field_validator over three fields, which refused a
        blank one and returned a stripped one.

        Raises:
            ValueError: If the slug, name or package is blank
        """
        for field_name in ("slug", "name", "package"):
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ValueError("must not be empty")
            object.__setattr__(self, field_name, value.strip())

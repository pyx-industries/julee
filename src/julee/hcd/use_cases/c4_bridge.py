"""Use case for generating C4 container diagram data from HCD entities.

Bridges human-centered design entities to C4 architectural model data
that can be rendered into diagrams.
"""

from dataclasses import dataclass, field

from julee.hcd.entities.app import App
from julee.supply_chain.entities.accelerator import Accelerator
from julee.hcd.entities.contrib import ContribModule
from julee.hcd.entities.persona import Persona


@dataclass
class C4Container:
    """Represents a C4 container in the diagram."""

    id: str
    name: str
    technology: str
    description: str
    container_type: str  # "app", "accelerator", "contrib", "foundation"


@dataclass
class C4Person:
    """Represents a C4 person (persona) in the diagram."""

    id: str
    name: str
    description: str


@dataclass
class C4Relationship:
    """Represents a relationship between C4 elements."""

    source_id: str
    target_id: str
    label: str


@dataclass
class C4ContainerDiagramData:
    """Complete data for a C4 container diagram."""

    title: str
    system_name: str
    persons: list[C4Person] = field(default_factory=list)
    containers: list[C4Container] = field(default_factory=list)
    relationships: list[C4Relationship] = field(default_factory=list)
    external_systems: list[tuple[str, str, str]] = field(default_factory=list)


def _safe_id(name: str) -> str:
    """Convert name to a safe identifier."""
    return name.replace("-", "_").replace(" ", "_").replace(".", "_")


def _escape_description(text: str) -> str:
    """Extract first sentence and escape for diagram use."""
    text = " ".join(text.split())
    for end in [". ", ".\n", ".\t"]:
        if end[0] in text:
            idx = text.find(end[0])
            if idx > 0:
                text = text[:idx]
                break
    return text.replace('"', '\\"')


def generate_c4_container_diagram(
    apps: list[App],
    accelerators: list[Accelerator],
    contribs: list[ContribModule],
    personas: list[Persona],
    title: str = "Container Diagram",
    system_name: str = "System",
    show_foundation: bool = False,
    foundation_name: str = "Foundation",
    show_external: bool = False,
    external_name: str = "External Systems",
) -> C4ContainerDiagramData:
    """Generate C4 container diagram data from HCD entities.

    Args:
        apps: Application entities
        accelerators: Accelerator (bounded context) entities
        contribs: Contrib module entities
        personas: Persona entities
        title: Diagram title
        system_name: Name of the system boundary
        show_foundation: Include foundation layer container
        foundation_name: Name for the foundation container
        show_external: Include external systems container
        external_name: Name for external systems

    Returns:
        C4ContainerDiagramData with all diagram elements
    """
    diagram = C4ContainerDiagramData(title=title, system_name=system_name)

    # Build lookup maps for relationship resolution
    app_by_slug = {app.slug: app for app in apps}
    accel_by_slug = {accel.slug: accel for accel in accelerators}
    contrib_by_slug = {contrib.slug: contrib for contrib in contribs}

    # Add personas that have relationships
    for persona in sorted(personas, key=lambda p: p.slug):
        if persona.app_slugs or persona.accelerator_slugs or persona.contrib_slugs:
            desc = (
                _escape_description(persona.context)
                if persona.context
                else persona.name
            )
            diagram.persons.append(
                C4Person(
                    id=_safe_id(persona.slug),
                    name=persona.name,
                    description=desc,
                )
            )

    # Add app containers
    for app in sorted(apps, key=lambda a: a.slug):
        desc = app.description or app.interface_label
        diagram.containers.append(
            C4Container(
                id=_safe_id(app.slug),
                name=app.name,
                technology=app.c4_technology,
                description=_escape_description(desc),
                container_type="app",
            )
        )

    # Add accelerator containers
    for accel in sorted(accelerators, key=lambda a: a.slug):
        diagram.containers.append(
            C4Container(
                id=_safe_id(accel.slug),
                name=accel.display_title,
                technology=accel.technology,
                description=_escape_description(accel.c4_description),
                container_type="accelerator",
            )
        )

    # Add contrib containers
    for contrib in sorted(contribs, key=lambda c: c.slug):
        diagram.containers.append(
            C4Container(
                id=_safe_id(contrib.slug),
                name=contrib.display_title,
                technology=contrib.technology,
                description=_escape_description(contrib.c4_description),
                container_type="contrib",
            )
        )

    # Add foundation container if requested
    if show_foundation:
        diagram.containers.append(
            C4Container(
                id="foundation",
                name=foundation_name,
                technology="Python",
                description="Clean architecture idioms and utilities",
                container_type="foundation",
            )
        )

    # Add external systems if requested
    if show_external:
        diagram.external_systems.append(
            ("external", external_name, "External dependencies")
        )

    # Build relationships: Personas to apps
    for persona in personas:
        persona_id = _safe_id(persona.slug)
        for app_slug in persona.app_slugs:
            if app_slug in app_by_slug:
                app = app_by_slug[app_slug]
                diagram.relationships.append(
                    C4Relationship(
                        source_id=persona_id,
                        target_id=_safe_id(app_slug),
                        label=app.interface.user_relationship,
                    )
                )

    # Personas to accelerators
    for persona in personas:
        persona_id = _safe_id(persona.slug)
        for accel_slug in persona.accelerator_slugs:
            if accel_slug in accel_by_slug:
                diagram.relationships.append(
                    C4Relationship(
                        source_id=persona_id,
                        target_id=_safe_id(accel_slug),
                        label="Uses",
                    )
                )

    # Personas to contribs
    for persona in personas:
        persona_id = _safe_id(persona.slug)
        for contrib_slug in persona.contrib_slugs:
            if contrib_slug in contrib_by_slug:
                diagram.relationships.append(
                    C4Relationship(
                        source_id=persona_id,
                        target_id=_safe_id(contrib_slug),
                        label="Uses",
                    )
                )

    # Apps to accelerators
    for app in apps:
        app_id = _safe_id(app.slug)
        for accel_slug in app.accelerators:
            diagram.relationships.append(
                C4Relationship(
                    source_id=app_id,
                    target_id=_safe_id(accel_slug),
                    label=app.interface.accelerator_relationship,
                )
            )

    # Accelerators/Contribs to foundation
    if show_foundation:
        for accel in accelerators:
            diagram.relationships.append(
                C4Relationship(
                    source_id=_safe_id(accel.slug),
                    target_id="foundation",
                    label="Built on",
                )
            )
        for contrib in contribs:
            diagram.relationships.append(
                C4Relationship(
                    source_id=_safe_id(contrib.slug),
                    target_id="foundation",
                    label="Built on",
                )
            )

    # Foundation to external
    if show_external and show_foundation:
        diagram.relationships.append(
            C4Relationship(
                source_id="foundation",
                target_id="external",
                label="Connects to",
            )
        )

    return diagram

"""C4 Diagram domain models.

These models represent the computed data for various C4 diagram types.
They are domain objects that can be serialized to different output formats
(PlantUML, Structurizr DSL, etc.) by serializers.
"""

from pydantic import BaseModel, Field

from .component import Component
from .container import Container
from .deployment_node import DeploymentNode
from .dynamic_step import DynamicStep
from .relationship import Relationship
from .software_system import SoftwareSystem


class PersonInfo(BaseModel):
    """Minimal person info for diagrams.

    Represents a user/actor in C4 diagrams. This is a lightweight
    representation used when full Person entities aren't needed.
    """

    slug: str
    name: str
    description: str = ""


class SystemLandscapeDiagram(BaseModel):
    """Domain model for a C4 System Landscape diagram.

    Shows all software systems and their relationships at the highest level.
    """

    systems: list[SoftwareSystem] = Field(default_factory=list)
    person_slugs: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class SystemContextDiagram(BaseModel):
    """Domain model for a C4 System Context diagram.

    Shows a single system in context with its users and external systems.
    """

    system: SoftwareSystem
    external_systems: list[SoftwareSystem] = Field(default_factory=list)
    person_slugs: list[str] = Field(default_factory=list)
    persons: list[PersonInfo] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class ContainerDiagram(BaseModel):
    """Domain model for a C4 Container diagram.

    Shows the containers within a software system.
    """

    system: SoftwareSystem
    containers: list[Container] = Field(default_factory=list)
    external_systems: list[SoftwareSystem] = Field(default_factory=list)
    person_slugs: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class ComponentDiagram(BaseModel):
    """Domain model for a C4 Component diagram.

    Shows the components within a container.
    """

    system: SoftwareSystem
    container: Container
    components: list[Component] = Field(default_factory=list)
    external_containers: list[Container] = Field(default_factory=list)
    external_systems: list[SoftwareSystem] = Field(default_factory=list)
    person_slugs: list[str] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class DeploymentDiagram(BaseModel):
    """Domain model for a C4 Deployment diagram.

    Shows the deployment infrastructure for an environment.
    """

    environment: str
    nodes: list[DeploymentNode] = Field(default_factory=list)
    containers: list[Container] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class DynamicDiagram(BaseModel):
    """Domain model for a C4 Dynamic diagram.

    Shows a sequence of interactions for a specific scenario.
    """

    sequence_name: str
    steps: list[DynamicStep] = Field(default_factory=list)
    systems: list[SoftwareSystem] = Field(default_factory=list)
    containers: list[Container] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)
    person_slugs: list[str] = Field(default_factory=list)

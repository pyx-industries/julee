"""GetComponentDiagramUseCase.

Use case for computing a component diagram.

A Component diagram shows the components that make up a container,
plus the relationships between them.
"""

from dataclasses import dataclass, field

from ...models.component import Component
from ...models.container import Container
from ...models.relationship import ElementType, Relationship
from ...models.software_system import SoftwareSystem
from ...repositories.component import ComponentRepository
from ...repositories.container import ContainerRepository
from ...repositories.relationship import RelationshipRepository
from ...repositories.software_system import SoftwareSystemRepository


@dataclass
class ComponentDiagramData:
    """Data for rendering a component diagram."""

    system: SoftwareSystem
    container: Container
    components: list[Component] = field(default_factory=list)
    external_containers: list[Container] = field(default_factory=list)
    external_systems: list[SoftwareSystem] = field(default_factory=list)
    person_slugs: list[str] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


class GetComponentDiagramUseCase:
    """Use case for computing a component diagram.

    The diagram shows:
    - The container boundary
    - Components within the container
    - Other containers that components interact with
    - External systems that components interact with
    - Persons that interact with components
    - Relationships between all these elements
    """

    def __init__(
        self,
        software_system_repo: SoftwareSystemRepository,
        container_repo: ContainerRepository,
        component_repo: ComponentRepository,
        relationship_repo: RelationshipRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            software_system_repo: SoftwareSystem repository instance
            container_repo: Container repository instance
            component_repo: Component repository instance
            relationship_repo: Relationship repository instance
        """
        self.software_system_repo = software_system_repo
        self.container_repo = container_repo
        self.component_repo = component_repo
        self.relationship_repo = relationship_repo

    async def execute(self, container_slug: str) -> ComponentDiagramData | None:
        """Compute the component diagram data.

        Args:
            container_slug: Slug of the container to show components for

        Returns:
            Diagram data containing the container, components, external elements,
            and relationships, or None if the container doesn't exist
        """
        container = await self.container_repo.get(container_slug)
        if not container:
            return None

        system = await self.software_system_repo.get(container.system_slug)
        if not system:
            return None

        components = await self.component_repo.get_by_container(container_slug)

        all_relationships: list[Relationship] = []
        external_container_slugs: set[str] = set()
        external_system_slugs: set[str] = set()
        person_slugs: set[str] = set()

        for component in components:
            rels = await self.relationship_repo.get_for_element(
                ElementType.COMPONENT, component.slug
            )
            for rel in rels:
                if rel not in all_relationships:
                    all_relationships.append(rel)

                if rel.source_type == ElementType.CONTAINER:
                    if rel.source_slug != container_slug:
                        external_container_slugs.add(rel.source_slug)
                elif rel.source_type == ElementType.SOFTWARE_SYSTEM:
                    external_system_slugs.add(rel.source_slug)
                elif rel.source_type == ElementType.PERSON:
                    person_slugs.add(rel.source_slug)

                if rel.destination_type == ElementType.CONTAINER:
                    if rel.destination_slug != container_slug:
                        external_container_slugs.add(rel.destination_slug)
                elif rel.destination_type == ElementType.SOFTWARE_SYSTEM:
                    external_system_slugs.add(rel.destination_slug)
                elif rel.destination_type == ElementType.PERSON:
                    person_slugs.add(rel.destination_slug)

        external_containers: list[Container] = []
        for slug in external_container_slugs:
            ext_container = await self.container_repo.get(slug)
            if ext_container:
                external_containers.append(ext_container)

        external_systems: list[SoftwareSystem] = []
        for slug in external_system_slugs:
            ext_system = await self.software_system_repo.get(slug)
            if ext_system:
                external_systems.append(ext_system)

        return ComponentDiagramData(
            system=system,
            container=container,
            components=components,
            external_containers=external_containers,
            external_systems=external_systems,
            person_slugs=list(person_slugs),
            relationships=all_relationships,
        )

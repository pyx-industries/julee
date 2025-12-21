"""GetContainerDiagramUseCase.

Use case for computing a container diagram.

A Container diagram shows the containers (applications, data stores, etc.)
that make up a software system, plus the relationships between them.
"""

from dataclasses import dataclass, field

from ...models.container import Container
from ...models.relationship import ElementType, Relationship
from ...models.software_system import SoftwareSystem
from ...repositories.container import ContainerRepository
from ...repositories.relationship import RelationshipRepository
from ...repositories.software_system import SoftwareSystemRepository


@dataclass
class ContainerDiagramData:
    """Data for rendering a container diagram."""

    system: SoftwareSystem
    containers: list[Container] = field(default_factory=list)
    external_systems: list[SoftwareSystem] = field(default_factory=list)
    person_slugs: list[str] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


class GetContainerDiagramUseCase:
    """Use case for computing a container diagram.

    The diagram shows:
    - The system boundary
    - Containers within the system
    - External systems that interact with containers
    - Persons (users) that interact with containers
    - Relationships between all these elements
    """

    def __init__(
        self,
        software_system_repo: SoftwareSystemRepository,
        container_repo: ContainerRepository,
        relationship_repo: RelationshipRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            software_system_repo: SoftwareSystem repository instance
            container_repo: Container repository instance
            relationship_repo: Relationship repository instance
        """
        self.software_system_repo = software_system_repo
        self.container_repo = container_repo
        self.relationship_repo = relationship_repo

    async def execute(self, system_slug: str) -> ContainerDiagramData | None:
        """Compute the container diagram data.

        Args:
            system_slug: Slug of the software system to show containers for

        Returns:
            Diagram data containing the system, containers, external elements,
            and relationships, or None if the system doesn't exist
        """
        system = await self.software_system_repo.get(system_slug)
        if not system:
            return None

        containers = await self.container_repo.get_by_system(system_slug)

        all_relationships: list[Relationship] = []
        external_system_slugs: set[str] = set()
        person_slugs: set[str] = set()

        for container in containers:
            rels = await self.relationship_repo.get_for_element(
                ElementType.CONTAINER, container.slug
            )
            for rel in rels:
                if rel not in all_relationships:
                    all_relationships.append(rel)

                if rel.source_type == ElementType.SOFTWARE_SYSTEM:
                    if rel.source_slug != system_slug:
                        external_system_slugs.add(rel.source_slug)
                elif rel.source_type == ElementType.PERSON:
                    person_slugs.add(rel.source_slug)

                if rel.destination_type == ElementType.SOFTWARE_SYSTEM:
                    if rel.destination_slug != system_slug:
                        external_system_slugs.add(rel.destination_slug)
                elif rel.destination_type == ElementType.PERSON:
                    person_slugs.add(rel.destination_slug)

        external_systems: list[SoftwareSystem] = []
        for slug in external_system_slugs:
            ext_system = await self.software_system_repo.get(slug)
            if ext_system:
                external_systems.append(ext_system)

        return ContainerDiagramData(
            system=system,
            containers=containers,
            external_systems=external_systems,
            person_slugs=list(person_slugs),
            relationships=all_relationships,
        )

"""GetSystemContextDiagramUseCase.

Use case for computing a system context diagram.

A System Context diagram shows the software system in scope and its
relationships with users (persons) and other software systems.
"""

from dataclasses import dataclass, field

from ...models.relationship import ElementType, Relationship
from ...models.software_system import SoftwareSystem
from ...repositories.relationship import RelationshipRepository
from ...repositories.software_system import SoftwareSystemRepository


@dataclass
class PersonInfo:
    """Minimal person info for diagrams."""

    slug: str
    name: str
    description: str = ""


@dataclass
class SystemContextDiagramData:
    """Data for rendering a system context diagram."""

    system: SoftwareSystem
    external_systems: list[SoftwareSystem] = field(default_factory=list)
    person_slugs: list[str] = field(default_factory=list)
    persons: list[PersonInfo] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


class GetSystemContextDiagramUseCase:
    """Use case for computing a system context diagram.

    The diagram shows:
    - The system in scope (center)
    - External systems that interact with it
    - Persons (users) that interact with it
    - Relationships between all these elements
    """

    def __init__(
        self,
        software_system_repo: SoftwareSystemRepository,
        relationship_repo: RelationshipRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            software_system_repo: SoftwareSystem repository instance
            relationship_repo: Relationship repository instance
        """
        self.software_system_repo = software_system_repo
        self.relationship_repo = relationship_repo

    async def execute(self, system_slug: str) -> SystemContextDiagramData | None:
        """Compute the system context diagram data.

        Args:
            system_slug: Slug of the software system to show context for

        Returns:
            Diagram data containing the system, related systems, persons,
            and relationships, or None if the system doesn't exist
        """
        system = await self.software_system_repo.get(system_slug)
        if not system:
            return None

        relationships = await self.relationship_repo.get_for_element(
            ElementType.SOFTWARE_SYSTEM, system_slug
        )

        external_system_slugs: set[str] = set()
        person_slugs: set[str] = set()

        for rel in relationships:
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

        return SystemContextDiagramData(
            system=system,
            external_systems=external_systems,
            person_slugs=list(person_slugs),
            relationships=relationships,
        )

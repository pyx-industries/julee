"""GetSystemLandscapeDiagramUseCase.

Use case for computing a system landscape diagram.

A System Landscape diagram shows all software systems and persons
within an enterprise or organization, plus their relationships.
"""

from dataclasses import dataclass, field

from ...models.relationship import ElementType, Relationship
from ...models.software_system import SoftwareSystem
from ...repositories.relationship import RelationshipRepository
from ...repositories.software_system import SoftwareSystemRepository


@dataclass
class SystemLandscapeDiagramData:
    """Data for rendering a system landscape diagram."""

    systems: list[SoftwareSystem] = field(default_factory=list)
    person_slugs: list[str] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


class GetSystemLandscapeDiagramUseCase:
    """Use case for computing a system landscape diagram.

    The diagram shows:
    - All software systems in the model
    - All persons (users) referenced in relationships
    - Relationships between systems and persons
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

    async def execute(self) -> SystemLandscapeDiagramData:
        """Compute the system landscape diagram data.

        Returns:
            Diagram data containing all systems, persons, and their relationships
        """
        systems = await self.software_system_repo.list_all()

        person_relationships = await self.relationship_repo.get_person_relationships()
        cross_system_relationships = await self.relationship_repo.get_cross_system_relationships()

        all_relationships: list[Relationship] = []
        person_slugs: set[str] = set()

        for rel in person_relationships:
            if rel not in all_relationships:
                all_relationships.append(rel)

            if rel.source_type == ElementType.PERSON:
                person_slugs.add(rel.source_slug)
            if rel.destination_type == ElementType.PERSON:
                person_slugs.add(rel.destination_slug)

        for rel in cross_system_relationships:
            if rel not in all_relationships:
                all_relationships.append(rel)

        return SystemLandscapeDiagramData(
            systems=systems,
            person_slugs=list(person_slugs),
            relationships=all_relationships,
        )

"""GetContainerDiagramUseCase with co-located request/response.

Use case for computing a container diagram.

A Container diagram shows the containers (applications, data stores, etc.)
that make up a software system, plus the relationships between them.
"""

from pydantic import BaseModel, Field

from julee.c4.entities.diagrams import ContainerDiagram
from julee.c4.entities.relationship import ElementType, Relationship
from julee.c4.entities.software_system import SoftwareSystem
from julee.c4.repositories.container import ContainerRepository
from julee.c4.repositories.relationship import RelationshipRepository
from julee.c4.repositories.software_system import SoftwareSystemRepository


class GetContainerDiagramRequest(BaseModel):
    """Request for generating a container diagram."""

    system_slug: str = Field(description="Software system to show containers for")
    format: str = Field(
        default="plantuml", description="Output format: plantuml, structurizr, data"
    )


class GetContainerDiagramResponse(BaseModel):
    """Response from computing a container diagram."""

    diagram: ContainerDiagram | None


class GetContainerDiagramUseCase:
    """Use case for computing a container diagram.

    .. usecase-documentation:: julee.c4.domain.use_cases.diagrams.container_diagram:GetContainerDiagramUseCase

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

    async def execute(
        self, request: GetContainerDiagramRequest
    ) -> GetContainerDiagramResponse:
        """Compute the container diagram data.

        Args:
            request: Request containing system_slug

        Returns:
            Response containing diagram data, or diagram=None if system doesn't exist
        """
        system = await self.software_system_repo.get(request.system_slug)
        if not system:
            return GetContainerDiagramResponse(diagram=None)

        containers = await self.container_repo.get_by_system(request.system_slug)

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
                    if rel.source_slug != request.system_slug:
                        external_system_slugs.add(rel.source_slug)
                elif rel.source_type == ElementType.PERSON:
                    person_slugs.add(rel.source_slug)

                if rel.destination_type == ElementType.SOFTWARE_SYSTEM:
                    if rel.destination_slug != request.system_slug:
                        external_system_slugs.add(rel.destination_slug)
                elif rel.destination_type == ElementType.PERSON:
                    person_slugs.add(rel.destination_slug)

        external_systems: list[SoftwareSystem] = []
        for slug in external_system_slugs:
            ext_system = await self.software_system_repo.get(slug)
            if ext_system:
                external_systems.append(ext_system)

        diagram = ContainerDiagram(
            system=system,
            containers=containers,
            external_systems=external_systems,
            person_slugs=list(person_slugs),
            relationships=all_relationships,
        )
        return GetContainerDiagramResponse(diagram=diagram)

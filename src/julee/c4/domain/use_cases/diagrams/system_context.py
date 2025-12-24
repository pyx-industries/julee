"""GetSystemContextDiagramUseCase with co-located request/response.

Use case for computing a system context diagram.

A System Context diagram shows the software system in scope and its
relationships with users (persons) and other software systems.
"""

from pydantic import BaseModel, Field

from ...models.diagrams import SystemContextDiagram
from ...models.relationship import ElementType
from ...models.software_system import SoftwareSystem
from ...repositories.relationship import RelationshipRepository
from ...repositories.software_system import SoftwareSystemRepository


class GetSystemContextDiagramRequest(BaseModel):
    """Request for generating a system context diagram."""

    system_slug: str = Field(description="Software system to show context for")
    format: str = Field(
        default="plantuml", description="Output format: plantuml, structurizr, data"
    )


class GetSystemContextDiagramResponse(BaseModel):
    """Response from computing a system context diagram."""

    diagram: SystemContextDiagram | None


class GetSystemContextDiagramUseCase:
    """Use case for computing a system context diagram.

    .. usecase-documentation:: julee.c4.domain.use_cases.diagrams.system_context:GetSystemContextDiagramUseCase

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

    async def execute(
        self, request: GetSystemContextDiagramRequest
    ) -> GetSystemContextDiagramResponse:
        """Compute the system context diagram data.

        Args:
            request: Request containing system_slug

        Returns:
            Response containing diagram data, or diagram=None if system doesn't exist
        """
        system = await self.software_system_repo.get(request.system_slug)
        if not system:
            return GetSystemContextDiagramResponse(diagram=None)

        relationships = await self.relationship_repo.get_for_element(
            ElementType.SOFTWARE_SYSTEM, request.system_slug
        )

        external_system_slugs: set[str] = set()
        person_slugs: set[str] = set()

        for rel in relationships:
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

        diagram = SystemContextDiagram(
            system=system,
            external_systems=external_systems,
            person_slugs=list(person_slugs),
            relationships=relationships,
        )
        return GetSystemContextDiagramResponse(diagram=diagram)

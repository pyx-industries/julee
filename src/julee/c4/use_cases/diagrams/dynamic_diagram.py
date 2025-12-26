"""GetDynamicDiagramUseCase with co-located request/response.

Use case for computing a dynamic diagram.

A Dynamic diagram shows how elements collaborate at runtime to
accomplish a specific use case or scenario.
"""

from pydantic import BaseModel, Field

from julee.c4.entities.component import Component
from julee.c4.entities.container import Container
from julee.c4.entities.diagrams import DynamicDiagram
from julee.c4.entities.relationship import ElementType
from julee.c4.entities.software_system import SoftwareSystem
from julee.c4.repositories.component import ComponentRepository
from julee.c4.repositories.container import ContainerRepository
from julee.c4.repositories.dynamic_step import DynamicStepRepository
from julee.c4.repositories.software_system import SoftwareSystemRepository
from julee.core.decorators import use_case


class GetDynamicDiagramRequest(BaseModel):
    """Request for generating a dynamic diagram."""

    sequence_name: str = Field(description="Dynamic sequence to show")
    format: str = Field(
        default="plantuml", description="Output format: plantuml, structurizr, data"
    )


class GetDynamicDiagramResponse(BaseModel):
    """Response from computing a dynamic diagram."""

    diagram: DynamicDiagram | None


@use_case
class GetDynamicDiagramUseCase:
    """Use case for computing a dynamic diagram.

    .. usecase-documentation:: julee.c4.domain.use_cases.diagrams.dynamic_diagram:GetDynamicDiagramUseCase

    The diagram shows:
    - A numbered sequence of interactions
    - Elements involved in the sequence (systems, containers, components, persons)
    - The flow of messages/calls between elements
    """

    def __init__(
        self,
        dynamic_step_repo: DynamicStepRepository,
        software_system_repo: SoftwareSystemRepository,
        container_repo: ContainerRepository,
        component_repo: ComponentRepository,
    ) -> None:
        """Initialize with repository dependencies.

        Args:
            dynamic_step_repo: DynamicStep repository instance
            software_system_repo: SoftwareSystem repository instance
            container_repo: Container repository instance
            component_repo: Component repository instance
        """
        self.dynamic_step_repo = dynamic_step_repo
        self.software_system_repo = software_system_repo
        self.container_repo = container_repo
        self.component_repo = component_repo

    async def execute(
        self, request: GetDynamicDiagramRequest
    ) -> GetDynamicDiagramResponse:
        """Compute the dynamic diagram data.

        Args:
            request: Request containing sequence_name

        Returns:
            Response containing diagram with steps and participating elements,
            or diagram=None if no steps exist for the sequence
        """
        steps = await self.dynamic_step_repo.get_by_sequence(request.sequence_name)
        if not steps:
            return GetDynamicDiagramResponse(diagram=None)

        system_slugs: set[str] = set()
        container_slugs: set[str] = set()
        component_slugs: set[str] = set()
        person_slugs: set[str] = set()

        for step in steps:
            for el_type, el_slug in [
                (step.source_type, step.source_slug),
                (step.destination_type, step.destination_slug),
            ]:
                if el_type == ElementType.SOFTWARE_SYSTEM:
                    system_slugs.add(el_slug)
                elif el_type == ElementType.CONTAINER:
                    container_slugs.add(el_slug)
                elif el_type == ElementType.COMPONENT:
                    component_slugs.add(el_slug)
                elif el_type == ElementType.PERSON:
                    person_slugs.add(el_slug)

        systems: list[SoftwareSystem] = []
        for slug in system_slugs:
            system = await self.software_system_repo.get(slug)
            if system:
                systems.append(system)

        containers: list[Container] = []
        for slug in container_slugs:
            container = await self.container_repo.get(slug)
            if container:
                containers.append(container)

        components: list[Component] = []
        for slug in component_slugs:
            component = await self.component_repo.get(slug)
            if component:
                components.append(component)

        diagram = DynamicDiagram(
            sequence_name=request.sequence_name,
            steps=steps,
            systems=systems,
            containers=containers,
            components=components,
            person_slugs=list(person_slugs),
        )
        return GetDynamicDiagramResponse(diagram=diagram)

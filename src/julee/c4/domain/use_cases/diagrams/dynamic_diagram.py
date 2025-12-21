"""GetDynamicDiagramUseCase.

Use case for computing a dynamic diagram.

A Dynamic diagram shows how elements collaborate at runtime to
accomplish a specific use case or scenario.
"""

from dataclasses import dataclass, field

from ...models.component import Component
from ...models.container import Container
from ...models.dynamic_step import DynamicStep
from ...models.relationship import ElementType
from ...models.software_system import SoftwareSystem
from ...repositories.component import ComponentRepository
from ...repositories.container import ContainerRepository
from ...repositories.dynamic_step import DynamicStepRepository
from ...repositories.software_system import SoftwareSystemRepository


@dataclass
class DynamicDiagramData:
    """Data for rendering a dynamic diagram."""

    sequence_name: str
    steps: list[DynamicStep] = field(default_factory=list)
    systems: list[SoftwareSystem] = field(default_factory=list)
    containers: list[Container] = field(default_factory=list)
    components: list[Component] = field(default_factory=list)
    person_slugs: list[str] = field(default_factory=list)


class GetDynamicDiagramUseCase:
    """Use case for computing a dynamic diagram.

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

    async def execute(self, sequence_name: str) -> DynamicDiagramData | None:
        """Compute the dynamic diagram data.

        Args:
            sequence_name: Name of the dynamic sequence to show

        Returns:
            Diagram data containing steps and participating elements,
            or None if no steps exist for the sequence
        """
        steps = await self.dynamic_step_repo.get_by_sequence(sequence_name)
        if not steps:
            return None

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

        return DynamicDiagramData(
            sequence_name=sequence_name,
            steps=steps,
            systems=systems,
            containers=containers,
            components=components,
            person_slugs=list(person_slugs),
        )

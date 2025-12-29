"""C4 semantic relation decorators.

Convenience decorators for declaring semantic relationships between
solution/viewpoint entities and C4 architecture entities.

These are shorthand for the generic julee.core.decorators.semantic_relation
decorator, pre-configured with C4 entity types.

Example usage:

    from julee.c4.decorators import projects_container

    @projects_container()
    class ApiGateway(BaseModel):
        '''API Gateway - projects a Container in C4 terms.'''
        slug: str
        technology: str

This is equivalent to:

    from julee.core.decorators import semantic_relation
    from julee.core.entities.semantic_relation import RelationType
    from julee.c4.entities.container import Container

    @semantic_relation(Container, RelationType.PROJECTS)
    class ApiGateway(BaseModel):
        ...
"""

from typing import Callable

from julee.core.decorators import semantic_relation
from julee.core.entities.semantic_relation import RelationType

# Import C4 entities for convenience decorators
from julee.c4.entities.component import Component
from julee.c4.entities.container import Container
from julee.c4.entities.deployment_node import DeploymentNode
from julee.c4.entities.software_system import SoftwareSystem


def projects_software_system() -> Callable[[type], type]:
    """Declare that the decorated class projects a SoftwareSystem.

    Use when a solution entity provides a view onto a software system
    in C4 terms.
    """
    return semantic_relation(SoftwareSystem, RelationType.PROJECTS)


def projects_container() -> Callable[[type], type]:
    """Declare that the decorated class projects a Container.

    Use when a solution entity provides a view onto a container
    (application, service, database) in C4 terms.
    """
    return semantic_relation(Container, RelationType.PROJECTS)


def projects_component() -> Callable[[type], type]:
    """Declare that the decorated class projects a Component.

    Use when a solution entity provides a view onto a component
    (module, class, use case) in C4 terms.
    """
    return semantic_relation(Component, RelationType.PROJECTS)


def projects_deployment_node() -> Callable[[type], type]:
    """Declare that the decorated class projects a DeploymentNode.

    Use when a solution entity provides a view onto deployment
    infrastructure in C4 terms.
    """
    return semantic_relation(DeploymentNode, RelationType.PROJECTS)


def is_a_container() -> Callable[[type], type]:
    """Declare that the decorated class is_a Container.

    Use when a solution entity IS a container in C4 terms.
    """
    return semantic_relation(Container, RelationType.IS_A)


def is_a_component() -> Callable[[type], type]:
    """Declare that the decorated class is_a Component.

    Use when a solution entity IS a component in C4 terms.
    """
    return semantic_relation(Component, RelationType.IS_A)


def is_a_deployment_node() -> Callable[[type], type]:
    """Declare that the decorated class is_a DeploymentNode.

    Use when a solution entity IS a deployment node in C4 terms.
    """
    return semantic_relation(DeploymentNode, RelationType.IS_A)

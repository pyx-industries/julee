"""HCD semantic relation decorators.

Convenience decorators for declaring semantic relationships between
solution entities and HCD viewpoint entities.

These are shorthand for the generic julee.core.decorators.semantic_relation
decorator, pre-configured with HCD entity types.

Example usage:

    from julee.hcd.decorators import is_a_persona

    @is_a_persona()
    class CustomerSegment(BaseModel):
        '''A customer segment - is_a Persona in HCD terms.'''
        slug: str
        name: str

This is equivalent to:

    from julee.core.decorators import semantic_relation
    from julee.core.entities.semantic_relation import RelationType
    from julee.hcd.entities.persona import Persona

    @semantic_relation(Persona, RelationType.IS_A)
    class CustomerSegment(BaseModel):
        ...
"""

from functools import partial
from typing import Callable

from julee.core.decorators import semantic_relation
from julee.core.entities.semantic_relation import RelationType

# Import Core entities for projection decorators
from julee.core.entities.application import Application
from julee.core.entities.bounded_context import BoundedContext

# Import HCD entities for convenience decorators
from julee.hcd.entities.accelerator import Accelerator
from julee.hcd.entities.app import App
from julee.hcd.entities.epic import Epic
from julee.hcd.entities.integration import Integration
from julee.hcd.entities.journey import Journey
from julee.hcd.entities.persona import Persona
from julee.hcd.entities.story import Story


def is_a_persona() -> Callable[[type], type]:
    """Declare that the decorated class is_a Persona.

    Use when a solution entity represents a persona/user type
    in HCD terms.
    """
    return semantic_relation(Persona, RelationType.IS_A)


def is_a_accelerator() -> Callable[[type], type]:
    """Declare that the decorated class is_a Accelerator.

    Use when a solution entity represents a business capability
    accelerator in HCD terms.
    """
    return semantic_relation(Accelerator, RelationType.IS_A)


def is_a_story() -> Callable[[type], type]:
    """Declare that the decorated class is_a Story.

    Use when a solution entity represents a user story
    in HCD terms.
    """
    return semantic_relation(Story, RelationType.IS_A)


def is_a_epic() -> Callable[[type], type]:
    """Declare that the decorated class is_a Epic.

    Use when a solution entity represents an epic
    in HCD terms.
    """
    return semantic_relation(Epic, RelationType.IS_A)


def is_a_journey() -> Callable[[type], type]:
    """Declare that the decorated class is_a Journey.

    Use when a solution entity represents a user journey
    in HCD terms.
    """
    return semantic_relation(Journey, RelationType.IS_A)


def is_a_app() -> Callable[[type], type]:
    """Declare that the decorated class is_a App.

    Use when a solution entity represents an application
    in HCD terms.
    """
    return semantic_relation(App, RelationType.IS_A)


def is_a_integration() -> Callable[[type], type]:
    """Declare that the decorated class is_a Integration.

    Use when a solution entity represents an integration
    in HCD terms.
    """
    return semantic_relation(Integration, RelationType.IS_A)


def enables_story() -> Callable[[type], type]:
    """Declare that the decorated class enables Story functionality.

    Use when a solution entity (e.g., UseCase) enables user stories.
    """
    return semantic_relation(Story, RelationType.ENABLES)


def enables_journey() -> Callable[[type], type]:
    """Declare that the decorated class enables Journey functionality.

    Use when a solution entity enables user journeys.
    """
    return semantic_relation(Journey, RelationType.ENABLES)


# Projection decorators - for HCD entities that project Core entities


def projects_bounded_context() -> Callable[[type], type]:
    """Declare that the decorated class projects a BoundedContext.

    Use when an HCD viewpoint entity provides a view onto a Core
    bounded context. For example, Accelerator projects BoundedContext.
    """
    return semantic_relation(BoundedContext, RelationType.PROJECTS)


def projects_application() -> Callable[[type], type]:
    """Declare that the decorated class projects an Application.

    Use when an HCD viewpoint entity provides a view onto a Core
    application. For example, App projects Application.
    """
    return semantic_relation(Application, RelationType.PROJECTS)


# Compositional decorators - for within-BC entity relationships


def part_of_app() -> Callable[[type], type]:
    """Declare that the decorated class is part of an App.

    Use for entities that are contained within an App and appear
    on the App's documentation page rather than having their own page.
    Example: Story is part_of App.
    """
    return semantic_relation(App, RelationType.PART_OF)


def contains_story() -> Callable[[type], type]:
    """Declare that the decorated class contains Stories.

    Use for entities that aggregate stories.
    Example: Epic contains Story, Journey contains Story.
    """
    return semantic_relation(Story, RelationType.CONTAINS)


def contains_epic() -> Callable[[type], type]:
    """Declare that the decorated class contains Epics.

    Use for entities that aggregate epics.
    Example: Journey contains Epic.
    """
    return semantic_relation(Epic, RelationType.CONTAINS)


def references_persona() -> Callable[[type], type]:
    """Declare that the decorated class references a Persona.

    Use for entities that reference a persona without containing it.
    Example: Story references Persona, Journey references Persona.
    """
    return semantic_relation(Persona, RelationType.REFERENCES)

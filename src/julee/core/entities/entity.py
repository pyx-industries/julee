"""Entity model for Clean Architecture domain objects."""

from julee.core.entities.code_info import ClassInfo


class Entity(ClassInfo):
    """Domain concepts that define the ontology of a bounded context.

    Entities are what business logic is expressed in terms of. A use case
    doesn't manipulate strings and dictionaries - it operates on Journeys,
    Personas, PollingConfigs. The entities ARE the domain language. They
    give meaning to the bounded context and constrain what can be said
    within it. Repositories store them; services transform them; use cases
    orchestrate both.

    Entities exist independent of any Application. Whether the system is
    accessed via API, CLI, or workflow trigger, the entities remain the
    same. They are the most stable part of your architecture because they
    represent the business itself, not the technology serving it.

    This is the Dependency Rule in action: entities know nothing about use
    cases, controllers, databases, or frameworks. When the UI framework
    changes, entities don't change. When you switch databases, entities
    don't change. They embody the business, not the technology.

    Each bounded context defines its own ontology. Because entities are
    architecturally bound to implementation (not just documented separately),
    we can reason over them programmatically. This binding enables viewpoint
    projection: HCD personas, C4 containers, and other perspectives can be
    inferred across bounded contexts because they share a common ontological
    foundation in code.

    Entities are more than dumb data containers. They are rich objects in
    their own right, with derivative methods that validate and calculate
    properties. They have both data and behavior - they encapsulate some
    of the business rules.

    In julee, entities are immutable value objects (Pydantic models with
    frozen=True). Immutability prevents accidental state corruption and
    makes the system easier to reason about. If you need to "change" an
    entity, you create a new one.
    """

    pass  # Inherits all fields from ClassInfo

"""Entity model for Clean Architecture domain objects."""

from julee.core.entities.code_info import ClassInfo


class Entity(ClassInfo):
    """The ontological root of the julee framework.

    Entity is equivalent to ``owl:Thing`` in the Web Ontology Language (OWL) -
    the top-level concept from which all other framework concepts derive. The
    framework's domain model includes core concepts that are all specializations
    of Entity:

    - **BoundedContext**: A linguistic boundary containing a coherent domain model
    - **UseCase**: An application-specific business operation
    - **Request**: Input contract for a use case
    - **Response**: Output contract from a use case
    - **Pipeline**: A composable transformation chain
    - **Application**: A deployment boundary exposing use cases

    Entity is not a language primitive - it is the ontological primitive of the
    framework, which happens to be expressed in software. The binding to source
    code occurs through :class:`~julee.core.entities.code_info.ClassInfo`, which
    provides introspection capabilities (module path, docstring, source location).
    This architectural binding enables programmatic reasoning over the ontology:
    we can traverse relationships, validate conformance, and project viewpoints
    because the concepts exist in code, not just documentation.

    **What Entities Represent**

    Entities are domain concepts that define the ontology of a bounded context.
    They are what business logic is expressed in terms of. A use case doesn't
    manipulate strings and dictionaries - it operates on Journeys, Personas,
    PollingConfigs. The entities ARE the domain language. They give meaning to
    the bounded context and constrain what can be said within it. Repositories
    store them; services transform them; use cases orchestrate both.

    **Architectural Stability**

    Entities exist independent of any Application. Whether the system is accessed
    via API, CLI, or workflow trigger, the entities remain the same. They are the
    most stable part of your architecture because they represent the business
    itself, not the technology serving it.

    This is the Dependency Rule in action: entities know nothing about use cases,
    controllers, databases, or frameworks. When the UI framework changes, entities
    don't change. When you switch databases, entities don't change. They embody
    the business, not the technology.

    **Ontological Foundation**

    Each bounded context defines its own ontology. Because entities are
    architecturally bound to implementation (not just documented separately),
    we can reason over them programmatically. This binding enables viewpoint
    projection: HCD personas, C4 containers, and other perspectives can be
    inferred across bounded contexts because they share a common ontological
    foundation in code.

    **Rich Domain Objects**

    Entities are more than dumb data containers. They are rich objects in their
    own right, with derivative methods that validate and calculate properties.
    They have both data and behavior - they encapsulate some of the business rules.

    In julee, entities are immutable value objects (Pydantic models with
    frozen=True). Immutability prevents accidental state corruption and makes
    the system easier to reason about. If you need to "change" an entity, you
    create a new one.
    """

    pass  # Inherits all fields from ClassInfo

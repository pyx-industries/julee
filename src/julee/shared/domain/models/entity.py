"""Entity model for Clean Architecture domain objects."""

from julee.shared.domain.models.code_info import ClassInfo


class Entity(ClassInfo):
    """The heart of the system - pure business logic with no dependencies.

    Entities encapsulate enterprise-wide business rules. They are the most
    stable part of your architecture because they represent concepts that
    exist independent of any application. A Customer, an Order, a Journey -
    these exist whether you have a web app, a CLI, or no software at all.

    This is the Dependency Rule in action: entities know nothing about use
    cases, controllers, databases, or frameworks. They are pure. When the
    UI framework changes, entities don't change. When you switch databases,
    entities don't change. They embody the business, not the technology.

    In julee, entities are immutable value objects (Pydantic models with
    frozen=True). Immutability prevents accidental state corruption and
    makes the system easier to reason about. If you need to "change" an
    entity, you create a new one.
    """

    pass  # Inherits all fields from ClassInfo

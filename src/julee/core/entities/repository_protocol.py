"""RepositoryProtocol model for Clean Architecture persistence abstractions."""

from julee.core.entities.code_info import ClassInfo


class RepositoryProtocol(ClassInfo):
    """An abstraction that hides persistence details from the domain.

    Repositories store things. Not to be confused with services, which do things.

    The repository pattern is Dependency Inversion made concrete. Your use
    case needs to save a Journey - but it must not know whether that Journey
    goes to PostgreSQL, MongoDB, or a flat file. The repository protocol
    defines WHAT can be done (save, find, delete) without revealing HOW.

    This is crucial: the use case imports the protocol (an interface), not
    the implementation. The database adapter implements the protocol. At
    runtime, dependency injection provides the concrete implementation. The
    use case remains blissfully ignorant of persistence technology.

    When you switch from PostgreSQL to DynamoDB, you write a new repository
    implementation. The use cases don't change. The domain doesn't change.
    Only the infrastructure changes. This is the power of proper boundaries.

    Interface Typing Doctrine
    -------------------------
    Repository protocols only deal in entities and simple primitives. No
    framework types, no infrastructure concerns - just domain language.
    The repository is bound to the semantics of a single entity type.

    Repository protocols live in the domain layer ({bc}/repositories/).
    Implementations live in infrastructure ({bc}/infrastructure/repositories/).
    The domain defines the interface; infrastructure provides the reality.
    """

    pass  # Inherits all fields from ClassInfo
